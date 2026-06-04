from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.database import init_db, TICKERS
from backend.scheduler import create_scheduler
from backend.services import ml_service
from backend.routers import financials, features, model, macro, agent
from backend.routers import auth as auth_router, admin as admin_router
from backend.middleware.auth_middleware import require_auth
from dotenv import load_dotenv

load_dotenv("backend/.env")

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ml_service.ensure_model_loaded()
    scheduler = create_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="NeoEye API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://neoeye.app"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(financials.router)
app.include_router(features.router)
app.include_router(model.router)
app.include_router(macro.router)
app.include_router(agent.router)


@app.get("/api/tickers")
def list_tickers():
    return TICKERS


@app.get("/health")
def health():
    return {"status": "ok"}