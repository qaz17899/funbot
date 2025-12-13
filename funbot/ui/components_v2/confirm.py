"""V2 Confirmation view with Yes/No buttons."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import ui

from .action_row import ActionRow
from .container import Container
from .layout_view import LayoutView
from .text_display import TextDisplay

if TYPE_CHECKING:
    from funbot.types import Interaction, User

__all__ = ("ConfirmView",)


class ConfirmView(LayoutView):
    """A V2 confirmation view with Yes/No buttons.

    Displays an optional message in a Container with Confirm/Cancel buttons.

    Attributes:
        result: True if confirmed, False if cancelled, None if timed out.

    Example:
        view = ConfirmView(
            author=interaction.user,
            message="Are you sure you want to delete this?",
        )
        await interaction.response.send_message(view=view)
        await view.wait()

        if view.result:
            # User confirmed
            ...
        elif view.result is False:
            # User cancelled
            ...
        else:
            # Timed out
            ...
    """

    def __init__(
        self,
        *,
        author: User | None = None,
        timeout: float = 60.0,
        message: str | None = None,
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
        confirm_style: discord.ButtonStyle = discord.ButtonStyle.success,
        cancel_style: discord.ButtonStyle = discord.ButtonStyle.secondary,
        accent_color: discord.Color | int | None = None,
    ) -> None:
        """Initialize the confirmation view.

        Args:
            author: The user who can interact with this view.
            timeout: Timeout in seconds.
            message: Optional message to display in the container.
            confirm_label: Label for the confirm button.
            cancel_label: Label for the cancel button.
            confirm_style: Style for the confirm button.
            cancel_style: Style for the cancel button.
            accent_color: Color for the container border.
        """
        super().__init__(author=author, timeout=timeout)
        self.result: bool | None = None

        # Add message container if provided
        if message:
            container = Container(
                TextDisplay(message), accent_color=accent_color or discord.Color.orange()
            )
            self.add_item(container)

        # Add buttons
        self.button_row = ConfirmButtonRow(
            confirm_label=confirm_label,
            cancel_label=cancel_label,
            confirm_style=confirm_style,
            cancel_style=cancel_style,
        )
        self.add_item(self.button_row)


class ConfirmButtonRow(ActionRow["ConfirmView"]):
    """Button row for confirmation view."""

    def __init__(
        self,
        *,
        confirm_label: str,
        cancel_label: str,
        confirm_style: discord.ButtonStyle,
        cancel_style: discord.ButtonStyle,
    ) -> None:
        super().__init__()
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label
        self.confirm_style = confirm_style
        self.cancel_style = cancel_style

        # Add buttons manually with custom labels/styles
        self.add_item(
            ui.Button(label=confirm_label, style=confirm_style, emoji="✅", custom_id="confirm:yes")
        )
        self.add_item(
            ui.Button(label=cancel_label, style=cancel_style, emoji="❌", custom_id="confirm:no")
        )

    async def interaction_check(self, interaction: Interaction) -> bool:
        """Handle button interactions."""
        # self.view is set when the ActionRow is added to a LayoutView
        assert self.view is not None

        if interaction.data and interaction.data.get("custom_id") == "confirm:yes":
            self.view.result = True
            self.view.stop()
            await interaction.response.defer()
        elif interaction.data and interaction.data.get("custom_id") == "confirm:no":
            self.view.result = False
            self.view.stop()
            await interaction.response.defer()
        return True
