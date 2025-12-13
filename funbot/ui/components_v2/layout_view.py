"""Enhanced LayoutView with author check, timeout handling, and error handling."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any, Self

import discord
from discord import ui
from loguru import logger

from funbot.embeds import ErrorEmbed

if TYPE_CHECKING:
    from collections.abc import Iterable

    from funbot.types import Interaction, User

__all__ = ("LayoutView",)


class LayoutView(ui.LayoutView):
    """Enhanced LayoutView with author checking and error handling.

    This is the V2 equivalent of funbot.ui.View. It provides:
    - Author-only interaction check
    - Automatic timeout cleanup
    - Built-in error handling with ErrorEmbed

    Note: When using LayoutView, you cannot send content, embeds,
    stickers, or polls. Use TextDisplay and Container instead.
    """

    def __init__(self, *, author: User | None = None, timeout: float = 600.0) -> None:
        """Initialize the layout view.

        Args:
            author: The user who can interact with this view. None allows anyone.
            timeout: Timeout in seconds (default: 10 minutes).
        """
        super().__init__(timeout=timeout)
        self.author = author
        self.message: discord.Message | None = None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"

    def add_items(self, items: Iterable[ui.Item[Any]]) -> Self:
        """Add multiple items to the view at once."""
        for item in items:
            self.add_item(item)
        return self

    async def on_timeout(self) -> None:
        """Handle view timeout by disabling interactive components."""
        if self.message is not None:
            with contextlib.suppress(discord.HTTPException):
                # In V2, we need to find and disable buttons/selects in ActionRows
                self._disable_interactive_items()
                await self.message.edit(view=self)
        else:
            logger.warning(f"LayoutView {self!r} timed out without a set message")

    def _disable_interactive_items(self) -> None:
        """Disable all interactive items (buttons and selects)."""
        for item in self.walk_children():
            if isinstance(item, ui.Button | ui.Select):
                # Skip URL buttons
                if isinstance(item, ui.Button) and item.url:
                    continue
                item.disabled = True

    async def on_error(
        self, interaction: Interaction, error: Exception, item: ui.Item[Any]
    ) -> None:
        """Handle errors from view interactions."""
        logger.error(f"Error in LayoutView {self!r} item {item}: {error}", exc_info=error)

        embed = ErrorEmbed(title="Interaction Error", description=str(error))
        await self.absolute_send(interaction, embed=embed, ephemeral=True)

    async def interaction_check(self, interaction: Interaction) -> bool:
        """Check if the user is authorized to interact with this view."""
        if self.author is None:
            return True

        if interaction.user.id != self.author.id:
            embed = ErrorEmbed(
                title="Not Authorized",
                description="Only the person who triggered this command can use these controls.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False

        return True

    @staticmethod
    async def absolute_send(interaction: Interaction, **kwargs) -> None:
        """Send a message, handling both initial response and followup."""
        with contextlib.suppress(discord.HTTPException):
            if not interaction.response.is_done():
                await interaction.response.send_message(**kwargs)
            else:
                await interaction.followup.send(**kwargs)

    @staticmethod
    async def absolute_edit(interaction: Interaction, **kwargs) -> None:
        """Edit the original message, handling both response and followup."""
        with contextlib.suppress(discord.HTTPException):
            if not interaction.response.is_done():
                await interaction.response.edit_message(**kwargs)
            else:
                await interaction.edit_original_response(**kwargs)
