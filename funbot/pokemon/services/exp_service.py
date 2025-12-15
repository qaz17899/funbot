"""Experience service for distributing EXP and handling level ups.

Based on Pokeclicker mechanics:
- All party Pokemon gain EXP from battles
- Level up uses medium-slow curve
- Max level is 100
"""

from __future__ import annotations

from dataclasses import dataclass

from funbot.pokemon.constants.game_constants import EXP_SCALE_FACTOR, MAX_LEVEL


@dataclass
class LevelUpResult:
    """Result of a level up check."""

    leveled_up: bool
    new_level: int
    exp_remaining: int


class ExpService:
    """Service for experience calculations."""

    @staticmethod
    def calculate_exp_to_level(level: int) -> int:
        """Calculate EXP required to reach a level.

        Uses medium-slow curve: exp = factor * level^3

        Args:
            level: Target level (1-100)

        Returns:
            Total EXP required
        """
        if level <= 1:
            return 0
        return int(EXP_SCALE_FACTOR * pow(level, 3))

    @staticmethod
    def calculate_exp_for_next_level(current_level: int) -> int:
        """Calculate EXP needed to go from current level to next.

        Args:
            current_level: Current level

        Returns:
            EXP needed for next level
        """
        if current_level >= MAX_LEVEL:
            return 0
        return ExpService.calculate_exp_to_level(
            current_level + 1
        ) - ExpService.calculate_exp_to_level(current_level)

    @staticmethod
    def calculate_battle_exp(
        base_exp: int, enemy_level: int, trainer: bool = False
    ) -> int:
        """Calculate EXP earned from defeating an enemy (Pokeclicker exact formula).

        From Party.ts:138-143:
        expTotal = Math.floor(exp * level * trainerBonus * multBonus / 9)

        In Pokeclicker, ALL party Pokemon receive the FULL exp amount.
        This is different from mainline Pokemon games where exp is split.

        Args:
            base_exp: Enemy Pokemon's base exp yield (from PokemonData.base_exp)
            enemy_level: Enemy Pokemon's level
            trainer: If True, apply 1.5x trainer bonus

        Returns:
            EXP earned (each party Pokemon gets this full amount)
        """
        trainer_bonus = 1.5 if trainer else 1.0
        mult_bonus = 1.0  # TODO: Add multiplier system if needed

        exp = int(base_exp * enemy_level * trainer_bonus * mult_bonus / 9)
        return max(1, exp)

    @staticmethod
    def add_exp_and_level_up(
        current_level: int, current_exp: int, exp_gained: int
    ) -> LevelUpResult:
        """Add EXP to a Pokemon and check for level ups.

        Args:
            current_level: Pokemon's current level
            current_exp: Pokemon's current EXP
            exp_gained: EXP to add

        Returns:
            LevelUpResult with new level and remaining exp
        """
        if current_level >= MAX_LEVEL:
            return LevelUpResult(leveled_up=False, new_level=MAX_LEVEL, exp_remaining=0)

        new_exp = current_exp + exp_gained
        new_level = current_level
        leveled_up = False

        # Check for level ups
        while new_level < MAX_LEVEL:
            exp_needed = ExpService.calculate_exp_for_next_level(new_level)
            if new_exp >= exp_needed:
                new_exp -= exp_needed
                new_level += 1
                leveled_up = True
            else:
                break

        # Cap at max level
        if new_level >= MAX_LEVEL:
            new_level = MAX_LEVEL
            new_exp = 0

        return LevelUpResult(
            leveled_up=leveled_up, new_level=new_level, exp_remaining=new_exp
        )

    @staticmethod
    def calculate_attack_from_level(base_attack: int, level: int) -> int:
        """Calculate Pokemon's attack stat based on level.

        Simple linear scaling: attack = base * (1 + (level-1) * 0.02)
        At level 100, attack is ~3x base.

        Args:
            base_attack: Pokemon's base attack stat
            level: Current level

        Returns:
            Calculated attack stat
        """
        multiplier = 1 + (level - 1) * 0.02
        return int(base_attack * multiplier)
