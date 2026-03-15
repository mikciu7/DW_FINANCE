from fastapi import APIRouter, HTTPException
from backend.database import TICKERS
from backend.services.feature_service import get_features

router = APIRouter(prefix="/api/financials/features", tags=["features"])


@router.get("")
def all_features():
    return get_features()


@router.get("/{ticker}")
def ticker_features(ticker: str):
    if ticker not in TICKERS:
        raise HTTPException(404, f"Ticker {ticker} not found")
    return get_features(ticker)
