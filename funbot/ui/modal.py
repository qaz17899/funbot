"""Enhanced Modal with error handling."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import discord
from discord.utils import MISSING
from loguru import logger

from funbot.embeds import ErrorEmbed

if TYPE_CHECKING:
    from funbot.types import Interaction

__all__ = ("Modal",)


class Modal(discord.ui.Modal):
    """Enhanced Modal with built-in error handling.

    Features:
    - Automatic error handling with ErrorEmbed
    - Customizable timeout
    """

    def __init__(self, *, title: str, custom_id: str = MISSING, timeout: float = 600.0) -> None:
        super().__init__(
            title=title,
            timeout=timeout,
            custom_id=self.__class__.__name__ if custom_id is MISSING else custom_id,
        )

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        """Handle errors during modal submission."""
        logger.error(f"Error in modal {self.__class__.__name__}: {error}", exc_info=error)

        embed = ErrorEmbed(title="Form Error", description=str(error))

        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)

    async def on_submit(self, interaction: Interaction) -> None:
        """Default submit handler - defer and stop.

        Override this in subclasses to add custom logic.
        """
        with contextlib.suppress(discord.NotFound):
            await interaction.response.defer()
        self.stop()
