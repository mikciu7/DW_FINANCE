"""
Wrapper around StatementsFetcher that upserts raw CATS financial data into PostgreSQL.
For initial load, data comes from the pre-scraped CSV files in /data/.
For incremental updates, StatementsFetcher fetches new 10-Q/10-K filings from EDGAR.
"""
import sys
import os
import pandas as pd
from psycopg2.extras import RealDictCursor
from backend.database import get_connection, CATS, TICKERS
from backend.services.llm_parser_service import parse_pre2010

# Make sure the project root (MED/) is on the path so StatementsFetcher can be imported
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CSV_RENAMES = {
    "property_plant_and_equipment_net": "property_plant_and_equipment",
}


def load_csv_financials(data_dir: str):
    """Load raw financial data from pre-scraped CSV files into the financials table."""
    for ticker in TICKERS:
        csv_path = os.path.join(data_dir, f"{ticker}_2010_2025.csv")
        if not os.path.exists(csv_path):
            print(f"[edgar_service] CSV not found: {csv_path}")
            continue
        try:
            df = pd.read_csv(csv_path)
            # Rename _net variant only if the plain column doesn't already exist
            if "property_plant_and_equipment_net" in df.columns and "property_plant_and_equipment" not in df.columns:
                df = df.rename(columns=CSV_RENAMES)
            # Drop duplicate column names (keep first)
            df = df.loc[:, ~df.columns.duplicated()]
            df["ticker"] = ticker
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            # LLM parser dla danych pre-2010
            mask = pd.to_datetime(df["date"]) < "2010-01-01"
            if mask.any():
                df.loc[mask] = parse_pre2010(df.loc[mask])

            # Keep only CATS columns that exist in this CSV
            available = [c for c in CATS if c in df.columns]
            missing = [c for c in CATS if c not in df.columns]
            if missing:
                print(f"[edgar_service] {ticker}: missing CATS cols: {missing}")

            rows_df = df[["ticker", "date"] + available].copy()
            
            # Wypełniamy None, żeby psycopg2 zamienił to na NULL w bazie
            for col in CATS:
                if col not in rows_df.columns:
                    rows_df[col] = None

            # Zastępujemy NaN z Pandas na None dla psycopg2 (inaczej wyskoczy błąd "can't adapt type 'numpy.float64'")
            rows_df = rows_df.where(pd.notnull(rows_df), None)

            cols = ["ticker", "date"] + CATS
            col_names = ", ".join(cols)
            # ZMIANA: W Postgresie używamy %s
            placeholders = ", ".join(["%s"] * len(cols))
            
            # ZMIANA: Składnia Upsert dla Postgresa
            updates = ", ".join([f"{c} = EXCLUDED.{c}" for c in CATS])
            query = f"""
                INSERT INTO financials ({col_names}) 
                VALUES ({placeholders})
                ON CONFLICT (ticker, date) DO UPDATE SET 
                {updates}
            """

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.executemany(query, rows_df[cols].values.tolist())
                conn.commit() # ZMIANA: Commit!

            print(f"[edgar_service] Loaded {len(rows_df)} rows for {ticker}")
        except Exception as e:
            print(f"[edgar_service] Error loading {ticker}: {e}")


def fetch_new_filings(ticker: str, since_date: str) -> bool:
    """
    Use StatementsFetcher to pull any new 10-Q/10-K filed since since_date.
    Returns True if new data was inserted.
    """
    try:
        from StatementsFetcher import StatementsFetcher
        fetcher = StatementsFetcher()
        from datetime import date
        today = date.today().strftime("%Y-%m-%d")
        
        df = fetcher.filings_for_period(ticker, since_date, today)
        if df is None or df.empty:
            return False

        df = df.rename(columns=CSV_RENAMES)
        df["ticker"] = ticker
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

        for col in CATS:
            if col not in df.columns:
                df[col] = None
                
        # Zastępujemy NaN z Pandas na None dla psycopg2
        df = df.where(pd.notnull(df), None)

        cols = ["ticker", "date"] + CATS
        col_names = ", ".join(cols)
        # ZMIANA: W Postgresie używamy %s
        placeholders = ", ".join(["%s"] * len(cols))
        
        # ZMIANA: Składnia Upsert
        updates = ", ".join([f"{c} = EXCLUDED.{c}" for c in CATS])
        query = f"""
            INSERT INTO financials ({col_names}) 
            VALUES ({placeholders})
            ON CONFLICT (ticker, date) DO UPDATE SET 
            {updates}
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(query, df[cols].values.tolist())
            conn.commit()
            
        return True

    except Exception as e:
        print(f"[edgar_service] fetch_new_filings error for {ticker}: {e}")
        return False


def get_financials(
    ticker: str | None = None,
    columns: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    safe_cols = [c for c in (columns or []) if c in CATS]
    select_cols = ["ticker", "date"] + (safe_cols if safe_cols else CATS)
    col_str = ", ".join(select_cols)

    conditions = []
    params: list = []
    if ticker:
        conditions.append("ticker=%s")
        params.append(ticker)
    if start_date:
        conditions.append("date >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("date <= %s")
        params.append(end_date)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"SELECT {col_str} FROM financials {where} ORDER BY ticker, date"

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    result = []
    for r in rows:
        row_dict = dict(r)
        if row_dict.get("date"):
            row_dict["date"] = str(row_dict["date"])
        result.append(row_dict)
    return result


def get_latest_financial_date(ticker: str) -> str | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(date) FROM financials WHERE ticker=%s", (ticker,))
            row = cur.fetchone()
            
    if row and row[0]:
        return str(row[0])
    return None