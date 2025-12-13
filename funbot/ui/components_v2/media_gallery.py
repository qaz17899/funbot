"""MediaGallery component - displays images in a gallery grid."""

from __future__ import annotations

import discord
from discord import ui

__all__ = ("MediaGallery", "MediaGalleryItem")


# Re-export for convenience
MediaGalleryItem = discord.MediaGalleryItem


class MediaGallery(ui.MediaGallery):
    """Enhanced MediaGallery for displaying 1-10 images in a grid.

    Use this instead of embed images/thumbnails when you need multiple images
    or want them displayed in a grid layout.

    Example with URLs:
        gallery = MediaGallery(
            MediaGalleryItem("https://example.com/image1.png", description="Alt text"),
            MediaGalleryItem("https://example.com/image2.png", spoiler=True),
        )

    Example with local files:
        file1 = discord.File("image1.png")
        file2 = discord.File("image2.png")

        gallery = MediaGallery(
            MediaGalleryItem(file1),
            MediaGalleryItem(file2),
        )

        # Remember to pass files when sending!
        await channel.send(view=layout, files=[file1, file2])
    """

    def __init__(
        self,
        *items: discord.MediaGalleryItem,
        id: int | None = None,  # noqa: A002
    ) -> None:
        """Initialize the media gallery.

        Args:
            *items: MediaGalleryItem instances (1-10 items).
            id: Optional numerical component ID.
        """
        super().__init__(*items, id=id)
