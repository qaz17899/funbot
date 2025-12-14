"""Pokemon system dataclasses and result types.

Centralized location for all structured data types used across
the Pokemon module. This eliminates scattered dataclass definitions
and provides a single source of truth for result/request types.
"""

from __future__ import annotations

from dataclasses import dataclass

# =============================================================================
# Battle Results
# =============================================================================


@dataclass
class BattleResult:
    """Result of a single battle encounter."""

    pokemon_name: str
    pokemon_id: int
    defeated: bool
    damage_dealt: int
    ticks_to_defeat: int
    money_earned: int
    exp_earned: int
    is_shiny: bool


@dataclass
class ExploreResult:
    """Result of exploring a route (multiple encounters)."""

    route: int
    region: int
    encounter_count: int
    pokemon_defeated: int
    pokemon_caught: int
    shiny_count: int
    total_money: int
    total_exp: int
    caught_pokemon: list[tuple[str, int, bool]]  # (name, id, is_shiny)


# =============================================================================
# Catch Results
# =============================================================================


@dataclass
class CatchAttemptResult:
    """Result of a catch attempt."""

    success: bool
    pokeball_used: int  # Pokeball enum value
    catch_rate: float


# =============================================================================
# Experience Results
# =============================================================================


@dataclass
class LevelUpResult:
    """Result of a level up check."""

    leveled_up: bool
    new_level: int
    exp_remaining: int
