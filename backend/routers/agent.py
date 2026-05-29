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
    async def generate():
        import asyncio
        loop = asyncio.get_event_loop()
        gen = chat_with_agent(req)
        _DONE = object()

        def _next():
            try:
                return next(gen)
            except StopIteration:
                return _DONE

        while True:
            token = await loop.run_in_executor(None, _next)
            if token is _DONE:
                break
            yield f"data: {token}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})