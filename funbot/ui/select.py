"""Enhanced Select with loading state support."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.utils import MISSING

if TYPE_CHECKING:
    from funbot.types import Interaction

    from .view import View

__all__ = ("Select", "SelectOption")


class SelectOption(discord.SelectOption):
    """Enhanced SelectOption - same as discord.py version but can be extended."""


class Select[V_co: View](discord.ui.Select):
    """Enhanced Select with loading state support.

    Type parameter V_co allows type-safe access to self.view.
    """

    def __init__(
        self,
        *,
        custom_id: str = MISSING,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        options: list[SelectOption],
        disabled: bool = False,
        row: int | None = None,
    ) -> None:
        # Handle empty options
        if not options:
            options = [SelectOption(label="No options", value="0")]
            disabled = True

        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            options=options,  # type: ignore
            disabled=disabled,
            row=row,
        )

        # Store original state for loading state management
        self.original_placeholder: str | None = None
        self.original_options: list[SelectOption] | None = None
        self.original_disabled: bool | None = None
        self.original_max_values: int | None = None
        self.original_min_values: int | None = None

        self.view: V_co

    async def set_loading_state(self, interaction: Interaction) -> None:
        """Set the select to a loading state."""
        self.original_options = list(self.options)  # type: ignore
        self.original_disabled = self.disabled
        self.original_placeholder = self.placeholder[:] if self.placeholder else None
        self.original_max_values = self.max_values
        self.original_min_values = self.min_values

        self.view.disable_items()

        self.options = [SelectOption(label="Loading...", value="loading", default=True, emoji="⏳")]  # type: ignore
        self.disabled = True
        self.max_values = 1
        self.min_values = 1

        await self.view.absolute_edit(interaction, view=self.view)

    async def unset_loading_state(self, interaction: Interaction, **kwargs) -> None:
        """Restore the select from loading state."""
        if (
            self.original_options is None
            or self.original_disabled is None
            or self.original_max_values is None
            or self.original_min_values is None
        ):
            msg = "unset_loading_state called before set_loading_state"
            raise RuntimeError(msg)

        self.view.enable_items()

        self.options = self.original_options  # type: ignore
        self.disabled = self.original_disabled
        self.placeholder = self.original_placeholder
        self.max_values = self.original_max_values
        self.min_values = self.original_min_values

        self.update_options_defaults()

        await self.view.absolute_edit(interaction, view=self.view, **kwargs)

    def update_options_defaults(self, *, values: list[str] | None = None) -> None:
        """Update which options are marked as default based on current values."""
        values = values or self.values
        for option in self.options:
            option.default = option.value in values

    def reset_options_defaults(self) -> None:
        """Reset all options to non-default."""
        for option in self.options:
            option.default = False
