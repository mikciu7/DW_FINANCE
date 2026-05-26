"""
Feature engineering pipeline.
Reads raw CATS data from financials + close prices from prices,
computes 30 model features, and stores them in the features table (PostgreSQL).
"""
import numpy as np
import pandas as pd
from psycopg2.extras import RealDictCursor
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
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # ZMIANA: %s zamiast ?
            cur.execute(
                "SELECT date, close FROM prices WHERE ticker=%s ORDER BY date", (ticker,)
            )
            rows = cur.fetchall()

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
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # ZMIANA: %s zamiast ?
            cur.execute(
                "SELECT * FROM financials WHERE ticker=%s ORDER BY date", (ticker,)
            )
            rows = cur.fetchall()
            
    if not rows:
        return None

    df = pd.DataFrame([dict(r) for r in rows])
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # ── Close price ──────────────────────────────────────────────────────────
    df["close_price"] = _get_quarterly_prices(ticker, df["date"])

    # ── Profitability ─────────────────────────────────────────────────────────
    rev = df["revenue"].replace(0, np.nan)
    df["profit_margin"]      = df["net_income"] / rev
    df["gross_margin"]       = df["gross_profit"] / rev
    df["operating_margin"]   = df["operating_income"] / rev
    df["roa"]                = df["net_income"] / df["total_assets"].replace(0, np.nan)
    df["roe"]                = df["net_income"] / df["total_stockholders_equity"].replace(0, np.nan)
    df["roic"]               = df["operating_income"] / (df["total_stockholders_equity"] + df["total_liabilities"]).replace(0, np.nan)
    df["operating_cf_margin"] = df["net_cash_from_operating_activities"] / rev

    # ── Leverage & Liquidity ──────────────────────────────────────────────────
    df["debt_to_assets"] = df["total_liabilities"] / df["total_assets"].replace(0, np.nan)
    df["cf_to_debt"]     = df["net_cash_from_operating_activities"] / df["total_liabilities"].replace(0, np.nan)
    df["current_ratio"]  = df["total_current_assets"] / df["total_current_liabilities"].replace(0, np.nan)
    df["asset_turnover"] = rev / df["total_assets"].replace(0, np.nan)

    # ── Cash Flow ─────────────────────────────────────────────────────────────
    fcf = df["net_cash_from_operating_activities"] + df["net_cash_from_investing_activities"]
    df["fcf_margin"] = fcf / rev

    # ── Growth rates ─────────────────────────────────────────────────────────
    df["revenue_growth_qoq"]  = df["revenue"].pct_change(1, fill_method=None)
    df["revenue_growth_yoy"]  = df["revenue"].pct_change(4, fill_method=None)
    df["earnings_growth_qoq"] = df["net_income"].pct_change(1, fill_method=None)
    df["earnings_growth_yoy"] = df["net_income"].pct_change(4, fill_method=None)
    df["eps_growth_qoq"]      = df["earnings_per_share_basic_"].pct_change(1, fill_method=None)
    df["eps_growth_yoy"]      = df["earnings_per_share_basic_"].pct_change(4, fill_method=None)

    # ── Acceleration ─────────────────────────────────────────────────────────
    df["revenue_acceleration"]  = df["revenue_growth_qoq"].diff()
    df["earnings_acceleration"] = df["earnings_growth_qoq"].diff()
    df["eps_acceleration"]      = df["eps_growth_qoq"].diff()

    # ── Price features ───────────────────────────────────────────────────────
    df["price_ma_4q"]       = df["close_price"].rolling(4, min_periods=2).mean()
    df["price_vs_ma4q"]     = (df["close_price"] - df["price_ma_4q"]) / df["price_ma_4q"].replace(0, np.nan)
    df["price_momentum_3m"] = df["close_price"].pct_change(1, fill_method=None)
    df["price_momentum_6m"] = df["close_price"].pct_change(2, fill_method=None)
    df["price_momentum_12m"] = df["close_price"].pct_change(4, fill_method=None)
    df["price_volatility_4q"] = df["close_price"].pct_change(fill_method=None).rolling(4, min_periods=2).std()
    df["pe_ratio"] = df["close_price"] / (df["earnings_per_share_basic_"] * 4).replace(0, np.nan)

    # ── Volatility ───────────────────────────────────────────────────────────
    df["earnings_volatility"] = (
        df["net_income"].rolling(4, min_periods=2).std()
        / df["net_income"].rolling(4, min_periods=2).mean().replace(0, np.nan)
    )
    df["revenue_volatility"] = (
        df["revenue"].rolling(4, min_periods=2).std()
        / df["revenue"].rolling(4, min_periods=2).mean().replace(0, np.nan)
    )

    # ── Surprises ────────────────────────────────────────────────────────────
    eps_ma4 = df["earnings_per_share_basic_"].rolling(4, min_periods=2).mean()
    df["eps_surprise"] = (df["earnings_per_share_basic_"] - eps_ma4) / eps_ma4.replace(0, np.nan)
    rev_ma4 = df["revenue"].rolling(4, min_periods=2).mean()
    df["revenue_surprise"] = (df["revenue"] - rev_ma4) / rev_ma4.replace(0, np.nan)
    ni_ma4 = df["net_income"].rolling(4, min_periods=2).mean()
    df["earnings_surprise"] = (df["net_income"] - ni_ma4) / ni_ma4.replace(0, np.nan)

    # ── Trend ────────────────────────────────────────────────────────────────
    df["revenue_trend"]  = _polyfit_slope(df["revenue"], 4)
    df["earnings_trend"] = _polyfit_slope(df["net_income"], 4)

    # ── Streaks ──────────────────────────────────────────────────────────────
    df["positive_earnings_streak"] = (df["earnings_growth_qoq"] > 0).rolling(4, min_periods=1).sum()
    df["positive_revenue_streak"]  = (df["revenue_growth_qoq"] > 0).rolling(4, min_periods=1).sum()

    # ── Changes ──────────────────────────────────────────────────────────────
    df["profit_margin_change"] = df["profit_margin"].diff()
    df["roe_change"]           = df["roe"].diff()

    # ── Composite scores ─────────────────────────────────────────────────────
    df["quality_score"] = (
        df["roe"].fillna(0) * 0.4
        + df["profit_margin"].fillna(0) * 0.3
        + df["operating_cf_margin"].fillna(0) * 0.3
    )
    df["growth_score"] = (
        df["revenue_growth_yoy"].fillna(0) * 0.4
        + df["earnings_growth_yoy"].fillna(0) * 0.4
        + df["positive_earnings_streak"].fillna(0) / 4 * 0.2
    )
    df["momentum_score"] = (
        df["price_momentum_12m"].fillna(0) * 0.5
        + df["eps_growth_yoy"].fillna(0) * 0.3
        + df["revenue_growth_yoy"].fillna(0) * 0.2
    )

    # ── Lags ─────────────────────────────────────────────────────────────────
    df["quality_score_lag1"]  = df["quality_score"].shift(1)
    df["quality_score_lag2"]  = df["quality_score"].shift(2)
    df["quality_score_lag4"]  = df["quality_score"].shift(4)
    df["profit_margin_lag1"]  = df["profit_margin"].shift(1)
    df["profit_margin_lag2"]  = df["profit_margin"].shift(2)
    df["profit_margin_lag4"]  = df["profit_margin"].shift(4)
    df["roe_lag1"]            = df["roe"].shift(1)
    df["roe_lag2"]            = df["roe"].shift(2)
    df["roe_lag4"]            = df["roe"].shift(4)

    # ── Z-scores ─────────────────────────────────────────────────────────────
    df["accounts_payable_std_8"]                   = _rolling_zscore(df["accounts_payable"], 8)
    df["net_change_in_cash_std_16"]                = _rolling_zscore(df["net_change_in_cash"], 16)
    df["cash_and_cash_equivalents_std_8"]          = _rolling_zscore(df["cash_and_cash_equivalents"], 8)
    df["income_tax_expense_std_16"]                = _rolling_zscore(df["income_tax_expense"], 16)
    df["nonoperating_income_expense_std_16"]       = _rolling_zscore(df["nonoperating_income_expense"], 16)
    df["total_liabilities_std_8"]                  = _rolling_zscore(df["total_liabilities"], 8)
    df["accounts_receivable_std_16"]               = _rolling_zscore(df["accounts_receivable"], 16)
    df["retained_earnings_std_16"]                 = _rolling_zscore(df["retained_earnings"], 16)
    df["net_cash_from_financing_activities_std_8"] = _rolling_zscore(df["net_cash_from_financing_activities"], 8)
    df["total_assets_std_16"]                      = _rolling_zscore(df["total_assets"], 16)
    df["total_current_liabilities_std_8"]          = _rolling_zscore(df["total_current_liabilities"], 8)
    df["cost_of_goods_and_services_sold_std_16"]   = _rolling_zscore(df["cost_of_goods_and_services_sold"], 16)
    df["earnings_per_share_basic__std_8"]          = _rolling_zscore(df["earnings_per_share_basic_"], 8)

    df = df.replace([np.inf, -np.inf], np.nan)

    # ── Store date as string ─────────────────────────────────────────────────
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    return df


