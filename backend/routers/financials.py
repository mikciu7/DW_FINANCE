from fastapi import APIRouter, HTTPException
from fastapi import Depends
from backend.middleware.auth_middleware import require_auth
from backend.database import TICKERS
from backend.services.price_service import get_prices
from backend.services.edgar_service import get_financials

router = APIRouter(prefix="/api/financials", tags=["financials"], dependencies=[Depends(require_auth)])


@router.get("/price")
def all_prices():
    return get_prices()


@router.get("/price/{ticker}")
def ticker_prices(ticker: str):
    if ticker not in TICKERS:
        raise HTTPException(404, f"Ticker {ticker} not found")
    return get_prices(ticker)


@router.get("/edgar")
def all_edgar():
    return get_financials()


@router.get("/edgar/{ticker}")
def ticker_edgar(ticker: str):
    if ticker not in TICKERS:
        raise HTTPException(404, f"Ticker {ticker} not found")
    return get_financials(ticker)
