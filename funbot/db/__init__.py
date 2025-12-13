"""Database module.

Uses lazy imports to avoid triggering config validation when only models are needed.
"""

from __future__ import annotations

from typing import Any

# Note: Most exports are lazy-loaded via __getattr__ to avoid circular imports
# Use: from funbot.db import Database, build_query, etc.

_MODULE_NAME = __name__

# Names that can be lazy-loaded
_LAZY_NAMES = {"Database", "build_query", "execute_raw", "fetch_all", "fetch_one", "fetch_val"}


def __getattr__(name: str) -> Any:
    """Lazy import to avoid circular imports with config."""
    if name == "Database":
        from funbot.db.database import Database  # noqa: PLC0415

        return Database
    if name in {
        "build_query",
        "build_exclude_query",
        "execute_raw",
        "fetch_all",
        "fetch_one",
        "fetch_val",
    }:
        from funbot.db import utils  # noqa: PLC0415

        return getattr(utils, name)
    msg = f"module {_MODULE_NAME!r} has no attribute {name!r}"
    raise AttributeError(msg)
