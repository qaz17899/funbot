"""Section component - combines text with an accessory."""

from __future__ import annotations

from typing import TYPE_CHECKING

from discord import ui

if TYPE_CHECKING:
    from .button import Button
    from .thumbnail import Thumbnail

__all__ = ("Section",)


class Section(ui.Section):
    """Enhanced Section for side-by-side text and accessory layouts.

    A Section combines up to 3 TextDisplays with an accessory (Thumbnail or Button)
    displayed on the right side. The accessory is required.

    Layout visualization:
        +--------------------Section--------------------+
        | +----------------------------+  +-Accessory-+ |
        | |  TextDisplay 1             |  | Thumbnail | |
        | |  TextDisplay 2             |  | or Button | |
        | |  TextDisplay 3             |  |           | |
        | +----------------------------+  +-----------+ |
        +-----------------------------------------------+

    Example with Thumbnail:
        section = Section(
            TextDisplay("## Title"),
            TextDisplay("Description here"),
            accessory=Thumbnail("https://example.com/image.png")
        )

    Example with Button:
        section = Section(
            TextDisplay("## Settings"),
            TextDisplay("-# Click to toggle"),
            accessory=ToggleButton()
        )
    """

    def __init__(
        self,
        *text_displays: ui.TextDisplay | str,
        accessory: Thumbnail | Button,
        id: int | None = None,  # noqa: A002
    ) -> None:
        """Initialize the section.

        Args:
            *text_displays: Up to 3 TextDisplay items or strings (auto-wrapped).
            accessory: A Thumbnail or Button to display on the right (required).
            id: Optional numerical component ID.
        """
        # Convert strings to TextDisplay
        items = []
        for td in text_displays[:3]:  # Max 3 text displays
            if isinstance(td, str):
                items.append(ui.TextDisplay(td))
            else:
                items.append(td)

        super().__init__(*items, accessory=accessory, id=id)
