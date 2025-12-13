"""Components V2 UI module - Discord.py 2.6+ LayoutView-based components.

This module provides enhanced UI components using Discord's Components V2 system.
Components V2 uses LayoutView instead of View, allowing mixed text, media, and
interactive components in a single message.

Key differences from legacy View:
- Cannot send content, embeds, stickers, or polls with V2 messages
- Use TextDisplay for text content, Container for embed-like styling
- Buttons/Selects must be placed in ActionRow
- Maximum 40 components per LayoutView

Usage:
    from funbot.ui.components_v2 import LayoutView, Container, TextDisplay, ActionRow
"""

from __future__ import annotations

# Components
from funbot.ui.components_v2.action_row import ActionRow

# Interactive components
from funbot.ui.components_v2.button import Button

# Views
from funbot.ui.components_v2.confirm import ConfirmView
from funbot.ui.components_v2.container import Container

# Base view
from funbot.ui.components_v2.layout_view import LayoutView
from funbot.ui.components_v2.media_gallery import MediaGallery, MediaGalleryItem
from funbot.ui.components_v2.paginator import Page, PaginatorView
from funbot.ui.components_v2.section import Section
from funbot.ui.components_v2.select import Select, SelectOption
from funbot.ui.components_v2.separator import Separator
from funbot.ui.components_v2.text_display import TextDisplay
from funbot.ui.components_v2.thumbnail import Thumbnail

# Re-exports (unchanged in V2)
from funbot.ui.modal import Modal
from funbot.ui.text_input import TextInput

__all__ = (
    "ActionRow",
    "Button",
    "ConfirmView",
    "Container",
    "LayoutView",
    "MediaGallery",
    "MediaGalleryItem",
    "Modal",
    "Page",
    "PaginatorView",
    "Section",
    "Select",
    "SelectOption",
    "Separator",
    "TextDisplay",
    "TextInput",
    "Thumbnail",
)
