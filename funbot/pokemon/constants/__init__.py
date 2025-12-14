# Pokemon Constants
"""Constants and enums for the Pokemon system."""

from __future__ import annotations

from funbot.pokemon.constants.enums import (
    POKEBALL_BONUS,
    ROUTE_STATUS_EMOJI,
    Currency,
    KeyItemType,
    Pokeball,
    PokemonType,
    QuestLineState,
    Region,
    RequirementType,
    RouteStatus,
)
from funbot.pokemon.constants.game_constants import (
    BASE_CATCH_RATE,
    BASE_EXP_MODIFIER,
    BATTLE_TICK_SECONDS,
    EXP_SCALE_FACTOR,
    ROUTE_HEALTH_BASE,
    ROUTE_MONEY_BASE,
    SHINY_CHANCE,
)
from funbot.pokemon.constants.type_chart import TYPE_EFFECTIVENESS

__all__ = [
    # Constants
    "BASE_CATCH_RATE",
    "BASE_EXP_MODIFIER",
    "BATTLE_TICK_SECONDS",
    "EXP_SCALE_FACTOR",
    "POKEBALL_BONUS",
    "ROUTE_HEALTH_BASE",
    "ROUTE_MONEY_BASE",
    "ROUTE_STATUS_EMOJI",
    "SHINY_CHANCE",
    # Type chart
    "TYPE_EFFECTIVENESS",
    # Enums
    "Currency",
    "KeyItemType",
    "Pokeball",
    "PokemonType",
    "QuestLineState",
    "Region",
    "RequirementType",
    "RouteStatus",
]
