"""Pokemon system enums."""

from __future__ import annotations

from enum import IntEnum, auto


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
