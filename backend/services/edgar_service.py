"""
Wrapper around StatementsFetcher that upserts raw CATS financial data into SQLite.
For initial load, data comes from the pre-scraped CSV files in /data/.
For incremental updates, StatementsFetcher fetches new 10-Q/10-K filings from EDGAR.
"""
import sys
import os
import pandas as pd
from backend.database import get_connection, CATS, TICKERS

# Make sure the project root (MED/) is on the path so StatementsFetcher can be imported
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Column mapping from raw EDGAR CSV → CATS names (already snake_case in our CSVs)
# property_plant_and_equipment_net → property_plant_and_equipment

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

            # Keep only CATS columns that exist in this CSV
            available = [c for c in CATS if c in df.columns]
            missing = [c for c in CATS if c not in df.columns]
            if missing:
                print(f"[edgar_service] {ticker}: missing CATS cols: {missing}")

            rows_df = df[["ticker", "date"] + available].copy()
            # Fill missing CATS with None
            for col in CATS:
                if col not in rows_df.columns:
                    rows_df[col] = None

            cols = ["ticker", "date"] + CATS
            placeholders = ", ".join(["?"] * len(cols))
            col_names = ", ".join(cols)

            with get_connection() as conn:
                conn.executemany(
                    f"INSERT OR REPLACE INTO financials ({col_names}) VALUES ({placeholders})",
                    rows_df[cols].values.tolist(),
                )
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

        available = [c for c in CATS if c in df.columns]
        for col in CATS:
            if col not in df.columns:
                df[col] = None

        cols = ["ticker", "date"] + CATS
        placeholders = ", ".join(["?"] * len(cols))
        col_names = ", ".join(cols)

        with get_connection() as conn:
            conn.executemany(
                f"INSERT OR REPLACE INTO financials ({col_names}) VALUES ({placeholders})",
                df[cols].values.tolist(),
            )
        return True

    except Exception as e:
        print(f"[edgar_service] fetch_new_filings error for {ticker}: {e}")
        return False


def get_financials(ticker: str | None = None) -> list[dict]:

    cols = ", ".join(["ticker", "date"] + CATS)
    with get_connection() as conn:
        if ticker:
            rows = conn.execute(
                f"SELECT {cols} FROM financials WHERE ticker=? ORDER BY date", (ticker,)
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT {cols} FROM financials ORDER BY ticker, date"
            ).fetchall()
    return [dict(r) for r in rows]


def get_latest_financial_date(ticker: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT MAX(date) as d FROM financials WHERE ticker=?", (ticker,)
        ).fetchone()
    return row["d"] if row else None
