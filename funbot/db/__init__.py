"""Database module.

Uses lazy imports to avoid triggering config validation when only models are needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from funbot.db.database import Database

__all__ = ("Database",)


def __getattr__(name: str):
    """Lazy import to avoid circular imports with config."""
    if name == "Database":
        from funbot.db.database import Database

        return Database
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
