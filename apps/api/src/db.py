"""asyncpg connection pool and FastAPI dependency."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg
from fastapi import FastAPI

from .config import settings

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def create_pool() -> asyncpg.Pool:
    """Create the application-wide asyncpg connection pool."""
    global _pool
    import ssl as _ssl
    dsn = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    # Strip sslmode query param - asyncpg uses ssl= kwarg instead
    if "sslmode" in dsn:
        dsn = dsn.split("?")[0]
    ssl_ctx = _ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = _ssl.CERT_NONE
    _pool = await asyncpg.create_pool(dsn=dsn, ssl=ssl_ctx, min_size=2, max_size=10)
    logger.info("Database pool created")
    return _pool


async def close_pool() -> None:
    """Gracefully close the connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        logger.info("Database pool closed")
        _pool = None


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[misc]
    """Manage DB pool lifecycle alongside the FastAPI app."""
    await create_pool()
    yield
    await close_pool()


async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """Yield an asyncpg connection from the pool for use as a FastAPI dependency."""
    if _pool is None:
        raise RuntimeError("Database pool is not initialised")
    async with _pool.acquire() as conn:
        yield conn
