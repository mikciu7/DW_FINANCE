from fastapi import APIRouter, Query
from backend.services.agent_service import get_geopolitics, get_stocks

router = APIRouter(prefix="/api/agent", tags=["agent"])

@router.get("/geopolitics")
async def geopolitics():
    return {"data": get_geopolitics()}

@router.get("/stocks")
async def stocks(tickers: list[str] = Query(default=[])):
    return {"data": get_stocks(tickers)}