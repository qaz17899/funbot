"""TextDisplay component - for displaying text content."""

from __future__ import annotations

from discord import ui

__all__ = ("TextDisplay",)


class TextDisplay(ui.TextDisplay):
    """Enhanced TextDisplay for displaying text content.

    TextDisplay replaces message content in V2. It supports full markdown
    including headers, bold, italic, code blocks, and more.

    Important notes:
    - Mentions (@user, @role, @everyone) WILL ping users
    - 4000 character limit shared across ALL TextDisplays in a LayoutView
    - Links will not auto-embed website previews

    Example:
        text = TextDisplay("# Hello World\\n**Bold** and *italic* work!")

        # With subheaders (Discord's -# syntax)
        text = TextDisplay("## Title\\n-# This is a subheader")
    """

    def __init__(self, content: str, *, id: int | None = None) -> None:  # noqa: A002
        """Initialize the text display.

        Args:
            content: The text content (supports markdown).
            id: Optional numerical component ID for finding this item later.
        """
        super().__init__(content, id=id)
