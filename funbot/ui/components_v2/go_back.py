"""GoBackButton for returning to previous view state."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
from discord import ui

if TYPE_CHECKING:
    import io
    from collections.abc import Sequence

    from funbot.types import Interaction

    from .layout_view import LayoutView

__all__ = ("GoBackButton",)


class GoBackButton[V_co: LayoutView](ui.Button[V_co]):
    """Button that restores previous view state.

    Stores original children and embeds, then restores them when clicked.
    Useful for multi-step UI flows where you want to go back.

    Example:
        class DetailView(LayoutView):
            def __init__(self, original_children, embeds):
                super().__init__()
                # ... add detail content ...
                self.add_item(GoBackButton(original_children, embeds))
    """

    def __init__(
        self,
        original_children: list[ui.Item[Any]],
        embeds: Sequence[discord.Embed] | None = None,
        byte_obj: io.BytesIO | None = None,
        *,
        row: int = 4,
        emoji: str = "⬅️",
        label: str | None = None,
    ) -> None:
        """Initialize the go back button.

        Args:
            original_children: List of items to restore.
            embeds: Optional embeds to restore.
            byte_obj: Optional BytesIO for image attachments.
            row: Button row (default: 4 - bottom).
            emoji: Button emoji (default: ⬅️).
            label: Optional button label.
        """
        super().__init__(emoji=emoji, label=label, row=row)
        self.original_children = original_children.copy()
        self.embeds = embeds
        self.byte_obj = byte_obj

        self.view: V_co

    async def callback(self, interaction: Interaction) -> Any:
        """Restore original children and edit the message."""
        self.view.clear_items()
        for item in self.original_children:
            self.view.add_item(item)

        kwargs: dict[str, Any] = {"view": self.view}

        if self.embeds is not None:
            kwargs["embeds"] = list(self.embeds)

        if self.byte_obj is not None:
            self.byte_obj.seek(0)

            # Find image filename from embed
            original_image = None
            for embed in self.embeds or []:
                if embed.image.url is not None:
                    # Remove query parameters from URL and get filename
                    url = embed.image.url.split("?")[0]
                    original_image = url.split("/")[-1]
                    embed.set_image(url=f"attachment://{original_image}")
                    break

            original_image = original_image or "image.png"
            kwargs["attachments"] = [discord.File(self.byte_obj, filename=original_image)]

        await interaction.response.edit_message(**kwargs)
