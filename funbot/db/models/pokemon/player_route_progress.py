"""Player route progress tracking.

Tracks:
- Kills per route (for RouteKillRequirement)
- Unlocked status

NOTE: Caught pokemon is NOT stored here!
Use PlayerPokedex to check which Pokemon the player has caught.
This avoids redundancy and ensures catching anywhere updates route status.
"""

from __future__ import annotations

from tortoise import fields

from funbot.db.models.base import BaseModel


class PlayerRouteProgress(BaseModel):
    """Player's progress on a specific route."""

    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="route_progress", on_delete=fields.CASCADE
    )
    route = fields.ForeignKeyField(
        "models.RouteData", related_name="player_progress", on_delete=fields.CASCADE
    )

    kills = fields.IntField(default=0, description="Pokemon defeated on this route")
    is_unlocked = fields.BooleanField(default=False)
    first_cleared_at = fields.DatetimeField(null=True, description="When requirements first met")

    # NOTE: Do NOT store caught_pokemon here!
    # Use PlayerPokedex to check route completion status.

    class Meta:
        table = "pokemon_player_route_progress"
        unique_together = (("user", "route"),)
