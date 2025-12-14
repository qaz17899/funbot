"""Battle service for calculating damage and simulating encounters.

Based on Pokeclicker mechanics:
- All party Pokemon attack simultaneously
- Damage = sum of all Pokemon attacks with type effectiveness
- Enemy defeated when health <= 0
"""

from __future__ import annotations

import random

from funbot.pokemon.constants.enums import PokemonType
from funbot.pokemon.constants.game_constants import (
    ROUTE_HEALTH_BASE,
    ROUTE_HEALTH_MIN,
    ROUTE_MONEY_BASE,
)
from funbot.pokemon.constants.type_chart import get_attack_modifier
from funbot.pokemon.schemas import BattleResult, ExploreResult

# Re-export for backward compatibility during transition
__all__ = ["BattleResult", "BattleService", "ExploreResult"]


class BattleService:
    """Service for battle calculations."""

    @staticmethod
    def calculate_route_health(route: int, region: int) -> int:
        """Calculate enemy Pokemon health for a route.

        Formula from Pokeclicker:
        health = max(20, (100 * route^2.2 / 12)^1.15 * (1 + region/20))

        Args:
            route: Route number
            region: Region index (0=Kanto, 1=Johto, etc.)

        Returns:
            Enemy max health
        """
        normalized_route = route  # TODO: normalize route based on region
        # Issue URL: https://github.com/qaz17899/funbot/issues/17
        health = int(
            ROUTE_HEALTH_BASE * pow(pow(normalized_route, 2.2) / 12, 1.15) * (1 + region / 20)
        )
        return max(ROUTE_HEALTH_MIN, health)

    @staticmethod
    def calculate_route_money(route: int, region: int, use_deviation: bool = True) -> int:
        """Calculate money earned from defeating a Pokemon on route.

        Formula (Pokeclicker exact): 3 * route + 5 * route^1.15 + random(-25, 25)

        Args:
            route: Route number
            region: Region index
            use_deviation: If True, add ±25 random deviation (Pokeclicker default)

        Returns:
            Money earned
        """
        deviation = random.randint(-25, 25) if use_deviation else 12  # 12 = mean
        money = int(ROUTE_MONEY_BASE * route + 5 * pow(route, 1.15) + deviation)
        return max(10, money)

    @staticmethod
    def calculate_dungeon_tokens(route: int, region: int) -> int:
        """Calculate dungeon tokens earned from route.

        Formula (Pokeclicker exact): max(1, 6 * pow(route * 2 / (2.8 / (1 + region / 3)), 1.08))

        Args:
            route: Normalized route number
            region: Region index

        Returns:
            Dungeon tokens earned
        """
        tokens = 6 * pow(route * 2 / (2.8 / (1 + region / 3)), 1.08)
        return max(1, int(tokens))

    @staticmethod
    def calculate_party_attack(
        party_pokemon: list[dict],
        enemy_type1: PokemonType,
        enemy_type2: PokemonType = PokemonType.NONE,
    ) -> int:
        """Calculate total party attack against an enemy.

        Sums all party Pokemon attacks with type effectiveness.

        Args:
            party_pokemon: List of party Pokemon dicts with:
                - attack: int
                - type1: PokemonType
                - type2: PokemonType
            enemy_type1: Enemy's primary type
            enemy_type2: Enemy's secondary type

        Returns:
            Total party attack damage
        """
        total_attack = 0

        for pokemon in party_pokemon:
            base_attack = pokemon.get("attack", 0)
            poke_type1 = pokemon.get("type1", PokemonType.NORMAL)
            poke_type2 = pokemon.get("type2", PokemonType.NONE)

            # Calculate type effectiveness
            modifier = get_attack_modifier(poke_type1, poke_type2, enemy_type1, enemy_type2)

            # Add modified attack to total
            total_attack += int(base_attack * modifier)

        return total_attack

    @staticmethod
    def calculate_ticks_to_defeat(enemy_health: int, party_attack: int) -> int:
        """Calculate how many ticks to defeat enemy.

        Args:
            enemy_health: Enemy's max health
            party_attack: Total party attack per tick

        Returns:
            Number of ticks (rounds up if not exact)
        """
        if party_attack <= 0:
            return 999999  # Can't defeat
        return max(1, (enemy_health + party_attack - 1) // party_attack)

    @staticmethod
    def can_defeat_enemy(enemy_health: int, party_attack: int, max_ticks: int = 100) -> bool:
        """Check if party can defeat enemy within tick limit.

        Args:
            enemy_health: Enemy's max health
            party_attack: Total party attack per tick
            max_ticks: Maximum allowed ticks

        Returns:
            True if enemy can be defeated
        """
        ticks = BattleService.calculate_ticks_to_defeat(enemy_health, party_attack)
        return ticks <= max_ticks
