"""Database module.

Uses lazy imports to avoid triggering config validation when only models are needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from funbot.db.database import Database

__all__ = ("Database",)

_MODULE_NAME = __name__


def __getattr__(name: str) -> Any:
    """Lazy import to avoid circular imports with config."""
    if name == "Database":
        from funbot.db.database import Database  # noqa: PLC0415

        return Database
    msg = f"module {_MODULE_NAME!r} has no attribute {name!r}"
    raise AttributeError(msg)
