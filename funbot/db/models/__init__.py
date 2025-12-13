"""Database models."""

from __future__ import annotations

from funbot.db.models.base import BaseModel, CachedModel
from funbot.db.models.user import User

__all__ = ("BaseModel", "CachedModel", "User")
