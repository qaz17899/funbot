"""URL button view for external links."""

from __future__ import annotations

import discord

__all__ = ("URLButtonView",)


class URLButtonView(discord.ui.View):
    """A simple view with one or more URL buttons.

    This view doesn't timeout since URL buttons don't require interaction handling.
    """

    def __init__(self) -> None:
        super().__init__(timeout=None)

    def add_url_button(
        self, *, label: str, url: str, emoji: str | None = None, row: int | None = None
    ) -> URLButtonView:
        """Add a URL button to the view.

        Args:
            label: The button label.
            url: The URL to open.
            emoji: Optional emoji.
            row: Optional row number.

        Returns:
            Self for chaining.
        """
        self.add_item(discord.ui.Button(label=label, url=url, emoji=emoji, row=row))
        return self

    @classmethod
    def single(cls, *, label: str, url: str, emoji: str | None = None) -> URLButtonView:
        """Create a view with a single URL button.

        Args:
            label: The button label.
            url: The URL to open.
            emoji: Optional emoji.

        Returns:
            A new URLButtonView with one button.
        """
        view = cls()
        view.add_url_button(label=label, url=url, emoji=emoji)
        return view
