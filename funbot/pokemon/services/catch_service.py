"""Catch service for calculating catch rates and auto-catching.

Based on Pokeclicker mechanics:
- Catch rate = (base_catch_rate^0.75) + pokeball_bonus
- Catch attempt is automatic after defeating enemy
- Ball used depends on player settings
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from funbot.pokemon.constants.enums import POKEBALL_BONUS, Pokeball
from funbot.pokemon.constants.game_constants import BASE_CATCH_RATE, SHINY_CHANCE


@dataclass
class CatchAttemptResult:
    """Result of a catch attempt."""

    success: bool
    pokeball_used: Pokeball
    catch_rate: float


class CatchService:
    """Service for catch calculations."""

    @staticmethod
    def calculate_catch_rate(base_catch_rate: int, pokeball: Pokeball) -> float:
        """Calculate actual catch rate.

        Formula: (base_catch_rate^0.75) + pokeball_bonus
        Result is clamped to 0-100.

        Args:
            base_catch_rate: Pokemon's base catch rate (0-255)
            pokeball: Pokeball being used

        Returns:
            Catch rate as percentage (0-100)
        """
        if pokeball == Pokeball.NONE:
            return 0.0

        if pokeball == Pokeball.MASTERBALL:
            return 100.0

        # Apply formula
        rate = pow(base_catch_rate, BASE_CATCH_RATE) + POKEBALL_BONUS[pokeball]

        # Clamp to 0-100
        return max(0.0, min(100.0, rate))

    @staticmethod
    def attempt_catch(base_catch_rate: int, pokeball: Pokeball) -> CatchAttemptResult:
        """Attempt to catch a Pokemon.

        Args:
            base_catch_rate: Pokemon's base catch rate
            pokeball: Pokeball to use

        Returns:
            CatchAttemptResult with success status
        """
        catch_rate = CatchService.calculate_catch_rate(base_catch_rate, pokeball)
        success = random.random() * 100 < catch_rate

        return CatchAttemptResult(success=success, pokeball_used=pokeball, catch_rate=catch_rate)

    @staticmethod
    def get_pokeball_for_pokemon(settings: dict, is_new: bool, is_shiny: bool) -> Pokeball:
        """Get which pokeball to use based on player settings.

        Settings keys:
        - new_shiny: Ball for new shiny Pokemon
        - new_pokemon: Ball for new (uncaught) Pokemon
        - caught_shiny: Ball for already caught shiny
        - caught_pokemon: Ball for already caught Pokemon

        Args:
            settings: Player's pokeball settings dict
            is_new: True if Pokemon not yet in party
            is_shiny: True if Pokemon is shiny

        Returns:
            Pokeball to use (NONE if should not attempt catch)
        """
        if is_new and is_shiny:
            return Pokeball(settings.get("new_shiny", Pokeball.ULTRABALL))
        if is_new:
            return Pokeball(settings.get("new_pokemon", Pokeball.POKEBALL))
        if is_shiny:
            return Pokeball(settings.get("caught_shiny", Pokeball.POKEBALL))
        return Pokeball(settings.get("caught_pokemon", Pokeball.NONE))

    @staticmethod
    def roll_shiny() -> bool:
        """Roll for shiny encounter.

        Returns:
            True if shiny (1/SHINY_CHANCE)
        """
        return random.randint(1, SHINY_CHANCE) == 1
