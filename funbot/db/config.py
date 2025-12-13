"""Tortoise ORM configuration."""

from __future__ import annotations

from funbot.config import CONFIG

# Tortoise ORM requires 'postgres://' scheme, not 'postgresql://'
_db_url = CONFIG.db_url
if _db_url.startswith("postgresql://"):
    _db_url = "postgres://" + _db_url[len("postgresql://") :]

# Tortoise ORM configuration
TORTOISE_CONFIG = {
    "connections": {"default": _db_url},
    "apps": {
        "models": {"models": ["funbot.db.models", "aerich.models"], "default_connection": "default"}
    },
    "use_tz": True,
    "timezone": "UTC",
}