def store_features(ticker: str, df: pd.DataFrame):
    cols = ["ticker", "date", "close_price"] + FEATURE_COLS
    df["ticker"] = ticker

    for c in cols:
        if c not in df.columns:
            df[c] = None

    # ZMIANA: Zastępujemy NaN z Pandas na None (NULL w bazie)
    df = df.where(pd.notnull(df), None)

    # ZMIANA: %s zamiast ?
    placeholders = ", ".join(["%s"] * len(cols))
    col_names = ", ".join(cols)
    
    # ZMIANA: Logika Upsert dla PostgreSQL
    updates = ", ".join([f"{c} = EXCLUDED.{c}" for c in ["close_price"] + FEATURE_COLS])
    query = f"""
        INSERT INTO features ({col_names}) 
        VALUES ({placeholders})
        ON CONFLICT (ticker, date) DO UPDATE SET 
        {updates}
    """

    rows = df[cols].values.tolist()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(query, rows)
        conn.commit() # ZMIANA: Commit do bazy


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
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if ticker:
                # ZMIANA: %s zamiast ?
                cur.execute(
                    f"SELECT {cols} FROM features WHERE ticker=%s ORDER BY date", (ticker,)
                )
            else:
                cur.execute(
                    f"SELECT {cols} FROM features ORDER BY ticker, date"
                )
            rows = cur.fetchall()
            
    # ZMIANA: Konwersja daty na string
    result = []
    for r in rows:
        row_dict = dict(r)
        if row_dict.get('date'):
            row_dict['date'] = str(row_dict['date'])
        result.append(row_dict)
        
    return result


def get_latest_features(ticker: str) -> dict | None:
    """Return the most recent feature row for a ticker (for live prediction)."""
    cols = ", ".join(["ticker", "date", "close_price"] + FEATURE_COLS)
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # ZMIANA: %s zamiast ?
            cur.execute(
                f"SELECT {cols} FROM features WHERE ticker=%s ORDER BY date DESC LIMIT 1",
                (ticker,)
            )
            row = cur.fetchone()
            
    if row:
        row_dict = dict(row)
        if row_dict.get('date'):
            row_dict['date'] = str(row_dict['date'])
        return row_dict
    return None
