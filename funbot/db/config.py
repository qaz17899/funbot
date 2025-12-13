"""Tortoise ORM configuration."""

from __future__ import annotations

from funbot.config import CONFIG

# Tortoise ORM configuration
TORTOISE_CONFIG = {
    "connections": {"default": CONFIG.db_url},
    "apps": {
        "models": {"models": ["funbot.db.models", "aerich.models"], "default_connection": "default"}
    },
    "use_tz": True,
    "timezone": "UTC",
}
