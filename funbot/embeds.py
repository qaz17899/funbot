"""Embed utilities for standardized Discord embeds."""

from __future__ import annotations

import discord

from funbot.constants import EMBED_COLOR

__all__ = ("DefaultEmbed", "ErrorEmbed")


class DefaultEmbed(discord.Embed):
    """Standard embed with default color."""

    def __init__(
        self,
        *,
        title: str | None = None,
        description: str | None = None,
        color: discord.Color | int | None = None,
        **kwargs,
    ) -> None:
        super().__init__(title=title, description=description, color=color or EMBED_COLOR, **kwargs)


class ErrorEmbed(discord.Embed):
    """Error embed with red color and error styling."""

    def __init__(
        self, *, title: str = "An error occurred", description: str | None = None, **kwargs
    ) -> None:
        super().__init__(
            title=f"❌ {title}", description=description, color=discord.Color.red(), **kwargs
        )

    def set_footer_hint(self, text: str) -> ErrorEmbed:
        """Add a hint footer to the error embed."""
        self.set_footer(text=f"💡 {text}")
        return self
