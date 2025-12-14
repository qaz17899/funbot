"""Enhanced Modal with error handling and validation."""

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
    """Enhanced Modal with built-in error handling and validation.

    Features:
    - Automatic error handling with ErrorEmbed
    - Customizable timeout
    - Auto-validation of TextInput children with is_digit=True
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

    def validate_inputs(self) -> None:
        """Validate all TextInput children.

        Raises:
            ValueError: If any TextInput with is_digit=True has invalid input.
        """
        from funbot.ui.components.text_input import TextInput

        for item in self.children:
            if isinstance(item, TextInput):
                is_valid, error_msg = item.validate()
                if not is_valid:
                    raise ValueError(error_msg)

    async def on_submit(self, interaction: Interaction) -> None:
        """Default submit handler - validate, defer and stop.

        Override this in subclasses to add custom logic.
        Call validate_inputs() manually if you override.
        """
        self.validate_inputs()
        with contextlib.suppress(discord.NotFound):
            await interaction.response.defer()
        self.stop()
