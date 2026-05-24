from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db, TICKERS
from backend.scheduler import create_scheduler
from backend.services import ml_service
from backend.routers import financials, features, model, agent
from dotenv import load_dotenv
load_dotenv("backend/.env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    init_db()

    ml_service.ensure_model_loaded()
    scheduler = create_scheduler()
    scheduler.start()

    yield

    scheduler.shutdown()


app = FastAPI(title="MED Stock Prediction API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(financials.router)
app.include_router(features.router)
app.include_router(model.router)
app.include_router(agent.router)

@app.get("/api/tickers")
def list_tickers():
    return TICKERS


@app.get("/health")
def health():
    return {"status": "ok"}
