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

    # =========================================================================
    # Pokeclicker: Hatchery System
    # =========================================================================

    # Egg slots (1-4, can purchase more with Quest Points)
    hatchery_egg_slots = fields.SmallIntField(default=1, description="Unlocked egg slots (1-4)")

    # Queue slots (4-32, gained by completing regions)
    # Formula: min(32, max(4, 4 * 2^(region-1)))
    # Kanto = 0+4 = 4, Johto = 8, Hoenn = 16, Sinnoh = 32
    hatchery_queue_slots = fields.SmallIntField(
        default=0, description="Unlocked queue slots (0-32)"
    )

    # Highest completed region (0 = none, 1 = Kanto, etc.)
    highest_region = fields.SmallIntField(default=0, description="Highest completed region")

    class Meta:
        table = "users"
