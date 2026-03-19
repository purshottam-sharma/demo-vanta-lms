"""Application configuration using pydantic-settings."""
from __future__ import annotations

import logging

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vanta_lms"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # JWT - default is intentionally insecure to catch misconfigured deployments
    SECRET_KEY: str = "dev-secret-change-in-production"

    # Google OAuth (optional - routes return 503 when absent)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Apple OAuth (optional - routes return 503 when absent)
    APPLE_CLIENT_ID: str = ""
    APPLE_CLIENT_SECRET: str = ""


def _build_settings() -> Settings:
    s = Settings()
    if s.SECRET_KEY == "dev-secret-change-in-production":
        logger.warning(
            "SECRET_KEY is using the insecure default value. "
            "Set SECRET_KEY in your .env file before deploying to production."
        )
    return s


settings = _build_settings()
