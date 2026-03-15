"""
Feature engineering pipeline.
Reads raw CATS data from financials + close prices from prices,
computes 30 model features, and stores them in the features table.
"""
import numpy as np
import pandas as pd
from backend.database import get_connection, FEATURE_COLS, TICKERS


def _rolling_zscore(s: pd.Series, window: int) -> pd.Series:
    mu = s.rolling(window, min_periods=2).mean()
    sigma = s.rolling(window, min_periods=2).std()
    return (s - mu) / sigma.replace(0, np.nan)


def _polyfit_slope(s: pd.Series, window: int) -> pd.Series:
    def _slope(arr):
        if arr.isna().any() or len(arr) < 2:
            return np.nan
        x = np.arange(len(arr))
        return np.polyfit(x, arr, 1)[0]
    return s.rolling(window, min_periods=2).apply(_slope, raw=False)


def _get_quarterly_prices(ticker: str, dates: pd.Series) -> pd.Series:
    """Return close prices matched to quarterly report dates."""

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT date, close FROM prices WHERE ticker=? ORDER BY date", (ticker,)
        ).fetchall()

    if not rows:
        return pd.Series(np.nan, index=dates.index)

    price_df = pd.DataFrame(rows, columns=["date", "close"])
    price_df["date"] = pd.to_datetime(price_df["date"])
    price_df = price_df.set_index("date").sort_index()

    # For each quarterly report date, use the closest available price (forward fill)
    report_dates = pd.to_datetime(dates.values)
    prices = []
    for d in report_dates:
        mask = price_df.index <= d
        if mask.any():
            prices.append(price_df.loc[mask, "close"].iloc[-1])
        else:
            prices.append(np.nan)
    return pd.Series(prices, index=dates.index)


def compute_features(ticker: str) -> pd.DataFrame | None:
    """Compute 30 model features for a single ticker from DB data."""

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM financials WHERE ticker=? ORDER BY date", (ticker,)
        ).fetchall()
    if not rows:
        return None

    df = pd.DataFrame([dict(r) for r in rows])
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # ── Close price ──────────────────────────────────────────────────────────
    df["close_price"] = _get_quarterly_prices(ticker, df["date"])

    # ── Basic ratios ─────────────────────────────────────────────────────────
    df["profit_margin"] = df["net_income"] / df["revenue"]
    df["roa"] = df["net_income"] / df["total_assets"]
    df["roe"] = df["net_income"] / df["total_stockholders_equity"]
    df["operating_cf_margin"] = df["net_cash_from_operating_activities"] / df["revenue"]
    df["debt_to_assets"] = df["total_liabilities"] / df["total_assets"]
    df["cf_to_debt"] = df["net_cash_from_operating_activities"] / df["total_liabilities"]

    # ── Growth rates ─────────────────────────────────────────────────────────
    df["revenue_growth_qoq"] = df["revenue"].pct_change(1, fill_method=None)
    df["earnings_growth_qoq"] = df["net_income"].pct_change(1, fill_method=None)
    df["eps_growth_qoq"] = df["earnings_per_share_basic_"].pct_change(1, fill_method=None)
    df["eps_growth_yoy"] = df["earnings_per_share_basic_"].pct_change(4, fill_method=None)

    # ── Acceleration (second derivative) ────────────────────────────────────
    df["revenue_acceleration"] = df["revenue_growth_qoq"].diff()
    df["earnings_acceleration"] = df["earnings_growth_qoq"].diff()
    df["eps_acceleration"] = df["eps_growth_qoq"].diff()

    # ── Trend (polyfit slope over 4 quarters) ───────────────────────────────
    df["revenue_trend"] = _polyfit_slope(df["revenue"], 4)
    df["earnings_trend"] = _polyfit_slope(df["net_income"], 4)

    # ── Volatility ───────────────────────────────────────────────────────────
    df["earnings_volatility"] = (
        df["net_income"].rolling(4, min_periods=2).std()
        / df["net_income"].rolling(4, min_periods=2).mean().replace(0, np.nan)
    )

    # ── EPS surprise ─────────────────────────────────────────────────────────
    eps_ma4 = df["earnings_per_share_basic_"].rolling(4, min_periods=2).mean()
    df["eps_surprise"] = (df["earnings_per_share_basic_"] - eps_ma4) / eps_ma4.replace(0, np.nan)

    # ── Quality score (composite) ────────────────────────────────────────────
    df["quality_score"] = (
        df["roe"] * 0.4
        + df["profit_margin"] * 0.3
        + df["operating_cf_margin"] * 0.3
    )
    df["quality_score_lag2"] = df["quality_score"].shift(2)
    df["quality_score_lag4"] = df["quality_score"].shift(4)

    # ── Profit margin lags ───────────────────────────────────────────────────
    df["profit_margin_lag2"] = df["profit_margin"].shift(2)
    df["profit_margin_lag4"] = df["profit_margin"].shift(4)

    # ── Price features ───────────────────────────────────────────────────────
    df["price_ma_4q"] = df["close_price"].rolling(4, min_periods=2).mean()
    df["price_momentum_6m"] = df["close_price"].pct_change(2, fill_method=None)

    # ── Z-scores (rolling standardization) ──────────────────────────────────
    df["accounts_payable_std_8"] = _rolling_zscore(df["accounts_payable"], 8)
    df["net_change_in_cash_std_16"] = _rolling_zscore(df["net_change_in_cash"], 16)
    df["cash_and_cash_equivalents_std_8"] = _rolling_zscore(df["cash_and_cash_equivalents"], 8)
    df["income_tax_expense_std_16"] = _rolling_zscore(df["income_tax_expense"], 16)
    df["nonoperating_income_expense_std_16"] = _rolling_zscore(df["nonoperating_income_expense"], 16)
    df["total_liabilities_std_8"] = _rolling_zscore(df["total_liabilities"], 8)
    df["accounts_receivable_std_16"] = _rolling_zscore(df["accounts_receivable"], 16)
    df["retained_earnings_std_16"] = _rolling_zscore(df["retained_earnings"], 16)
    df["net_cash_from_financing_activities_std_8"] = _rolling_zscore(df["net_cash_from_financing_activities"], 8)
    df["total_assets_std_16"] = _rolling_zscore(df["total_assets"], 16)
    df["total_current_liabilities_std_8"] = _rolling_zscore(df["total_current_liabilities"], 8)
    df["cost_of_goods_and_services_sold_std_16"] = _rolling_zscore(df["cost_of_goods_and_services_sold"], 16)
    df["earnings_per_share_basic__std_8"] = _rolling_zscore(df["earnings_per_share_basic_"], 8)

    # ── Store date as string ─────────────────────────────────────────────────
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    return df


