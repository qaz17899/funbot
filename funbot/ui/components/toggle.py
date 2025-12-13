"""Toggle button that switches between on/off states."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from .button import Button

if TYPE_CHECKING:
    from funbot.types import Interaction

    from .view import View

__all__ = ("ToggleButton",)


class ToggleButton[V_co: View](Button):
    """A button that toggles between on/off states.

    Attributes:
        current_toggle: Current toggle state (True = on).
    """

    def __init__(
        self,
        *,
        current_toggle: bool = False,
        on_label: str = "On",
        off_label: str = "Off",
        on_emoji: str = "✅",
        off_emoji: str = "❌",
        row: int | None = None,
        custom_id: str | None = None,
    ) -> None:
        self.current_toggle = current_toggle
        self.on_label = on_label
        self.off_label = off_label
        self.on_emoji = on_emoji
        self.off_emoji = off_emoji

        super().__init__(
            style=self._get_style(),
            label=self._get_label(),
            emoji=self._get_emoji(),
            row=row,
            custom_id=custom_id,
        )

        self.view: V_co

    def _get_style(self) -> discord.ButtonStyle:
        return discord.ButtonStyle.success if self.current_toggle else discord.ButtonStyle.secondary

    def _get_label(self) -> str:
        return self.on_label if self.current_toggle else self.off_label

    def _get_emoji(self) -> str:
        return self.on_emoji if self.current_toggle else self.off_emoji

    def update_style(self) -> None:
        """Update the button's appearance based on current state."""
        self.style = self._get_style()
        self.label = self._get_label()
        self.emoji = self._get_emoji()

    async def callback(self, interaction: Interaction) -> None:
        """Toggle the state and update appearance."""
        self.current_toggle = not self.current_toggle
        self.update_style()
        await interaction.response.edit_message(view=self.view)
