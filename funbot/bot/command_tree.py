"""Custom CommandTree for the bot."""

from __future__ import annotations

from discord import app_commands
from loguru import logger

__all__ = ("CommandTree",)


class CommandTree(app_commands.CommandTree["FunBot"]):
    """Custom command tree with enhanced functionality.

    Features:
    - Logging for command sync events
    - Custom error handling integration
    """

    async def sync(self, *, guild: object = None) -> list[app_commands.AppCommand]:
        """Sync commands with Discord and log the result."""
        commands = await super().sync(guild=guild)

        if guild is None:
            logger.info(f"Synced {len(commands)} global commands")
        else:
            logger.info(f"Synced {len(commands)} commands to guild {guild}")

        return commands
