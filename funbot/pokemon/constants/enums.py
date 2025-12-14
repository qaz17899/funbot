"""Pokemon system enums.

Centralized location for all Pokemon-related enumerations.
"""

from __future__ import annotations

from enum import IntEnum, auto

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


class KeyItemType(IntEnum):
    """Key items from Pokeclicker."""

    TEACHY_TV = 0
    COIN_CASE = 1
    POKEBALL_BAG = 2
    TOWN_MAP = 3
    DUNGEON_TICKET = 4
    SUPER_ROD = 5  # Unlocks water Pokemon!
    HOLO_CASTER = 6
    MYSTERY_EGG = 7
    SAFARI_TICKET = 8
    WAILMER_PAIL = 9
    EXPLORER_KIT = 10
    EON_TICKET = 11
    EVENT_CALENDAR = 12
    GEM_CASE = 13
    DNA_SPLICERS = 14
    REINS_OF_UNITY = 15
    POKERUS_VIRUS = 16
    Z_POWER_RING = 17


# =============================================================================
# Route and Progress Status
# =============================================================================


class RouteStatus(IntEnum):
    """Route status matching PokéClicker's areaStatus.

    Fixed priority order (highest to lowest):
    1. LOCKED - Can't access yet
    2. INCOMPLETE - Kills < 10
    3. QUEST_AT_LOCATION - Has active quest (not implemented yet)
    4. UNCAUGHT_POKEMON - Has new Pokemon
    5. UNCAUGHT_SHINY - Missing shiny variants
    6. COMPLETED - Everything done
    """

    LOCKED = 0
    INCOMPLETE = 1
    QUEST_AT_LOCATION = 2
    UNCAUGHT_POKEMON = 3
    UNCAUGHT_SHINY = 4
    COMPLETED = 5


# Emoji mapping for each route status
ROUTE_STATUS_EMOJI: dict[RouteStatus, str] = {
    RouteStatus.LOCKED: "🔒",
    RouteStatus.INCOMPLETE: "⚔️",
    RouteStatus.QUEST_AT_LOCATION: "📋",
    RouteStatus.UNCAUGHT_POKEMON: "🆕",
    RouteStatus.UNCAUGHT_SHINY: "✨",
    RouteStatus.COMPLETED: "🌈",
}


# =============================================================================
# Requirements System
# =============================================================================


class RequirementType(IntEnum):
    """Types of route unlock requirements."""

    # Leaf nodes (basic conditions)
    ROUTE_KILL = 1  # RouteKillRequirement(10, Region.kanto, 1)
    GYM_BADGE = 2  # GymBadgeRequirement(BadgeEnums.Boulder)
    DUNGEON_CLEAR = 3  # ClearDungeonRequirement(1, getDungeonIndex('Mt. Moon'))
    TEMP_BATTLE = 4  # TemporaryBattleRequirement('Blue 2')
    QUEST_LINE_COMPLETED = 5  # QuestLineCompletedRequirement('Celio\'s Errand')
    QUEST_LINE_STEP = 6  # QuestLineStepCompletedRequirement('Bill\'s Errand', 0)
    OBTAINED_POKEMON = 7  # ObtainedPokemonRequirement('Sunkern')
    WEATHER = 8  # WeatherRequirement
    DAY_OF_WEEK = 9  # DayOfWeekRequirement
    SPECIAL_EVENT = 10  # SpecialEventRequirement
    ITEM_OWNED = 11  # ItemOwnedRequirement
    STATISTIC = 12  # StatisticRequirement
    POKEMON_LEVEL = 13  # PokemonLevelRequirement

    # Branch nodes (logical operators)
    ONE_FROM_MANY = 100  # OR - at least one child must pass
    MULTI = 101  # AND - all children must pass


# =============================================================================
# Quest System
# =============================================================================


class QuestLineState(IntEnum):
    """Quest line state matching Pokeclicker's QuestLineState.ts.

    Pokeclicker source:
        enum QuestLineState {
            inactive = 0,
            started = 1,
            ended = 2,
        }
    """

    INACTIVE = 0  # Not started
    STARTED = 1  # In progress
    ENDED = 2  # Completed
