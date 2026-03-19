"""Vanta LMS FastAPI application entry point."""
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import lifespan
from .auth.router import router as auth_router
from .users.router import router as users_router

app = FastAPI(
    title="Vanta LMS API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "version": "0.1.0"}


api_router = APIRouter(prefix="/api/v1")


@api_router.get("/")
async def api_v1_root() -> dict:
    return {"message": "Vanta LMS API v1"}


# Auth routes mounted at /api/v1/auth
api_router.include_router(auth_router)

# Users routes mounted at /api/v1/users
api_router.include_router(users_router)

app.include_router(api_router)
