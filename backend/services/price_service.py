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
                conn.commit()  # ZMIANA: Wymagane zapisanie zmian w Postgresie!

        except Exception as e:
            print(f"[price_service] Error fetching {ticker}: {e}")


def get_prices(ticker: str | None = None) -> list[dict]:
    with get_connection() as conn:
        # ZMIANA: Używamy RealDictCursor, żeby wyniki zwracały się jako słowniki (jak sqlite3.Row)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if ticker:
                # ZMIANA: %s zamiast ?
                cur.execute(
                    "SELECT ticker, date, open, high, low, close, volume FROM prices WHERE ticker=%s ORDER BY date",
                    (ticker,)
                )
            else:
                cur.execute(
                    "SELECT ticker, date, open, high, low, close, volume FROM prices ORDER BY ticker, date"
                )
            rows = cur.fetchall()
            
    # Zamieniamy daty z obiektów datetime.date na stringi dla spójności
    result = []
    for r in rows:
        row_dict = dict(r)
        if row_dict['date']:
            row_dict['date'] = str(row_dict['date'])
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