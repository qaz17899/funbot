"""Pokemon system enums.

Centralized location for all Pokemon-related enumerations.
"""

from __future__ import annotations

from enum import Enum, IntEnum, auto

# =============================================================================
# Pokemon Types and Regions
# =============================================================================


class PokemonType(IntEnum):
    """Pokemon types (Gen 1-9)."""

    NONE = 0
    NORMAL = 1
    FIRE = 2
    WATER = 3
    ELECTRIC = 4
    GRASS = 5
    ICE = 6
    FIGHTING = 7
    POISON = 8
    GROUND = 9
    FLYING = 10
    PSYCHIC = 11
    BUG = 12
    ROCK = 13
    GHOST = 14
    DRAGON = 15
    DARK = 16
    STEEL = 17
    FAIRY = 18


class Region(IntEnum):
    """Pokemon game regions."""

    NONE = -1
    KANTO = 0  # Gen 1
    JOHTO = 1  # Gen 2
    HOENN = 2  # Gen 3
    SINNOH = 3  # Gen 4
    UNOVA = 4  # Gen 5
    KALOS = 5  # Gen 6
    ALOLA = 6  # Gen 7
    GALAR = 7  # Gen 8
    PALDEA = 8  # Gen 9


# =============================================================================
# Items and Currency
# =============================================================================


class Currency(IntEnum):
    """Pokemon currency types."""

    POKEDOLLAR = 0
    DUNGEON_TOKEN = auto()
    BATTLE_POINT = auto()
    QUEST_POINT = auto()


class Pokeball(IntEnum):
    """Pokeball types for catching."""

    NONE = 0  # Don't attempt to catch
    POKEBALL = 1
    GREATBALL = 2
    ULTRABALL = 3
    MASTERBALL = 4


# Pokeball catch rate bonuses
POKEBALL_BONUS: dict[Pokeball, float] = {
    Pokeball.NONE: 0.0,
    Pokeball.POKEBALL: 0.0,
    Pokeball.GREATBALL: 5.0,
    Pokeball.ULTRABALL: 10.0,
    Pokeball.MASTERBALL: 100.0,  # Always catch
}


# =============================================================================
# Pokemon Attributes
# =============================================================================


class Gender(IntEnum):
    """Pokemon gender."""

    GENDERLESS = 0
    MALE = 1
    FEMALE = 2


class PokerusState(IntEnum):
    """Pokerus infection state (exact Pokeclicker values).

    From GameConstants.ts:2424-2429:
    - UNINFECTED: Can contract virus, cannot gain EVs
    - INFECTED: Just contracted, cannot gain EVs yet, cannot spread
    - CONTAGIOUS: Can gain EVs, can spread to others in Hatchery
    - RESISTANT: EVs >= 50, can gain EVs, can spread, counts for achievements
    """

    UNINFECTED = 0  # Base state, can contract virus
    INFECTED = 1  # Just contracted, needs to hatch once
    CONTAGIOUS = 2  # Can gain EVs and spread
    RESISTANT = 3  # EVs >= 50, permanent EV gains


# =============================================================================
# Loot and Rewards
# =============================================================================


class LootTier(str, Enum):
    """Loot tier classifications matching PokeClicker."""

    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"
