import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

if settings.hf_token:
    os.environ["HF_TOKEN"] = settings.hf_token
import app.database as _db
from app.database import init_engine
from app.routers import auth, chat, curriculum, exercises, feedback, research, sessions
from app.services.exercise_db import exercise_db
from app.services.rag import rag_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_engine()
    await rag_engine.load_existing_index()
    await exercise_db.load()
    logger.info("Application started")
    yield
    if _db.engine is not None:
        await _db.engine.dispose()
    logger.info("Application shut down gracefully")


app = FastAPI(
    title="AI Socratic Teaching Assistant",
    description="LLM-powered programming tutor that provides scaffolded hints",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(chat.router, prefix="/api/v1/ws", tags=["chat"])
app.include_router(exercises.router, prefix="/api/v1/exercises", tags=["exercises"])
app.include_router(curriculum.router, prefix="/api/v1/curriculum", tags=["curriculum"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["feedback"])
app.include_router(research.router, prefix="/api/v1/research", tags=["research"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
