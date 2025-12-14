"""Player's breeding eggs model.

Each row represents an egg in the player's hatchery.
Matches Pokeclicker's Egg class from Egg.ts.
"""

from __future__ import annotations

from tortoise import fields

from funbot.db.models.base import BaseModel


class PlayerEgg(BaseModel):
    """An egg in the player's hatchery slot.

    Based on Pokeclicker Egg.ts:
    - Steps-based hatching progress
    - 4 max slots (start with 1)
    - Shiny chance averaged during incubation
    """

    class Meta:
        table = "player_eggs"
        unique_together = (("user", "slot"),)

    id = fields.IntField(pk=True)

    # Owner reference
    user = fields.ForeignKeyField("models.User", related_name="eggs", on_delete=fields.CASCADE)

    # The Pokemon being hatched
    pokemon_data = fields.ForeignKeyField(
        "models.PokemonData", related_name="egg_instances", on_delete=fields.CASCADE
    )

    # Slot in hatchery (0-3)
    slot = fields.SmallIntField(description="Hatchery slot (0-3)")

    # Steps progress
    steps = fields.IntField(default=0, description="Current steps progress")
    steps_required = fields.IntField(description="Steps needed to hatch")

    # Shiny calculation (averaged during progress)
    shiny_chance = fields.IntField(default=1024, description="1 in N shiny chance")

    # Notification flag
    notified = fields.BooleanField(default=False, description="Has user been notified of ready")

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)

    # =========================================================================
    # Computed Properties
    # =========================================================================

    @property
    def progress(self) -> float:
        """Progress percentage (0-100)."""
        if self.steps_required <= 0:
            return 100.0
        return min(100.0, (self.steps / self.steps_required) * 100)

    @property
    def can_hatch(self) -> bool:
        """Check if egg is ready to hatch."""
        return self.steps >= self.steps_required

    @property
    def steps_remaining(self) -> int:
        """Steps remaining until hatch."""
        return max(0, self.steps_required - self.steps)

    def add_steps(self, amount: int) -> None:
        """Add steps to egg progress."""
        self.steps += amount
