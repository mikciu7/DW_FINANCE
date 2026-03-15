"""
ML service: trains RandomForestRegressor on features, stores model as pkl,
and serves predictions.
"""
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error

from backend.database import get_connection, FEATURE_COLS, TICKERS

PKL_PATH = os.path.join(os.path.dirname(__file__), "..", "stock_prediction_model.pkl")

_model_cache: dict = {}  


def _load_pkl() -> bool:
    global _model_cache
    path = os.path.abspath(PKL_PATH)
    if os.path.exists(path):
        with open(path, "rb") as f:
            _model_cache = pickle.load(f)
        print(f"[ml_service] Model loaded from {path}")
        return True
    return False


def _compute_return_3m(ticker: str, report_dates: pd.Series) -> pd.Series:
    """
    For each report date, find the actual close price ~90 calendar days later
    from the daily prices table and compute the percentage return.
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT date, close FROM prices WHERE ticker=? ORDER BY date", (ticker,)
        ).fetchall()

    if not rows:
        return pd.Series(np.nan, index=report_dates.index)

    price_df = pd.DataFrame(rows, columns=["date", "close"])
    price_df["date"] = pd.to_datetime(price_df["date"])
    price_df = price_df.set_index("date").sort_index()

    returns = []
    for d in report_dates:
        target_date = d + pd.Timedelta(days=90)
        # price at report date (last available trading day on or before d)
        mask_d = price_df.index <= d
        # price 90 days later (first available trading day on or after target_date)
        mask_t = price_df.index >= target_date

        if mask_d.any() and mask_t.any():
            p0 = price_df.loc[mask_d, "close"].iloc[-1]
            p1 = price_df.loc[mask_t, "close"].iloc[0]
            returns.append((p1 - p0) / p0 if p0 != 0 else np.nan)
        else:
            returns.append(np.nan)

    return pd.Series(returns, index=report_dates.index)


def _get_training_data() -> tuple[pd.DataFrame, pd.Series] | tuple[None, None]:
    """
    Pull feature rows from the DB and compute return_3m as the actual
    price change 90 calendar days after each quarterly report date.
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT ticker, date, close_price, " + ", ".join(FEATURE_COLS) +
            " FROM features ORDER BY ticker, date"
        ).fetchall()

    if not rows:
        return None, None

    df = pd.DataFrame([dict(r) for r in rows])
    df["date"] = pd.to_datetime(df["date"])

    targets = []
    for ticker, grp in df.groupby("ticker"):
        grp = grp.sort_values("date").reset_index(drop=True)
        grp["return_3m"] = _compute_return_3m(ticker, grp["date"])
        targets.append(grp)

    df = pd.concat(targets).sort_values(["ticker", "date"]).reset_index(drop=True)

    df_clean = df.dropna(subset=["return_3m"] + FEATURE_COLS)
    if df_clean.empty:
        return None, None

    X = df_clean[FEATURE_COLS]
    y = df_clean["return_3m"]
    return X, y


def train_model():
    """Train RandomForest on all available feature data and save to pkl."""
    X, y = _get_training_data()
    if X is None or len(X) < 30:
        print("[ml_service] Not enough data to train model")
        return

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        min_samples_split=10,
        min_samples_leaf=4,
        max_features="sqrt",
        random_state=42,
        n_jobs=-1,
    )

    # Time-series CV for metrics
    tscv = TimeSeriesSplit(n_splits=5)
    r2_scores = cross_val_score(model, X, y, cv=tscv, scoring="r2")
    rmse_scores = -cross_val_score(model, X, y, cv=tscv, scoring="neg_root_mean_squared_error")
    mae_scores = -cross_val_score(model, X, y, cv=tscv, scoring="neg_mean_absolute_error")

    # Hit rate
    hit_rates = []
    for train_idx, test_idx in tscv.split(X):
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        y_pred = model.predict(X.iloc[test_idx])
        hit_rates.append(np.mean(np.sign(y_pred) == np.sign(y.iloc[test_idx])))

    # Final fit on full data
    model.fit(X, y)

    feature_importance = pd.DataFrame({
        "feature": FEATURE_COLS,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)

    metrics = {
        "r2": float(r2_scores.mean()),
        "r2_std": float(r2_scores.std()),
        "rmse": float(rmse_scores.mean()),
        "mae": float(mae_scores.mean()),
        "hit_rate": float(np.mean(hit_rates)),
    }

    model_data = {
        "model": model,
        "features": FEATURE_COLS,
        "metrics": metrics,
        "feature_importance": feature_importance,
        "n_features": len(FEATURE_COLS),
        "n_observations": len(y),
    }

    pkl_path = os.path.abspath(PKL_PATH)
    with open(pkl_path, "wb") as f:
        pickle.dump(model_data, f)

    # Persist metrics to DB
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO model_metrics (trained_at, r2, mae, rmse, hit_rate, n_features, n_observations) VALUES (datetime('now'), ?, ?, ?, ?, ?, ?)",
            (metrics["r2"], metrics["mae"], metrics["rmse"], metrics["hit_rate"],
             len(FEATURE_COLS), len(y)),
        )

    global _model_cache
    _model_cache = model_data
    print(f"[ml_service] Model trained - R2={metrics['r2']:.4f}, Hit Rate={metrics['hit_rate']:.2%}")


def ensure_model_loaded():
    """Load from pkl on startup; train if pkl doesn't exist."""
    if not _model_cache:
        if not _load_pkl():
            print("[ml_service] No pkl found — training model...")
            train_model()


def get_model_metrics() -> dict:
    if not _model_cache:
        return {}
    return _model_cache.get("metrics", {})


def get_feature_importance() -> list[dict]:
    if not _model_cache:
        return []
    fi = _model_cache.get("feature_importance")
    if fi is None:
        return []
    return fi.to_dict(orient="records")



def predict(ticker: str) -> dict | None:
    """
    Return a prediction dict for the given ticker using the latest features.
    """
    from backend.services.feature_service import get_latest_features

    if not _model_cache:
        return None

    row = get_latest_features(ticker)
    if row is None:
        return None

    features = _model_cache["features"]
    X = np.array([[row.get(f, np.nan) for f in features]])

    if np.isnan(X).all():
        return None

    model = _model_cache["model"]
    predicted = float(model.predict(X)[0])
    direction = "UP" if predicted > 0 else "DOWN"

    return {
        "ticker": ticker,
        "date": row.get("date"),
        "predicted_return_3m": round(predicted, 4),
        "direction": direction,
        "close_price": row.get("close_price"),
    }
