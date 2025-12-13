"""UI components - Enhanced Discord UI components (legacy View-based)."""

from __future__ import annotations

from funbot.ui.components.button import Button, GoBackButton
from funbot.ui.components.confirm import ConfirmView
from funbot.ui.components.modal import Modal
from funbot.ui.components.paginator import Page, PaginatorView
from funbot.ui.components.select import Select, SelectOption
from funbot.ui.components.text_input import TextInput
from funbot.ui.components.toggle import ToggleButton
from funbot.ui.components.url_button import URLButtonView
from funbot.ui.components.view import View

__all__ = (
    "Button",
    "ConfirmView",
    "GoBackButton",
    "Modal",
    "Page",
    "PaginatorView",
    "Select",
    "SelectOption",
    "TextInput",
    "ToggleButton",
    "URLButtonView",
    "View",
)
