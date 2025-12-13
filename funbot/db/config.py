"""Tortoise ORM configuration."""

from __future__ import annotations

from funbot.config import CONFIG

# Tortoise ORM requires 'postgres://' scheme, not 'postgresql://'
_db_url = CONFIG.db_url.replace("postgresql://", "postgres://")

# Tortoise ORM configuration
TORTOISE_CONFIG = {
    "connections": {"default": _db_url},
    "apps": {
        "models": {"models": ["funbot.db.models", "aerich.models"], "default_connection": "default"}
    },
    "use_tz": True,
    "timezone": "UTC",
}
