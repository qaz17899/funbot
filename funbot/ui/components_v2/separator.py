"""Separator component - visual spacing between components."""

from __future__ import annotations

import discord
from discord import ui

__all__ = ("Separator",)


class Separator(ui.Separator):
    """Enhanced Separator for visual spacing.

    Adds spacing between components with an optional visible divider line.

    Example:
        container = Container(
            TextDisplay("Above"),
            Separator(spacing=discord.SeparatorSpacing.large, divider=True),
            TextDisplay("Below"),
        )
    """

    def __init__(
        self,
        *,
        spacing: discord.SeparatorSpacing = discord.SeparatorSpacing.small,
        divider: bool = True,
        id: int | None = None,  # noqa: A002
    ) -> None:
        """Initialize the separator.

        Args:
            spacing: Amount of space (small or large).
            divider: Whether to show a visible line.
            id: Optional numerical component ID.
        """
        super().__init__(spacing=spacing, visible=divider, id=id)
