"""FunBot entry point."""

from __future__ import annotations

import asyncio
import contextlib

import asyncpg
from loguru import logger

from funbot.bot import FunBot
from funbot.config import CONFIG
from funbot.db import Database
from funbot.utils import setup_async_event_loop, setup_logging


async def main() -> None:
    """Main entry point for the bot."""
    setup_logging("logs/funbot.log")
    setup_async_event_loop()

    logger.info("Starting FunBot...")

    # Redis client (optional)
    redis = None
    if CONFIG.redis_url:
        try:
            from redis.asyncio import Redis

            redis = Redis.from_url(CONFIG.redis_url)
            logger.info("Redis connection initialized")
        except ImportError:
            logger.warning("redis package not installed, skipping Redis initialization")

    with contextlib.suppress(KeyboardInterrupt, asyncio.CancelledError):
        async with (
            asyncpg.create_pool(CONFIG.db_url) as pool,
            Database(),
            FunBot(pool=pool, redis=redis, config=CONFIG) as bot,
        ):
            await bot.start(CONFIG.discord_token)

    # Cleanup Redis
    if redis is not None:
        await redis.close()
        logger.info("Redis connection closed")


if __name__ == "__main__":
    asyncio.run(main())
