from fastapi import APIRouter, HTTPException
from backend.database import TICKERS
from backend.services.ml_service import get_model_metrics, get_feature_importance, predict

router = APIRouter(prefix="/api/model", tags=["model"])


@router.get("/metrics")
def model_metrics():
    return get_model_metrics()


@router.get("/feature_importance")
def feature_importance():
    return get_feature_importance()


@router.get("/predict/{ticker}")
def predict_ticker(ticker: str):
    if ticker not in TICKERS:
        raise HTTPException(404, f"Ticker {ticker} not found")
    result = predict(ticker)
    if result is None:
        raise HTTPException(503, "Model not ready or no feature data available")
    return result
