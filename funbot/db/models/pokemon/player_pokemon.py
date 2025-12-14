"""Player's owned Pokemon model.

Each row represents a Pokemon owned by a player.
Matches Pokeclicker's extensive stat tracking system.
"""

from __future__ import annotations

from tortoise import fields

from funbot.db.models.base import BaseModel
from funbot.pokemon.constants import Gender, PokerusState


class PlayerPokemon(BaseModel):
    """A Pokemon owned by a player.

    Created when catching a new Pokemon.
    Tracks all Pokeclicker stats: EVs, vitamins, statistics, etc.

    Note: Use ExpService.calculate_attack_from_level() for attack calculations
    to maintain a single source of truth for battle formulas.
    """

    class Meta:
        table = "player_pokemon"
        unique_together = (("user", "pokemon_data"),)

    id = fields.IntField(pk=True)

    # =========================================================================
    # Core References
    # =========================================================================

    # Owner reference
    user = fields.ForeignKeyField("models.User", related_name="pokemon", on_delete=fields.CASCADE)

    # Pokemon species reference
    pokemon_data = fields.ForeignKeyField(
        "models.PokemonData", related_name="owned_by", on_delete=fields.CASCADE
    )

    # =========================================================================
    # Basic Stats (Original)
    # =========================================================================

    # Custom nickname (optional)
    nickname = fields.CharField(max_length=20, null=True)

    # Level and experience
    level = fields.SmallIntField(default=1, description="Current level (1-100)")
    exp = fields.IntField(default=0, description="Current EXP towards next level")

    # Visual flags
    shiny = fields.BooleanField(default=False, description="Is shiny variant")

    # =========================================================================
    # Pokeclicker: EVs System
    # =========================================================================

    # Effort Values - accumulated from battles
    # In Pokeclicker: evs increases when defeating Pokemon of this species
    evs = fields.FloatField(default=0.0, description="Effort Values (increases attack)")

    # =========================================================================
    # Pokeclicker: Vitamins System
    # =========================================================================

    # Vitamins boost attack power
    vitamins_protein = fields.IntField(default=0, description="Protein vitamins used")
    vitamins_calcium = fields.IntField(default=0, description="Calcium vitamins used")
    vitamins_carbos = fields.IntField(default=0, description="Carbos vitamins used")

    @property
    def vitamins_total(self) -> int:
        """Total vitamins used on this Pokemon."""
        return self.vitamins_protein + self.vitamins_calcium + self.vitamins_carbos

    # =========================================================================
    # Pokeclicker: Gender System
    # =========================================================================

    # Gender (determined at catch based on species ratio)
    gender = fields.SmallIntField(default=1, description="Gender: 0=genderless, 1=male, 2=female")

    # Display preference
    display_gender = fields.SmallIntField(
        default=1, description="Displayed gender (can differ from actual for some Pokemon)"
    )

    # =========================================================================
    # Pokeclicker: Pokerus
    # =========================================================================

    # Pokerus doubles EV gain
    pokerus = fields.SmallIntField(default=0, description="0=none, 1=infected, 2=cured")

    # =========================================================================
    # Pokeclicker: Held Item
    # =========================================================================

    # Held item (simplified - just store item name)
    held_item = fields.CharField(max_length=50, null=True, description="Held item name")

    # =========================================================================
    # Pokeclicker: UI Preferences
    # =========================================================================

    # Hide shiny sprite toggle
    hide_shiny_sprite = fields.BooleanField(default=False, description="Show normal sprite instead")

    # =========================================================================
    # Pokeclicker: Statistics (Per-Pokemon)
    # =========================================================================

    # Encounter statistics
    stat_encountered = fields.IntField(default=0, description="Times encountered in wild")
    stat_defeated = fields.IntField(default=0, description="Times defeated in battle")
    stat_captured = fields.IntField(default=0, description="Times captured")

    # Shiny statistics
    stat_shiny_encountered = fields.IntField(default=0, description="Shiny encounters")
    stat_shiny_defeated = fields.IntField(default=0, description="Shiny defeats")
    stat_shiny_captured = fields.IntField(default=0, description="Shiny captures")

    # Breeding statistics (for future)
    stat_hatched = fields.IntField(default=0, description="Times hatched from egg")
    stat_shiny_hatched = fields.IntField(default=0, description="Shiny hatches")

    # =========================================================================
    # Timestamps
    # =========================================================================

    caught_at = fields.DatetimeField(auto_now_add=True, description="When first caught")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # =========================================================================
    # Computed Properties
    # =========================================================================

    def __str__(self) -> str:
        name = self.nickname or f"Pokemon #{self.id}"
        shiny_mark = "✨" if self.shiny else ""
        return f"{shiny_mark}{name} Lv.{self.level}"

    @property
    def ev_bonus(self) -> float:
        """Calculate EV bonus multiplier (Pokeclicker formula).

        EVs give diminishing returns: bonus = 1 + (evs / 1000)
        """
        return 1.0 + (self.evs / 1000.0)

    @property
    def vitamin_bonus(self) -> int:
        """Calculate vitamin attack bonus.

        Each vitamin gives +1 attack bonus.
        """
        return self.vitamins_total

    @property
    def has_pokerus(self) -> bool:
        """Check if Pokemon has or had Pokerus."""
        return self.pokerus > 0

    @property
    def is_pokerus_active(self) -> bool:
        """Check if Pokerus is currently active (can spread)."""
        return self.pokerus == PokerusState.INFECTED

    @property
    def gender_symbol(self) -> str:
        """Get gender symbol for display."""
        if self.gender == Gender.MALE:
            return "♂"
        if self.gender == Gender.FEMALE:
            return "♀"
        return ""
