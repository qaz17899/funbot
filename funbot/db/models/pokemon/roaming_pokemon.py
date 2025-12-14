"""Roaming Pokemon model for legendary encounters.

Based on Pokeclicker's roaming system:
- Legendaries roam random routes
- Route changes every 8 hours
- Some require quest completion
"""

from __future__ import annotations

from tortoise import fields
from tortoise.models import Model


class RoamingPokemon(Model):
    """Roaming legendary Pokemon that appear randomly on routes."""

    id = fields.IntField(pk=True)
    pokemon_name = fields.CharField(max_length=50, description="Pokemon name")
    region = fields.SmallIntField(description="Region where it roams")
    sub_region_group = fields.SmallIntField(
        default=0, description="Sub-region group (0=main, 1=Sevii, etc.)"
    )

    # Requirement to unlock this roaming Pokemon
    # Stored as JSON for flexibility
    requirement_data = fields.JSONField(
        null=True, description='Requirement config {"type": "quest", "quest": "Celio\'s Errand"}'
    )

    # Event-only roamers (Christmas, New Year, etc.)
    is_event = fields.BooleanField(default=False)
    event_name = fields.CharField(max_length=50, null=True)

    class Meta:
        table = "pokemon_roaming"

    def __str__(self) -> str:
        return f"{self.pokemon_name} (Region {self.region})"
