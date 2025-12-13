"""Custom CommandTree for the bot."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Literal

import discord
from discord import InteractionType, app_commands
from loguru import logger

from funbot.db.models import User

if TYPE_CHECKING:
    from discord.abc import Snowflake

    from funbot.bot import FunBot  # noqa: F401
    from funbot.types import Interaction

__all__ = ("CommandTree",)


class CommandTree(app_commands.CommandTree["FunBot"]):
    """Custom command tree with enhanced functionality.

    Features:
    - Auto user creation on first interaction
    - Logging for command sync events
    - Custom error handling integration
    """

    async def interaction_check(self, i: Interaction) -> Literal[True]:
        """Check before every interaction - auto-create user if needed.

        This runs before every slash command and autocomplete.
        Creates the user in the database if they don't exist.
        """
        # Only check for commands and autocomplete
        if i.type not in {InteractionType.application_command, InteractionType.autocomplete}:
            return True

        # Skip if user already tracked in memory
        if i.user.id in i.client.user_ids:
            return True

        try:
            # Try to get or create user
            _, created = await User.get_or_create(id=i.user.id)
            i.client.user_ids.add(i.user.id)

            if created:
                logger.debug(f"Created new user record for {i.user.id}")
        except Exception as e:
            logger.error(f"Failed to create user {i.user.id}: {e}")

        return True

    async def on_error(self, i: Interaction, error: app_commands.AppCommandError) -> None:
        """Handle errors from application commands."""
        # Unwrap CommandInvokeError
        original = (
            error.original if isinstance(error, app_commands.errors.CommandInvokeError) else error
        )

        logger.error(f"Command error in {i.command}: {original}", exc_info=original)

        # Send error response to user
        from funbot.embeds import ErrorEmbed  # noqa: PLC0415

        embed = ErrorEmbed(title="Command Error", description=str(original))

        with contextlib.suppress(discord.NotFound, discord.HTTPException):
            if i.response.is_done():
                await i.followup.send(embed=embed, ephemeral=True)
            else:
                await i.response.send_message(embed=embed, ephemeral=True)

    async def sync(self, *, guild: Snowflake | None = None) -> list[app_commands.AppCommand]:
        """Sync commands with Discord and log the result."""
        commands = await super().sync(guild=guild)

        if guild is None:
            logger.info(f"Synced {len(commands)} global commands")
        else:
            logger.info(f"Synced {len(commands)} commands to guild {guild}")

        return commands
