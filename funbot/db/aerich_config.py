"""Aerich-specific Tortoise ORM configuration.

This is a lightweight config that only loads database settings,
avoiding validation of Discord-specific fields that aren't needed
for database migrations.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# Aerich only needs the database URL
# Tortoise ORM requires 'postgres://' scheme, not 'postgresql://'
_raw_db_url = os.getenv("DB_URL", "postgres://localhost:5432/funbot")
DB_URL = _raw_db_url.replace("postgresql://", "postgres://")

TORTOISE_CONFIG = {
    "connections": {"default": DB_URL},
    "apps": {
        "models": {"models": ["funbot.db.models", "aerich.models"], "default_connection": "default"}
    },
    "use_tz": True,
    "timezone": "UTC",
}
