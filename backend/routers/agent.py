from fastapi import APIRouter, Query
from backend.services.agent_service import get_geopolitics, get_stocks

router = APIRouter(prefix="/api/agent", tags=["agent"])

@router.get("/geopolitics")
async def geopolitics():
    data = await get_geopolitics()
    return {"data": data}

@router.get("/stocks")
async def stocks(tickers: list[str] = Query(default=[])):
    data = await get_stocks(tickers)
    return {"data": data}