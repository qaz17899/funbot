"""Static Pokemon data model.

This table stores data imported from PokeAPI for all Pokemon.
Data is read-only after initial import.
"""

from __future__ import annotations

from tortoise import fields
from tortoise.models import Model


class PokemonData(Model):
    """Static Pokemon data imported from PokeAPI.

    Contains base stats and info for all 1025+ Pokemon.
    """

    class Meta:
        table = "pokemon_data"

    # Primary key: National Pokedex number
    id = fields.IntField(pk=True, description="National Pokedex number")

    # Basic info
    name = fields.CharField(max_length=50, unique=True, description="Pokemon name")
    name_ja = fields.CharField(max_length=50, null=True, description="Japanese name (optional)")

    # Types (using IntEnum values from PokemonType)
    type1 = fields.SmallIntField(description="Primary type (PokemonType enum)")
    type2 = fields.SmallIntField(null=True, default=None, description="Secondary type (optional)")

    # Base stats
    base_hp = fields.SmallIntField(description="Base HP stat")
    base_attack = fields.SmallIntField(description="Base Attack stat")
    base_defense = fields.SmallIntField(description="Base Defense stat")
    base_sp_attack = fields.SmallIntField(description="Base Sp. Attack stat")
    base_sp_defense = fields.SmallIntField(description="Base Sp. Defense stat")
    base_speed = fields.SmallIntField(description="Base Speed stat")

    # Catch/breeding info
    catch_rate = fields.SmallIntField(description="Base catch rate (0-255)")
    base_exp = fields.SmallIntField(description="Base experience yield")
    egg_cycles = fields.SmallIntField(default=20, description="Egg hatch cycles")

    # Visual
    sprite_url = fields.CharField(max_length=200, null=True, description="Sprite image URL")
    sprite_shiny_url = fields.CharField(max_length=200, null=True, description="Shiny sprite URL")

    # Region/generation
    generation = fields.SmallIntField(description="Generation (1-9)")
    region = fields.SmallIntField(description="Native region (Region enum)")

    # Evolution (simplified)
    evolves_from = fields.IntField(null=True, description="Pokemon ID this evolves from")
    evolution_level = fields.SmallIntField(
        null=True, description="Level required to evolve (if level-based)"
    )

    def __str__(self) -> str:
        return f"#{self.id} {self.name}"

    @property
    def total_stats(self) -> int:
        """Calculate total base stats."""
        return (
            self.base_hp
            + self.base_attack
            + self.base_defense
            + self.base_sp_attack
            + self.base_sp_defense
            + self.base_speed
        )
