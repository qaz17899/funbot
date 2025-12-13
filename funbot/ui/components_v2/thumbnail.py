"""Thumbnail component - image displayed in a Section."""

from __future__ import annotations

import discord
from discord import ui

__all__ = ("Thumbnail",)


class Thumbnail(ui.Thumbnail):
    """Enhanced Thumbnail for Section accessories.

    A Thumbnail displays an image on the right side of a Section.
    It replaces embed thumbnails in V2.

    Example:
        section = Section(
            TextDisplay("## Title"),
            TextDisplay("Description"),
            accessory=Thumbnail("https://example.com/thumb.png")
        )

    With local file:
        file = discord.File("thumb.png")
        section = Section(
            TextDisplay("Title"),
            accessory=Thumbnail(media=file)
        )
        # Remember: await channel.send(view=layout, files=[file])
    """

    def __init__(
        self,
        media: str | discord.File | None = None,
        *,
        url: str | None = None,
        description: str | None = None,
        spoiler: bool = False,
        id: int | None = None,  # noqa: A002
    ) -> None:
        """Initialize the thumbnail.

        Args:
            media: URL string or discord.File for the image.
            url: Alternative to media for URL strings.
            description: Alt text for the image.
            spoiler: Whether to hide behind a spoiler.
            id: Optional numerical component ID.
        """
        # Handle both positional media and url kwarg
        actual_media = media or url
        if actual_media is None:
            msg = "Thumbnail requires either media or url parameter"
            raise ValueError(msg)

        super().__init__(media=actual_media, description=description, spoiler=spoiler, id=id)
