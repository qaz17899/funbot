"""Enhanced TextInput with validation support."""

from __future__ import annotations

import discord
from discord.utils import MISSING

__all__ = ("TextInput",)


class TextInput(discord.ui.TextInput):
    """Enhanced TextInput with numeric validation support.

    Features:
    - is_digit: Validate input as a number
    - min_value/max_value: Range validation for numeric inputs
    """

    def __init__(
        self,
        *,
        label: str,
        style: discord.TextStyle = discord.TextStyle.short,
        custom_id: str = MISSING,
        placeholder: str | None = None,
        default: str | None = None,
        required: bool = True,
        min_length: int | None = None,
        max_length: int | None = None,
        row: int | None = None,
        is_digit: bool = False,
        min_value: int | None = None,
        max_value: int | None = None,
    ) -> None:
        super().__init__(
            label=label,
            style=style,
            custom_id=custom_id,
            placeholder=placeholder,
            default=default,
            required=required,
            min_length=min_length,
            max_length=max_length,
            row=row,
        )

        self.is_digit = is_digit
        self.min_value = min_value
        self.max_value = max_value

        # Auto-generate placeholder for numeric inputs
        if is_digit and placeholder is None:
            if min_value is not None and max_value is not None:
                self.placeholder = f"({min_value} ~ {max_value})"
            elif min_value is not None:
                self.placeholder = f"(≥{min_value})"
            elif max_value is not None:
                self.placeholder = f"(≤{max_value})"

    def validate(self) -> tuple[bool, str | None]:
        """Validate the input value.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not self.is_digit:
            return True, None

        try:
            value = int(self.value)
        except ValueError:
            return False, f"{self.label} must be a number."

        if self.min_value is not None and value < self.min_value:
            return False, f"{self.label} must be at least {self.min_value}."

        if self.max_value is not None and value > self.max_value:
            return False, f"{self.label} must be at most {self.max_value}."

        return True, None

    @property
    def int_value(self) -> int | None:
        """Get the value as an integer, or None if invalid."""
        try:
            return int(self.value)
        except ValueError:
            return None
