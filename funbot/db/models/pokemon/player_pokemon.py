"""Player's owned Pokemon model.

Each row represents a Pokemon owned by a player.
"""

from __future__ import annotations

from tortoise import fields
from tortoise.models import Model


class PlayerPokemon(Model):
    """A Pokemon owned by a player.

    Created when catching a new Pokemon.
    """

    class Meta:
        table = "player_pokemon"
        unique_together = (("user", "pokemon_data"),)

    id = fields.IntField(pk=True)

    # Owner reference
    user = fields.ForeignKeyField("models.User", related_name="pokemon", on_delete=fields.CASCADE)

    # Pokemon species reference
    pokemon_data = fields.ForeignKeyField(
        "models.PokemonData", related_name="owned_by", on_delete=fields.CASCADE
    )

    # Custom nickname (optional)
    nickname = fields.CharField(max_length=20, null=True)

    # Stats
    level = fields.SmallIntField(default=1, description="Current level (1-100)")
    exp = fields.IntField(default=0, description="Current EXP towards next level")
    attack_bonus = fields.SmallIntField(default=0, description="Bonus attack from vitamins etc.")

    # Special flags
    shiny = fields.BooleanField(default=False, description="Is shiny variant")
    caught_at = fields.DatetimeField(auto_now_add=True, description="When caught")

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    def __str__(self) -> str:
        name = self.nickname or f"Pokemon #{self.pokemon_data_id}"
        shiny_mark = "✨" if self.shiny else ""
        return f"{shiny_mark}{name} Lv.{self.level}"

    async def calculate_attack(self) -> int:
        """Calculate total attack power.

        Returns:
            Attack stat based on base_attack, level, and bonus
        """
        # Need to load related pokemon_data if not already loaded
        if not hasattr(self, "_pokemon_data") or self._pokemon_data is None:
            await self.fetch_related("pokemon_data")

        pokemon = self.pokemon_data  # type: ignore
        base_attack = pokemon.base_attack

        # Level scaling: attack grows ~3x from level 1 to 100
        level_multiplier = 1 + (self.level - 1) * 0.02

        return int(base_attack * level_multiplier) + self.attack_bonus
