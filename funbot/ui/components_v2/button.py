"""Enhanced Button for V2 LayoutView with loading state support."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import ui

if TYPE_CHECKING:
    from funbot.types import Interaction

    from .layout_view import LayoutView

__all__ = ("Button",)


class Button[V_co: LayoutView](ui.Button[V_co]):
    """Enhanced Button with loading state support for V2.

    In V2, buttons MUST be placed in an ActionRow. Use the @row.button
    decorator or add Button instances to an ActionRow.

    Example with decorator:
        class MyLayout(LayoutView):
            row = ActionRow()

            @row.button(label="Click", style=discord.ButtonStyle.primary)
            async def click(self, interaction, button):
                await interaction.response.send_message("Clicked!")

    Example as instance:
        class MyButtonRow(ActionRow):
            def __init__(self, settings):
                super().__init__()
                self.add_item(ToggleButton(settings))
    """

    def __init__(
        self,
        *,
        style: discord.ButtonStyle = discord.ButtonStyle.secondary,
        label: str | None = None,
        disabled: bool = False,
        custom_id: str | None = None,
        url: str | None = None,
        emoji: str | discord.PartialEmoji | None = None,
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
        self.original_emoji: str | discord.PartialEmoji | None = None
        self.original_disabled: bool | None = None

        self.view: V_co

    async def set_loading_state(self, interaction: Interaction) -> None:
        """Set the button to a loading state.

        Stores original state and shows loading indicator.
        """
        assert self.view is not None, "Button must be attached to a view"

        self.original_label = self.label[:] if self.label else None
        self.original_emoji = self.emoji
        self.original_disabled = self.disabled

        self.disabled = True
        self.emoji = "⏳"
        self.label = "Loading..."

        await self.view.absolute_edit(interaction, view=self.view)

    async def unset_loading_state(self, interaction: Interaction, **kwargs) -> None:
        """Restore the button from loading state.

        Restores original state.
        """
        assert self.view is not None, "Button must be attached to a view"

        if self.original_disabled is None:
            msg = "unset_loading_state called before set_loading_state"
            raise RuntimeError(msg)

        self.disabled = self.original_disabled
        self.emoji = self.original_emoji
        self.label = self.original_label

        await self.view.absolute_edit(interaction, view=self.view, **kwargs)
