"""FastAPI entry point. Run from backend/: uvicorn app.main:app --reload"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.dependencies import get_blob_storage
from app.routes import health, uploads


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_blob_storage().ensure_ready()  # container exists + browser may PUT to it
    yield


app = FastAPI(title="Auto Data Analyst Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(uploads.router)
