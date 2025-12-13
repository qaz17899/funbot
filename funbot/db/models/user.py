"""User model for Discord users."""

from __future__ import annotations

from tortoise import fields

from funbot.db.models.base import BaseModel

__all__ = ("User",)


class User(BaseModel):
    """Represents a Discord user in the database.

    Attributes:
        id: Discord user ID (primary key).
        created_at: When the user was first seen.
        updated_at: When the user record was last updated.
    """

    id = fields.BigIntField(pk=True, description="Discord user ID")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # User preferences/settings can be added here
    # Example:
    # language = fields.CharField(max_length=10, default="en")

    class Meta:
        table = "users"
