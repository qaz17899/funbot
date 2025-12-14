"""Player's owned Pokemon model.

Each row represents a Pokemon owned by a player.
Matches Pokeclicker's exact stat tracking system.
"""

from __future__ import annotations

import math

from tortoise import fields

from funbot.db.models.base import BaseModel
from funbot.pokemon.constants import Gender, PokerusState
from funbot.pokemon.constants.game_constants import EP_EV_RATIO, RESISTANT_EV_THRESHOLD


class PlayerPokemon(BaseModel):
    """A Pokemon owned by a player.

    Created when catching a new Pokemon.
    Tracks all Pokeclicker stats exactly as the original.

    EVs System (Pokeclicker):
    - Stores effort_points (raw value)
    - EVs = effort_points / 1000
    - Only Pokemon with Pokerus >= CONTAGIOUS can gain EVs
    - EVs are gained when RE-CATCHING the same Pokemon, not from defeating

    EV Bonus Formula:
    - EVs < 50: bonus = 1 + 0.01 * evs (linear)
    - EVs >= 50: bonus = evs^(log(1.5)/log(50)) (diminishing returns)

    TODO: Pokerus Spreading (requires Hatchery system)
    - Per PartyPokemon.ts:160-192:
    - Spreads only in Hatchery between manually-bred eggs
    - Contagious/Resistant Pokemon can spread to same-type Pokemon
    - INFECTED->CONTAGIOUS upgrade happens when egg hatches
    - Current simplification: Starter gets CONTAGIOUS immediately
    """

    class Meta:
        table = "player_pokemon"
        unique_together = (("user", "pokemon_data"),)

    id = fields.IntField(pk=True)

    # =========================================================================
    # Core References
    # =========================================================================

    user = fields.ForeignKeyField("models.User", related_name="pokemon", on_delete=fields.CASCADE)
    pokemon_data = fields.ForeignKeyField(
        "models.PokemonData", related_name="owned_by", on_delete=fields.CASCADE
    )

    # =========================================================================
    # Basic Stats
    # =========================================================================

    nickname = fields.CharField(max_length=20, null=True)
    level = fields.SmallIntField(default=1, description="Current level (1-100)")
    exp = fields.IntField(default=0, description="Current EXP towards next level")
    shiny = fields.BooleanField(default=False, description="Is shiny variant")

    # =========================================================================
    # Pokeclicker: EVs System (CORRECTED)
    # =========================================================================

    # Raw effort points (NOT EVs directly!)
    # EVs = effort_points / EP_EV_RATIO (1000)
    # EVs are gained by RE-CATCHING Pokemon, not by defeating
    effort_points = fields.IntField(default=0, description="Raw effort points (EVs = EP/1000)")

    # =========================================================================
    # Pokeclicker: Gender System
    # =========================================================================

    gender = fields.SmallIntField(default=1, description="0=genderless, 1=male, 2=female")
    display_gender = fields.SmallIntField(default=1, description="Displayed gender preference")

    # =========================================================================
    # Pokeclicker: Pokerus (4 states - CORRECTED)
    # =========================================================================

    # 0=Uninfected, 1=Infected, 2=Contagious, 3=Resistant
    # Only Contagious (2) and Resistant (3) can gain EVs
    pokerus = fields.SmallIntField(default=0, description="Pokerus state (0-3)")

    # =========================================================================
    # Pokeclicker: Held Item
    # =========================================================================

    held_item = fields.CharField(max_length=50, null=True, description="Held item name")

    # =========================================================================
    # Pokeclicker: UI Preferences
    # =========================================================================

    hide_shiny_sprite = fields.BooleanField(default=False, description="Show normal sprite instead")

    # =========================================================================
    # Pokeclicker: Statistics (Per-Pokemon)
    # =========================================================================

    stat_encountered = fields.IntField(default=0, description="Times encountered")
    stat_defeated = fields.IntField(default=0, description="Times defeated")
    stat_captured = fields.IntField(default=0, description="Times captured")
    stat_shiny_encountered = fields.IntField(default=0, description="Shiny encounters")
    stat_shiny_defeated = fields.IntField(default=0, description="Shiny defeats")
    stat_shiny_captured = fields.IntField(default=0, description="Shiny captures")
    stat_hatched = fields.IntField(default=0, description="Times hatched")
    stat_shiny_hatched = fields.IntField(default=0, description="Shiny hatches")

    # =========================================================================
    # Pokeclicker: Breeding System
    # =========================================================================

    # Whether this Pokemon is currently in the hatchery
    breeding = fields.BooleanField(default=False, description="In hatchery")

    # Attack bonuses from hatching (from Egg.hatch() lines 134-136)
    # attackBonusPercent += BREEDING_ATTACK_BONUS + calcium
    # attackBonusAmount += protein
    attack_bonus_percent = fields.IntField(default=0, description="% attack bonus from breeding")
    attack_bonus_amount = fields.IntField(default=0, description="Flat attack bonus from breeding")

    # =========================================================================
    # Pokeclicker: Vitamin System (PartyPokemon.ts:77-78, 421-428)
    # =========================================================================

    # Vitamins applied to this Pokemon (max = (region + 1) * 5 total)
    # - Protein: +1 flat attack bonus per hatch
    # - Calcium: +1% attack bonus per hatch
    # - Carbos: Reduce egg steps formula
    vitamin_protein = fields.SmallIntField(default=0, description="Protein uses (+flat ATK/hatch)")
    vitamin_calcium = fields.SmallIntField(default=0, description="Calcium uses (+% ATK/hatch)")
    vitamin_carbos = fields.SmallIntField(default=0, description="Carbos uses (reduce steps)")

    # =========================================================================
    # Timestamps
    # =========================================================================

    caught_at = fields.DatetimeField(auto_now_add=True, description="When first caught")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # =========================================================================
    # Computed Properties (Pokeclicker formulas)
    # =========================================================================

    def __str__(self) -> str:
        name = self.nickname or f"Pokemon #{self.id}"
        shiny_mark = "✨" if self.shiny else ""
        return f"{shiny_mark}{name} Lv.{self.level}"

    @property
    def evs(self) -> float:
        """Calculate EVs from effort points (Pokeclicker: EP / 1000)."""
        return self.effort_points / EP_EV_RATIO

    @property
    def ev_bonus(self) -> float:
        """Calculate EV attack bonus (exact Pokeclicker formula).

        From PartyPokemon.ts:412-417:
        - No bonus if Pokerus < Contagious
        - EVs < 50: linear bonus (1 + 0.01 * evs)
        - EVs >= 50: diminishing returns (evs^(log(1.5)/log(50)))

        Examples:
            0 EVs = 1.00x
            25 EVs = 1.25x
            50 EVs = 1.50x
            802 EVs = 2.00x
            40,121 EVs = 3.00x
        """
        # Must have Contagious or Resistant Pokerus to get EV bonus
        if self.pokerus < PokerusState.CONTAGIOUS:
            return 1.0

        evs = self.evs
        if evs < 50:
            # Linear: +1% per EV
            return 1.0 + 0.01 * evs
        # Diminishing returns formula
        return evs ** (math.log(1.5) / math.log(50))

    @property
    def vitamin_bonus(self) -> int:
        """Calculate total vitamins used on this Pokemon."""
        return self.vitamin_protein + self.vitamin_calcium + self.vitamin_carbos

    @property
    def total_vitamins_used(self) -> int:
        """Alias for vitamin_bonus (Pokeclicker compatibility)."""
        return self.vitamin_bonus

    def calculate_attack(self, base_attack: int, ignore_level: bool = False) -> int:
        """Calculate total attack (exact Pokeclicker formula).

        From PartyPokemon.ts:140-146:
        attackBonusMultiplier = 1 + (attackBonusPercent / 100)
        levelMultiplier = level / 100
        return (baseAttack * attackBonusMultiplier + attackBonusAmount)
               * levelMultiplier * evsMultiplier * heldItem * shadow

        Args:
            base_attack: The Pokemon's base attack from PokemonData
            ignore_level: If True, use 1.0 for level multiplier (for breeding efficiency)

        Returns:
            Final attack value
        """
        # Breeding attack bonus multiplier: +1% per point of attackBonusPercent
        attack_bonus_multiplier = 1.0 + (self.attack_bonus_percent / 100)

        # Level multiplier: level/100 (Lv.100 = 1.0x)
        level_multiplier = 1.0 if ignore_level else self.level / 100

        # EV bonus (requires Contagious+ Pokerus)
        ev_multiplier = self.ev_bonus

        # TODO: held_item_multiplier and shadow_multiplier when implemented
        held_item_multiplier = 1.0
        shadow_multiplier = 1.0

        return max(
            1,
            int(
                (base_attack * attack_bonus_multiplier + self.attack_bonus_amount)
                * level_multiplier
                * ev_multiplier
                * held_item_multiplier
                * shadow_multiplier
            ),
        )

    @property
    def is_resistant(self) -> bool:
        """Check if Pokemon has reached Resistant status (EVs >= 50)."""
        return self.evs >= RESISTANT_EV_THRESHOLD

    @property
    def can_gain_evs(self) -> bool:
        """Check if Pokemon can gain EVs (requires Contagious or Resistant Pokerus)."""
        return self.pokerus >= PokerusState.CONTAGIOUS

    @property
    def has_pokerus(self) -> bool:
        """Check if Pokemon has any Pokerus status."""
        return self.pokerus > PokerusState.UNINFECTED

    @property
    def is_pokerus_contagious(self) -> bool:
        """Check if Pokerus can spread (Contagious or Resistant)."""
        return self.pokerus >= PokerusState.CONTAGIOUS

    @property
    def gender_symbol(self) -> str:
        """Get gender symbol for display."""
        if self.gender == Gender.MALE:
            return "♂"
        if self.gender == Gender.FEMALE:
            return "♀"
        return ""

    def gain_effort_points(self, base_ep: int, *, shiny: bool = False, shadow: bool = False) -> int:
        """Add effort points to this Pokemon (called when re-catching).

        Only works if Pokemon has Contagious or Resistant Pokerus.

        Args:
            base_ep: Base effort points yield
            shiny: If caught Pokemon was shiny (5x multiplier)
            shadow: If caught Pokemon was shadow (2x multiplier)

        Returns:
            Actual effort points gained (0 if no Pokerus)
        """
        if not self.can_gain_evs:
            return 0

        ep = base_ep
        if shiny:
            ep *= 5  # SHINY_EP_MODIFIER
        if shadow:
            ep *= 2  # SHADOW_EP_MODIFIER

        self.effort_points += ep

        # Auto-upgrade to Resistant when reaching 50 EVs
        if self.evs >= RESISTANT_EV_THRESHOLD and self.pokerus == PokerusState.CONTAGIOUS:
            self.pokerus = PokerusState.RESISTANT

        return ep
