"""Global error handler for application commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from loguru import logger

if TYPE_CHECKING:
    from funbot.types import Interaction

__all__ = ("get_error_embed", "on_tree_error")


def get_error_embed(error: Exception, *, title: str = "An error occurred") -> discord.Embed:
    """Create a standardized error embed.

    Args:
        error: The exception that occurred.
        title: The title for the embed.

    Returns:
        A Discord embed describing the error.
    """
    return discord.Embed(title=f"❌ {title}", description=str(error), color=discord.Color.red())


async def on_tree_error(interaction: Interaction, error: app_commands.AppCommandError) -> None:
    """Handle errors from application commands.

    Args:
        interaction: The interaction that raised the error.
        error: The error that was raised.
    """
    # Unwrap the original error if wrapped
    original_error = getattr(error, "original", error)

    # Log the error
    logger.error(
        f"Error in command '{interaction.command}': {original_error}", exc_info=original_error
    )

    # Create error embed
    embed = get_error_embed(original_error)

    # Send error response
    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.HTTPException:
        # If we can't send the error message, just log it
        logger.warning("Failed to send error message to user")
