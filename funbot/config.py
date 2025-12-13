"""Application configuration using Pydantic settings."""

from __future__ import annotations

from typing import Literal

from dotenv import load_dotenv
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict

type EnvType = Literal["dev", "test", "prod"]


class Config(BaseSettings):
    """Bot configuration loaded from environment variables."""

    # Discord
    discord_token: str
    discord_client_id: int | None = None

    # Database
    db_url: str

    # Redis
    redis_url: str | None = None

    # Environment
    env: EnvType = "dev"

    # Logging
    log_level: str = "DEBUG"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def is_dev(self) -> bool:
        """Check if running in development environment."""
        return self.env == "dev"

    @property
    def is_prod(self) -> bool:
        """Check if running in production environment."""
        return self.env == "prod"


load_dotenv()
CONFIG = Config()  # pyright: ignore[reportCallIssue]
logger.info(f"Environment: {CONFIG.env}")
