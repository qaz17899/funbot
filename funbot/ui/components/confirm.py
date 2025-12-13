"""Confirmation view with Yes/No buttons."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from .button import Button
from .view import View

if TYPE_CHECKING:
    from funbot.types import Interaction, User

__all__ = ("ConfirmView",)


class ConfirmView(View):
    """A simple confirmation view with Yes/No buttons.

    Attributes:
        result: True if confirmed, False if cancelled, None if timed out.
    """

    def __init__(
        self,
        *,
        author: User | None = None,
        timeout: float = 60.0,
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
        confirm_style: discord.ButtonStyle = discord.ButtonStyle.success,
        cancel_style: discord.ButtonStyle = discord.ButtonStyle.secondary,
    ) -> None:
        super().__init__(author=author, timeout=timeout)
        self.result: bool | None = None

        self.add_item(ConfirmButton(label=confirm_label, style=confirm_style))
        self.add_item(CancelButton(label=cancel_label, style=cancel_style))

    async def on_timeout(self) -> None:
        """Handle timeout - result stays None."""
        await super().on_timeout()


class ConfirmButton(Button["ConfirmView"]):
    """Confirmation button."""

    def __init__(self, *, label: str, style: discord.ButtonStyle) -> None:
        super().__init__(label=label, style=style, emoji="✅", custom_id="confirm:yes")

    async def callback(self, interaction: Interaction) -> None:
        self.view.result = True
        self.view.stop()
        await interaction.response.defer()


class CancelButton(Button["ConfirmView"]):
    """Cancel button."""

    def __init__(self, *, label: str, style: discord.ButtonStyle) -> None:
        super().__init__(label=label, style=style, emoji="❌", custom_id="confirm:no")

    async def callback(self, interaction: Interaction) -> None:
        self.view.result = False
        self.view.stop()
        await interaction.response.defer()
