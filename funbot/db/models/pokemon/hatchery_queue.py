"""Player's hatchery queue model.

Each row represents a Pokemon waiting in the breeding queue.
Matches Pokeclicker's queueList from Breeding.ts.
"""

from __future__ import annotations

from tortoise import fields

from funbot.db.models.base import BaseModel


class HatcheryQueue(BaseModel):
    """A Pokemon waiting in the hatchery queue.

    Based on Pokeclicker Breeding.ts:
    - Queue slots gained by completing regions (4-32)
    - Auto-fills egg slots when they become available
    """

    class Meta:
        table = "hatchery_queue"

    id = fields.IntField(pk=True)

    # Owner reference
    user = fields.ForeignKeyField(
        "models.User", related_name="hatchery_queue", on_delete=fields.CASCADE
    )

    # The Pokemon to breed
    pokemon_data = fields.ForeignKeyField(
        "models.PokemonData", related_name="queue_instances", on_delete=fields.CASCADE
    )

    # Position in queue (0 = first)
    position = fields.SmallIntField(description="Queue position (0 = first)")

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
