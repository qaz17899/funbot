"""Container component - embed-like box with accent color."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import ui

if TYPE_CHECKING:
    from typing import Self

__all__ = ("Container",)


class Container(ui.Container):
    """Enhanced Container with convenience methods.

    A Container is similar to an Embed - it has a darkened background
    and optional accent color (like embed border). Unlike embeds,
    it can contain other components like buttons, sections, or galleries.

    Example:
        container = Container(
            TextDisplay("# Header"),
            Separator(),
            TextDisplay("Content here"),
            accent_color=discord.Color.blurple()
        )
    """

    def __init__(
        self,
        *children: ui.Item,
        accent_color: discord.Color | int | None = None,
        spoiler: bool = False,
        id: int | None = None,  # noqa: A002
    ) -> None:
        """Initialize the container.

        Args:
            *children: Items to add to the container.
            accent_color: Color for the container border (like embed color).
            spoiler: Whether the container contents are hidden behind a spoiler.
            id: Optional numerical component ID.
        """
        super().__init__(accent_colour=accent_color, spoiler=spoiler, id=id)
        for child in children:
            self.add_item(child)

    def add_items(self, *items: ui.Item) -> Self:
        """Add multiple items to the container."""
        for item in items:
            self.add_item(item)
        return self
