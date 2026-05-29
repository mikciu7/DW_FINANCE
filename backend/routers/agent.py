from fastapi import APIRouter, Query
from backend.services.agent_service import get_geopolitics, get_stocks
from fastapi.responses import StreamingResponse
from backend.services.new_agent_service import *
router = APIRouter(prefix="/api/agent", tags=["agent"])

@router.get("/geopolitics")
async def geopolitics():
    data = await get_geopolitics()
    return {"data": data}

@router.get("/stocks")
async def stocks(tickers: list[str] = Query(default=[])):
    data = await get_stocks(tickers)
    return {"data": data}

@router.post("/chat")
async def chat(req: ChatRequest):
    print("Received chat request:", req)
    def generate():
        for token in chat_with_agent(req):
            yield f"data: {token}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")