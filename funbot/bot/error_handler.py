"""Global error handler for application commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from loguru import logger

from funbot.embeds import ErrorEmbed
from funbot.exceptions import FunBotError

if TYPE_CHECKING:
    from funbot.types import Interaction

__all__ = ("get_error_embed", "on_tree_error")


def get_error_embed(error: Exception) -> tuple[ErrorEmbed, bool]:
    """Create a standardized error embed.

    Args:
        error: The exception that occurred.

    Returns:
        A tuple of (ErrorEmbed, recognized). If recognized is False,
        the error should be logged/reported.
    """
    recognized = True

    # Handle known error types
    if isinstance(error, FunBotError):
        embed = ErrorEmbed(title="Error", description=error.message)
    elif isinstance(error, discord.HTTPException):
        if error.code == 50013:
            embed = ErrorEmbed(
                title="Missing Permissions",
                description="I don't have the required permissions to perform this action.",
            )
        else:
            recognized = False
            embed = ErrorEmbed(title="Discord Error", description=f"[{error.code}] {error.text}")
    elif isinstance(error, app_commands.CommandOnCooldown):
        embed = ErrorEmbed(
            title="Cooldown",
            description=f"Please wait {error.retry_after:.1f} seconds before using this command.",
        )
    elif isinstance(error, app_commands.MissingPermissions):
        perms = ", ".join(error.missing_permissions)
        embed = ErrorEmbed(
            title="Missing Permissions", description=f"You need the following permissions: {perms}"
        )
    else:
        recognized = False
        embed = ErrorEmbed(title="Unexpected Error", description=f"{type(error).__name__}: {error}")

    if not recognized:
        embed.set_footer_hint("This error has been logged for investigation.")

    return embed, recognized


async def on_tree_error(interaction: Interaction, error: app_commands.AppCommandError) -> None:
    """Handle errors from application commands.

    Args:
        interaction: The interaction that raised the error.
        error: The error that was raised.
    """
    # Unwrap the original error if wrapped
    original_error = getattr(error, "original", error)

    # Get error embed
    embed, recognized = get_error_embed(original_error)

    # Log unrecognized errors
    if not recognized:
        logger.error(
            f"Unhandled error in command '{interaction.command}': {original_error}",
            exc_info=original_error,
        )
    else:
        logger.warning(f"Handled error in command '{interaction.command}': {original_error}")

    # Send error response
    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.HTTPException:
        logger.warning("Failed to send error message to user")
