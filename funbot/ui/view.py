"""Enhanced View with author check, timeout handling, and error handling."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any, Self

import discord
from loguru import logger

from funbot.embeds import ErrorEmbed

if TYPE_CHECKING:
    from collections.abc import Iterable

    from funbot.types import Interaction, User

    from .button import Button
    from .select import Select

__all__ = ("View",)


class View(discord.ui.View):
    """Enhanced View with author checking and error handling.

    Features:
    - Author-only interaction check
    - Automatic timeout cleanup
    - Built-in error handling with ErrorEmbed
    - Item state management for loading states
    """

    def __init__(self, *, author: User | None = None, timeout: float = 600.0) -> None:
        """Initialize the view.

        Args:
            author: The user who can interact with this view. None allows anyone.
            timeout: Timeout in seconds (default: 10 minutes).
        """
        super().__init__(timeout=timeout)
        self.author = author
        self.message: discord.Message | None = None
        self.item_states: dict[str, bool] = {}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"

    def add_items(self, items: Iterable[Button | Select]) -> Self:
        """Add multiple items to the view at once."""
        for item in items:
            self.add_item(item)
        return self

    async def on_timeout(self) -> None:
        """Handle view timeout by disabling all non-URL buttons."""
        # Check if all buttons are URL buttons (which don't need disabling)
        all_url_buttons = all(
            isinstance(item, discord.ui.Button) and item.url is not None
            for item in self.children
            if isinstance(item, discord.ui.Button)
        )

        if self.message is not None and not all_url_buttons:
            self.disable_items()
            with contextlib.suppress(discord.HTTPException):
                await self.message.edit(view=self)

        if self.message is None and not all_url_buttons:
            logger.warning(f"View {self!r} timed out without a set message")

    async def on_error(
        self, interaction: Interaction, error: Exception, item: discord.ui.Item[Any]
    ) -> None:
        """Handle errors from view interactions."""
        logger.error(f"Error in view {self!r} item {item}: {error}", exc_info=error)

        embed = ErrorEmbed(title="Interaction Error", description=str(error))

        # Try to unset loading state if applicable
        with contextlib.suppress(Exception):
            if hasattr(item, "unset_loading_state"):
                await item.unset_loading_state(interaction)  # type: ignore
            await self.absolute_edit(interaction, view=self)

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

    def disable_items(self) -> None:
        """Disable all interactive items (for loading state)."""
        for child in self.children:
            if isinstance(child, discord.ui.Button | discord.ui.Select):
                # Store original state
                if child.custom_id is not None:
                    self.item_states[child.custom_id] = child.disabled

                # Skip URL buttons
                if isinstance(child, discord.ui.Button) and child.url:
                    continue

                child.disabled = True

    def enable_items(self) -> None:
        """Re-enable items (restore from loading state)."""
        for child in self.children:
            if isinstance(child, discord.ui.Button | discord.ui.Select):
                # Skip URL buttons
                if isinstance(child, discord.ui.Button) and child.url:
                    continue

                # Restore original state
                if child.custom_id is not None:
                    child.disabled = self.item_states.get(child.custom_id, False)
                else:
                    child.disabled = False

    def get_item(self, custom_id: str) -> discord.ui.Item[Any] | None:
        """Get an item by its custom_id."""
        for item in self.children:
            if hasattr(item, "custom_id") and item.custom_id == custom_id:
                return item
        return None

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