def store_features(ticker: str, df: pd.DataFrame):
    cols = ["ticker", "date", "close_price"] + FEATURE_COLS
    df["ticker"] = ticker

    for c in cols:
        if c not in df.columns:
            df[c] = None

    placeholders = ", ".join(["?"] * len(cols))
    col_names = ", ".join(cols)

    rows = df[cols].where(df[cols].notna(), other=None).values.tolist()
    with get_connection() as conn:
        conn.executemany(
            f"INSERT OR REPLACE INTO features ({col_names}) VALUES ({placeholders})",
            rows,
        )


def run_feature_pipeline(tickers: list[str] = TICKERS):
    """Run full feature engineering for all tickers and store results."""
    for ticker in tickers:
        df = compute_features(ticker)
        if df is not None and not df.empty:
            store_features(ticker, df)
            print(f"[feature_service] Computed features for {ticker}: {len(df)} rows")
        else:
            print(f"[feature_service] No data for {ticker}")


def get_features(ticker: str | None = None) -> list[dict]:
    cols = ", ".join(["ticker", "date", "close_price"] + FEATURE_COLS)
    with get_connection() as conn:
        if ticker:
            rows = conn.execute(
                f"SELECT {cols} FROM features WHERE ticker=? ORDER BY date", (ticker,)
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT {cols} FROM features ORDER BY ticker, date"
            ).fetchall()
    return [dict(r) for r in rows]


def get_latest_features(ticker: str) -> dict | None:
    """Return the most recent feature row for a ticker (for live prediction)."""
    cols = ", ".join(["ticker", "date", "close_price"] + FEATURE_COLS)
    with get_connection() as conn:
        row = conn.execute(
            f"SELECT {cols} FROM features WHERE ticker=? ORDER BY date DESC LIMIT 1",
            (ticker,),
        ).fetchone()
    return dict(row) if row else None
