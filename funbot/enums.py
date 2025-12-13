"""Shared enumerations for the bot."""

from __future__ import annotations

from enum import StrEnum, auto


class Environment(StrEnum):
    """Application environment types."""

    DEV = auto()
    TEST = auto()
    PROD = auto()


class CommandCategory(StrEnum):
    """Command categories for organization."""

    ADMIN = auto()
    FUN = auto()
    UTILITY = auto()
    GAME = auto()
