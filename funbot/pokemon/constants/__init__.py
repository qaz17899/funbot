# Pokemon Constants
"""Constants and enums for the Pokemon system."""

from funbot.pokemon.constants.enums import Currency, Pokeball, PokemonType, Region
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
    # Enums
    "Currency",
    "Pokeball",
    "PokemonType",
    "Region",
    # Constants
    "BASE_CATCH_RATE",
    "BASE_EXP_MODIFIER",
    "BATTLE_TICK_SECONDS",
    "EXP_SCALE_FACTOR",
    "ROUTE_HEALTH_BASE",
    "ROUTE_MONEY_BASE",
    "SHINY_CHANCE",
    # Type chart
    "TYPE_EFFECTIVENESS",
]
