"""Database context manager for Tortoise ORM lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from tortoise import Tortoise

from funbot.db.config import TORTOISE_CONFIG

if TYPE_CHECKING:
    from types import TracebackType

__all__ = ("Database",)


class Database:
    """Async context manager for Tortoise ORM.

    Usage:
        async with Database():
            # Database is now connected and ready
            ...
        # Database connections are closed automatically
    """

    async def __aenter__(self) -> None:
        """Initialize Tortoise ORM and connect to the database."""
        await Tortoise.init(config=TORTOISE_CONFIG)
        logger.info("Connected to database")

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close all database connections."""
        await Tortoise.close_connections()
        logger.info("Disconnected from database")
