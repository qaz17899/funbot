"""Toggle buttons for V2 LayoutView."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
from discord import ui

if TYPE_CHECKING:
    from funbot.types import Interaction

    from .layout_view import LayoutView

__all__ = ("ToggleButton", "ToggleUIButton")

# Toggle emoji mapping
TOGGLE_EMOJIS = {True: "✅", False: "❌"}

HIDE_UI_EMOJI = "🔽"
SHOW_UI_EMOJI = "🔼"


class ToggleButton[V_co: LayoutView](ui.Button[V_co]):
    """On/Off toggle button with auto-updating style.

    Automatically updates style, emoji, and label based on toggle state.

    Example:
        class SettingsRow(ActionRow):
            def __init__(self, notifications_enabled: bool):
                super().__init__()
                self.add_item(ToggleButton(
                    current_toggle=notifications_enabled,
                    toggle_label="Notifications",
                ))

        # In callback:
        async def callback(self, interaction):
            await toggle_button.toggle(interaction)
            # toggle_button.current_toggle now has the new value
    """

    def __init__(
        self,
        current_toggle: bool,
        toggle_label: str,
        *,
        row: int | None = 1,
        custom_id: str | None = None,
    ) -> None:
        """Initialize the toggle button.

        Args:
            current_toggle: Initial toggle state.
            toggle_label: Label text (will be shown as "Label: On/Off").
            row: Button row (default: 1).
            custom_id: Optional custom ID.
        """
        self.current_toggle = current_toggle
        self.toggle_label = toggle_label

        super().__init__(
            style=self._get_style(),
            label=self._get_label(),
            emoji=TOGGLE_EMOJIS[current_toggle],
            row=row,
            custom_id=custom_id,
        )

        self.view: V_co

    def _get_style(self) -> discord.ButtonStyle:
        """Get button style based on toggle state."""
        return discord.ButtonStyle.green if self.current_toggle else discord.ButtonStyle.gray

    def _get_label(self) -> str:
        """Get label with toggle status."""
        status = "On" if self.current_toggle else "Off"
        return f"{self.toggle_label}: {status}"

    def update_style(self) -> None:
        """Update button appearance based on current toggle state."""
        self.style = self._get_style()
        self.label = self._get_label()
        self.emoji = TOGGLE_EMOJIS[self.current_toggle]

    async def callback(self, interaction: Interaction) -> Any:
        """Toggle the state and update the view."""
        self.current_toggle = not self.current_toggle
        self.update_style()
        await interaction.response.edit_message(view=self.view)

    async def toggle(self, interaction: Interaction, *, edit: bool = True) -> None:
        """Toggle the state programmatically.

        Args:
            interaction: The interaction to respond with.
            edit: Whether to edit the message (default: True).
        """
        self.current_toggle = not self.current_toggle
        self.update_style()
        if edit:
            await interaction.response.edit_message(view=self.view)


class ToggleUIButton[V_co: LayoutView](ui.Button[V_co]):
    """Button that hides/shows all other UI items.

    When clicked, toggles between showing all items and showing only this button.
    Useful for cleaning up the UI while preserving state.

    Example:
        class MyLayout(LayoutView):
            def __init__(self):
                super().__init__()
                # ... add components ...
                self.add_item(ToggleUIButton())
    """

    def __init__(self, *, row: int = 4) -> None:
        """Initialize the toggle UI button.

        Args:
            row: Button row (default: 4 - bottom).
        """
        super().__init__(
            style=discord.ButtonStyle.gray, label="Hide UI", emoji=HIDE_UI_EMOJI, row=row
        )
        self._items: list[ui.Item[Any]] = []
        self._mode: str = "hide"

        self.view: V_co

    def _set_style(self) -> None:
        """Update button style based on current mode."""
        if self._mode == "hide":
            self.emoji = HIDE_UI_EMOJI
            self.style = discord.ButtonStyle.gray
            self.label = "Hide UI"
        else:
            self.emoji = SHOW_UI_EMOJI
            self.style = discord.ButtonStyle.blurple
            self.label = "Show UI"

    async def callback(self, interaction: Interaction) -> None:
        """Toggle UI visibility."""
        if self._mode == "hide":
            # Save current items and hide them
            children = list(self.view.children)
            children.remove(self)
            self._items = children  # type: ignore[assignment]
            self.view.clear_items()

            self._mode = "show"
            self._set_style()
            self.view.add_item(self)
        else:
            # Restore items
            self.view.clear_items()
            for item in self._items:
                self.view.add_item(item)

            self._mode = "hide"
            self._set_style()
            self.view.add_item(self)

        await interaction.response.edit_message(view=self.view)
