"""Route Data model - stores route information from Pokeclicker.

Each route has:
- Pokemon distributions (land/water/headbutt)
- Unlock requirements
- Progress tracking per player
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tortoise import fields

from funbot.db.models.base import BaseModel

if TYPE_CHECKING:
    from funbot.db.models.pokemon.route_requirement import RouteRequirement


class RouteData(BaseModel):
    """Pokemon route data from Pokeclicker."""

    id = fields.IntField(pk=True)
    region = fields.SmallIntField(description="Region index (0=Kanto, 1=Johto...)")
    number = fields.IntField(description="Route number (1, 2, 22, 101...)")
    name = fields.CharField(max_length=50, description="Display name (Kanto Route 1)")
    order_number = fields.FloatField(description="Progression order (1.0, 1.1, 2.0 for branching)")
    sub_region = fields.SmallIntField(null=True, description="Sub-region (Sevii Islands, etc.)")
    custom_health = fields.IntField(null=True, description="Override route health formula")

    # Pokemon distributions (JSON arrays of pokemon names)
    land_pokemon = fields.JSONField(
        default=list, description='Land encounters ["Pidgey", "Rattata"]'
    )
    water_pokemon = fields.JSONField(default=list, description="Water encounters (needs Super_rod)")
    headbutt_pokemon = fields.JSONField(default=list, description="Headbutt tree encounters")

    # Routes with DevelopmentRequirement are not fully implemented yet
    is_implemented = fields.BooleanField(
        default=True, description="False for routes with DevelopmentRequirement"
    )

    # Reverse relation from RouteRequirement
    requirements: fields.ReverseRelation[RouteRequirement]

    class Meta:
        table = "pokemon_route_data"
        unique_together = (("region", "number"),)

    def __str__(self) -> str:
        return self.name
