"""Enhanced Button with loading state support."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord

if TYPE_CHECKING:
    from funbot.types import Interaction

    from .view import View

__all__ = ("Button", "GoBackButton")


class Button[V_co: View](discord.ui.Button):
    """Enhanced Button with loading state support.

    Type parameter V_co allows type-safe access to self.view.
    """

    def __init__(
        self,
        *,
        style: discord.ButtonStyle = discord.ButtonStyle.secondary,
        label: str | None = None,
        disabled: bool = False,
        custom_id: str | None = None,
        url: str | None = None,
        emoji: str | None = None,
        row: int | None = None,
    ) -> None:
        super().__init__(
            style=style,
            label=label,
            disabled=disabled,
            custom_id=custom_id,
            url=url,
            emoji=emoji,
            row=row,
        )

        # Store original state for loading state management
        self.original_label: str | None = None
        self.original_emoji: str | None = None
        self.original_disabled: bool | None = None

        self.view: V_co

    async def set_loading_state(self, interaction: Interaction) -> None:
        """Set the button to a loading state.

        Stores original state and disables all items in the view.
        """
        self.original_label = self.label[:] if self.label else None
        self.original_emoji = str(self.emoji) if self.emoji else None
        self.original_disabled = self.disabled

        self.view.disable_items()

        self.disabled = True
        self.emoji = "⏳"
        self.label = "Loading..."

        await self.view.absolute_edit(interaction, view=self.view)

    async def unset_loading_state(self, interaction: Interaction, **kwargs) -> None:
        """Restore the button from loading state.

        Restores original state and re-enables items.
        """
        if self.original_disabled is None:
            msg = "unset_loading_state called before set_loading_state"
            raise RuntimeError(msg)

        self.view.enable_items()

        self.disabled = self.original_disabled
        self.emoji = self.original_emoji
        self.label = self.original_label

        await self.view.absolute_edit(interaction, view=self.view, **kwargs)


class GoBackButton[V_co: View](Button):
    """A button that restores the view to a previous state."""

    def __init__(
        self,
        original_children: list[discord.ui.Item[Any]],
        *,
        embeds: list[discord.Embed] | None = None,
        row: int = 4,
    ) -> None:
        super().__init__(emoji="◀️", row=row)
        self.original_children = original_children.copy()
        self.embeds = embeds

        self.view: V_co

    async def callback(self, interaction: Interaction) -> Any:
        """Restore the view to its original state."""
        self.view.clear_items()
        for item in self.original_children:
            self.view.add_item(item)

        kwargs: dict[str, Any] = {"view": self.view}
        if self.embeds is not None:
            kwargs["embeds"] = self.embeds

        await interaction.response.edit_message(**kwargs)
