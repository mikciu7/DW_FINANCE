import yfinance as yf
import pandas as pd
from psycopg2.extras import RealDictCursor
from backend.database import get_connection, TICKERS

def fetch_and_store_prices(tickers: list[str] = TICKERS, full_history: bool = False):
    """
    Download price history from yfinance and upsert into prices table.
    """
    for ticker in tickers:
        try:
            if full_history:
                start = "2010-01-01"
            else:
                latest = get_latest_price_date(ticker)
                start = latest if latest else "2010-01-01"

            df = yf.download(ticker, start=start, progress=False, auto_adjust=True)
            if df.empty:
                continue
            df = df.reset_index()
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0].lower() for c in df.columns]
            else:
                df.columns = [c.lower() for c in df.columns]

            df["ticker"] = ticker
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            rows = df[["ticker", "date", "open", "high", "low", "close", "volume"]].values.tolist()

            # ZMIANA: Składnia PostgreSQL dla Upsert (zamiast INSERT OR REPLACE) i parametry %s
            query = """
                INSERT INTO prices (ticker, date, open, high, low, close, volume) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, date) DO UPDATE SET 
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume
            """

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.executemany(query, rows)
                    print("udalo sie wstawic ceny dla", ticker)
                conn.commit()  # ZMIANA: Wymagane zapisanie zmian w Postgresie!

        except Exception as e:
            print(f"[price_service] Error fetching {ticker}: {e}")


def get_prices(
    ticker: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
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
    query = f"SELECT ticker, date, open, high, low, close, volume FROM prices {where} ORDER BY ticker, date"

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    result = []
    for r in rows:
        row_dict = dict(r)
        if row_dict["date"]:
            row_dict["date"] = str(row_dict["date"])
        result.append(row_dict)
    return result


def get_latest_price_date(ticker: str) -> str | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # ZMIANA: %s zamiast ?
            cur.execute("SELECT MAX(date) FROM prices WHERE ticker=%s", (ticker,))
            row = cur.fetchone()
            
    # fetchone w zwykłym kursorze zwraca tuplę np. (datetime.date(2023, 10, 25),)
    if row and row[0]:
        return str(row[0]) # Zamienia obiekt daty na string 'YYYY-MM-DD'
    return None