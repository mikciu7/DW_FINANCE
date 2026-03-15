import yfinance as yf
import pandas as pd
from backend.database import get_connection, TICKERS


def fetch_and_store_prices(tickers: list[str] = TICKERS, full_history: bool = False):
    """
    Download price history from yfinance and upsert into prices table.
    - full_history=True  → fetch from 2010-01-01 (used by init_db)
    - full_history=False → fetch only from last known date in DB (daily scheduler)
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

            with get_connection() as conn:
                conn.executemany(
                    "INSERT OR REPLACE INTO prices (ticker, date, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    rows,
                )
        except Exception as e:
            print(f"[price_service] Error fetching {ticker}: {e}")


def get_prices(ticker: str | None = None) -> list[dict]:
    with get_connection() as conn:
        if ticker:
            rows = conn.execute(
                "SELECT ticker, date, open, high, low, close, volume FROM prices WHERE ticker=? ORDER BY date",
                (ticker,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT ticker, date, open, high, low, close, volume FROM prices ORDER BY ticker, date"
            ).fetchall()
    return [dict(r) for r in rows]


def get_latest_price_date(ticker: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT MAX(date) as d FROM prices WHERE ticker=?", (ticker,)
        ).fetchone()
    return row["d"] if row else None
