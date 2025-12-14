"""Player's Pokeball settings for auto-catching.

Based on Pokeclicker's Pokeball settings UI.
"""

from __future__ import annotations

from tortoise import fields

from funbot.db.models.base import BaseModel
from funbot.pokemon.constants.enums import Pokeball


class PlayerPokeballSettings(BaseModel):
    """Pokeball auto-catch settings for a player.

    Determines which Pokeball to use (or NONE to skip) for each category.
    """

    class Meta:
        table = "player_pokeball_settings"

    id = fields.IntField(pk=True)

    # Owner reference (one-to-one)
    user = fields.OneToOneField(
        "models.User", related_name="pokeball_settings", on_delete=fields.CASCADE
    )

    # Settings: which ball to use for each category
    # Values are Pokeball enum integers (0=NONE, 1=POKEBALL, 2=GREATBALL, 3=ULTRABALL, 4=MASTERBALL)
    new_shiny = fields.SmallIntField(
        default=3,
        description="Ball for new shiny Pokemon",  # ULTRABALL
    )
    new_pokemon = fields.SmallIntField(
        default=1,
        description="Ball for new (uncaught) Pokemon",  # POKEBALL
    )
    caught_shiny = fields.SmallIntField(
        default=1,
        description="Ball for already caught shiny",  # POKEBALL
    )
    caught_pokemon = fields.SmallIntField(
        default=0, description="Ball for already caught Pokemon (NONE = don't catch)"
    )

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    def __str__(self) -> str:
        return f"PokeballSettings(id={self.id})"

    def to_dict(self) -> dict:
        """Convert settings to dict for CatchService."""
        return {
            "new_shiny": self.new_shiny,
            "new_pokemon": self.new_pokemon,
            "caught_shiny": self.caught_shiny,
            "caught_pokemon": self.caught_pokemon,
        }

    def get_ball_name(self, category: str) -> str:
        """Get ball name for a category.

        Args:
            category: One of 'new_shiny', 'new_pokemon', 'caught_shiny', 'caught_pokemon'

        Returns:
            Ball name string
        """
        ball_value = getattr(self, category, Pokeball.NONE)
        return Pokeball(ball_value).name.replace("_", " ").title()
