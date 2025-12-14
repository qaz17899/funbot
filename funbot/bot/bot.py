"""FunBot main class - the heart of the bot."""

from __future__ import annotations

from typing import TYPE_CHECKING

import anyio
import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from funbot.bot.command_tree import CommandTree
from funbot.bot.error_handler import on_tree_error

if TYPE_CHECKING:
    from types import TracebackType

    import asyncpg
    from redis.asyncio import Redis

    from funbot.config import Config

__all__ = ("FunBot",)


class FunBot(commands.AutoShardedBot):
    """FunBot - A Discord entertainment bot with perfect architecture.

    This class serves as the central hub that holds all shared resources:
    - Database connection pool
    - Redis cache client
    - Configuration
    """

    def __init__(self, *, pool: asyncpg.Pool, redis: Redis | None, config: Config) -> None:
        """Initialize the bot with injected dependencies.

        Args:
            pool: The asyncpg connection pool for database operations.
            redis: The Redis client for caching (optional).
            config: The application configuration.
        """
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            case_insensitive=True,
            allowed_mentions=discord.AllowedMentions(
                users=True, everyone=False, roles=False, replied_user=False
            ),
            help_command=None,
            chunk_guilds_at_startup=False,
            max_messages=None,
            tree_cls=CommandTree,
            allowed_contexts=app_commands.AppCommandContext(
                guild=True, dm_channel=True, private_channel=True
            ),
            allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
        )

        # Injected dependencies
        self.pool = pool
        self.redis = redis
        self.config = config

        # Internal state
        self.user_ids: set[int] = set()

    async def setup_hook(self) -> None:
        """Called when the bot is starting up.

        This is where we:
        - Load all cogs
        - Set up the command tree error handler
        - Sync commands (once at startup, not on reconnects)
        """
        self.tree.on_error = on_tree_error

        # Load all cogs dynamically
        await self._load_cogs()

        # Sync commands based on environment (only runs once at startup)
        guild_to_sync = None
        if self.config.is_dev:
            if self.config.dev_guild_id:
                guild_to_sync = discord.Object(id=self.config.dev_guild_id)
            else:
                logger.warning("DEV_GUILD_ID not set, syncing commands globally in dev mode")

        # Debug: show registered commands before sync
        all_commands = self.tree.get_commands()
        logger.debug(f"Registered commands before sync: {[c.name for c in all_commands]}")

        # If syncing to a specific guild, copy global commands to that guild first
        if guild_to_sync is not None:
            self.tree.copy_global_to(guild=guild_to_sync)

        # The custom CommandTree.sync method will log the outcome
        await self.tree.sync(guild=guild_to_sync)

        logger.info("Bot setup complete")

    async def _load_cogs(self) -> None:
        """Dynamically load all cogs from the cogs directory.

        Auto-discovers all .py files:
        - funbot/cogs/*.py -> loads as funbot.cogs.{name}
        - funbot/cogs/{subdir}/*.py -> loads as funbot.cogs.{subdir}.{name}

        No manual __init__.py registration required!
        """
        cogs_path = anyio.Path("funbot/cogs")

        # Load individual cog files (*.py) in the root cogs directory
        async for filepath in cogs_path.glob("*.py"):
            cog_name = filepath.stem

            # Skip __init__.py and private modules
            if cog_name.startswith("_"):
                continue

            try:
                await self.load_extension(f"funbot.cogs.{cog_name}")
                logger.info(f"Loaded cog: {cog_name!r}")
            except Exception as e:
                logger.exception(f"Failed to load cog {cog_name!r}: {e}")

        # Auto-discover and load all .py files in subdirectories
        async for dirpath in cogs_path.iterdir():
            if not await dirpath.is_dir():
                continue

            dir_name = dirpath.name
            if dir_name.startswith("_"):
                continue

            # Load each .py file in the subdirectory as a separate cog
            async for filepath in dirpath.glob("*.py"):
                cog_name = filepath.stem

                # Skip __init__.py and private modules
                if cog_name.startswith("_"):
                    continue

                extension_name = f"funbot.cogs.{dir_name}.{cog_name}"
                try:
                    await self.load_extension(extension_name)
                    logger.info(f"Loaded cog: {dir_name}/{cog_name}")
                except Exception as e:
                    logger.exception(f"Failed to load cog {dir_name}/{cog_name}: {e}")

    async def on_ready(self) -> None:
        """Called when the bot is ready and connected to Discord."""
        if self.user is None:
            return

        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        logger.info(f"Shard count: {self.shard_count or 1}")

    async def close(self) -> None:
        """Clean up resources when shutting down."""
        logger.info("Bot shutting down...")
        await super().close()

    # Context manager support for clean lifecycle management
    async def __aenter__(self) -> FunBot:
        """Enter the async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the async context manager and clean up."""
        await self.close()
