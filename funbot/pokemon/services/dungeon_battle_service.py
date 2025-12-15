"""Dungeon battle service for battle calculations and simulation.

Handles enemy health calculation, battle simulation, boss battles, and rewards.
Matches PokeClicker's dungeon battle mechanics from DungeonBattle.ts and PokemonFactory.ts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

from funbot.pokemon.services.battle_service import BattleService


class DungeonBattleStatus(Enum):
    """Status of a dungeon battle."""

    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"


@dataclass
class DungeonBattleResult:
    """Result of a dungeon battle encounter."""

    pokemon_name: str
    defeated: bool
    damage_dealt: int
    ticks_to_defeat: int
    exp_earned: int
    money_earned: int
    is_shiny: bool = False
    is_boss: bool = False
    catch_attempted: bool = False
    catch_success: bool = False


@dataclass
class TrainerBattleState:
    """State of a trainer battle with multiple Pokemon."""

    trainer_class: str
    trainer_name: str | None
    pokemon_list: list[dict]  # List of {name, health, level, max_health}
    current_pokemon_index: int = 0
    is_boss: bool = False

    @property
    def current_pokemon(self) -> dict | None:
        """Get the current Pokemon being battled."""
        if 0 <= self.current_pokemon_index < len(self.pokemon_list):
            return self.pokemon_list[self.current_pokemon_index]
        return None

    @property
    def all_defeated(self) -> bool:
        """Check if all trainer Pokemon are defeated."""
        return self.current_pokemon_index >= len(self.pokemon_list)


@dataclass
class DungeonRewards:
    """Rewards from completing a dungeon."""

    money: int = 0
    exp: int = 0
    dungeon_tokens: int = 0
    first_clear_bonus: dict | None = None
    pokemon_caught: list[str] = field(default_factory=list)


# EP modifiers from GameConstants.ts
DUNGEON_EP_MODIFIER = 3
DUNGEON_BOSS_EP_MODIFIER = 10
BASE_EP_YIELD = 100


class DungeonBattleService:
    """Service for dungeon battle calculations.

    Matches PokeClicker's dungeon battle mechanics:
    - Enemy health calculation (PokemonFactory.ts:149-172)
    - Boss health calculation (PokemonFactory.ts:192-214)
    - Trainer battle sequential processing (DungeonBattle.ts:238-244)
    - Battle simulation with tick-based damage
    """

    # =========================================================================
    # Enemy Health Calculation (Task 5.1)
    # =========================================================================

    @staticmethod
    def calculate_enemy_health(base_health: int, chests_opened: int) -> int:
        """Calculate enemy Pokemon health in a dungeon.

        Matches PokeClicker's PokemonFactory.generateDungeonPokemon():
        maxHealth = floor(baseHealth * (1 + (chestsOpened / 5)))

        The formula increases enemy health based on chests opened:
        - 0 chests: 100% base health
        - 5 chests: 200% base health
        - 10 chests: 300% base health

        Args:
            base_health: The dungeon's base health value
            chests_opened: Number of chests opened in current run

        Returns:
            Calculated enemy health (minimum 1)
        """
        if base_health <= 0:
            return 1

        # PokeClicker formula: baseHealth * (1 + (chestsOpened / 5))
        health = math.floor(base_health * (1 + (chests_opened / 5)))
        return max(1, health)

    @staticmethod
    def calculate_trainer_pokemon_health(
        base_health: int,
        chests_opened: int,
        is_boss: bool,
        team_size: int,
    ) -> int:
        """Calculate trainer Pokemon health in a dungeon.

        Matches PokeClicker's PokemonFactory.generateDungeonTrainerPokemon():
        maxHealth = floor(baseHealth * (1 + (chestsOpened / 5)) / (isBoss ? 1 : trainerPokemon ** 0.75))

        Non-boss trainer Pokemon have reduced health based on team size.

        Args:
            base_health: The dungeon's base health value
            chests_opened: Number of chests opened in current run
            is_boss: Whether this is a boss trainer
            team_size: Number of Pokemon in the trainer's team

        Returns:
            Calculated Pokemon health (minimum 1)
        """
        if base_health <= 0:
            return 1

        # Base calculation with chest bonus
        health = base_health * (1 + (chests_opened / 5))

        # Non-boss trainers have health divided by team_size^0.75
        if not is_boss and team_size > 1:
            health /= team_size**0.75

        return max(1, math.floor(health))

    # =========================================================================
    # Battle Simulation (Task 5.3)
    # =========================================================================

    # Delegate to BattleService for consistency (SSOT)
    calculate_damage_per_tick = staticmethod(BattleService.calculate_damage_per_tick)
    calculate_ticks_to_defeat = staticmethod(BattleService.calculate_ticks_to_defeat)

    @staticmethod
    def simulate_battle(
        player_attack: int,
        enemy_health: int,
        enemy_name: str = "Unknown",
        is_boss: bool = False,
    ) -> DungeonBattleResult:
        """Simulate a complete battle to defeat an enemy.

        Calculates the number of ticks needed and rewards earned.

        Args:
            player_attack: Total party attack power
            enemy_health: Enemy's total health
            enemy_name: Name of the enemy Pokemon
            is_boss: Whether this is a boss encounter

        Returns:
            DungeonBattleResult with battle outcome
        """
        ticks = BattleService.calculate_ticks_to_defeat(enemy_health, player_attack)
        damage_dealt = enemy_health  # Total damage = enemy health when defeated

        # Calculate experience earned
        # EP modifier is higher for bosses
        ep_modifier = DUNGEON_BOSS_EP_MODIFIER if is_boss else DUNGEON_EP_MODIFIER
        exp_earned = BASE_EP_YIELD * ep_modifier

        return DungeonBattleResult(
            pokemon_name=enemy_name,
            defeated=True,  # Battle always completes (Requirement 2.5)
            damage_dealt=damage_dealt,
            ticks_to_defeat=ticks,
            exp_earned=exp_earned,
            money_earned=0,  # Money is calculated separately
            is_boss=is_boss,
        )

    @staticmethod
    def can_defeat_in_time(
        enemy_health: int,
        party_attack: int,
        max_ticks: int = 100,
    ) -> bool:
        """Check if party can defeat enemy within tick limit.

        Args:
            enemy_health: Enemy's total health
            party_attack: Total party attack per tick
            max_ticks: Maximum allowed ticks

        Returns:
            True if enemy can be defeated in time
        """
        ticks = BattleService.calculate_ticks_to_defeat(enemy_health, party_attack)
        return ticks <= max_ticks

    # =========================================================================
    # Boss Battle Logic (Task 5.5)
    # =========================================================================

    @staticmethod
    def calculate_boss_health(boss_base_health: int, chests_opened: int) -> int:
        """Calculate boss Pokemon health.

        Matches PokeClicker's PokemonFactory.generateDungeonBoss():
        maxHealth = floor(bossPokemon.baseHealth * (1 + (chestsOpened / 5)))

        Boss Pokemon use their predefined baseHealth from DungeonBossPokemon,
        not the dungeon's base health.

        Args:
            boss_base_health: The boss's predefined base health
            chests_opened: Number of chests opened in current run

        Returns:
            Calculated boss health (minimum 1)
        """
        if boss_base_health <= 0:
            return 1

        # Same formula as regular enemies but uses boss's own base health
        health = math.floor(boss_base_health * (1 + (chests_opened / 5)))
        return max(1, health)

    @staticmethod
    async def get_boss_stats(
        dungeon_id: int,
        boss_name: str | None = None,
    ) -> dict | None:
        """Get boss Pokemon stats from database.

        Retrieves predefined boss health and level from DungeonPokemon.

        Args:
            dungeon_id: The dungeon's database ID
            boss_name: Optional specific boss name to find

        Returns:
            Dict with boss stats or None if not found
        """
        from funbot.db.models.pokemon.dungeon_data import DungeonPokemon

        query = DungeonPokemon.filter(dungeon_id=dungeon_id, is_boss=True)
        if boss_name:
            query = query.filter(pokemon_name=boss_name)

        boss = await query.first()
        if not boss:
            return None

        return {
            "name": boss.pokemon_name,
            "health": boss.health,
            "level": boss.level,
            "is_boss": True,
        }

    @staticmethod
    async def get_boss_trainer_stats(
        dungeon_id: int,
        trainer_name: str | None = None,
    ) -> TrainerBattleState | None:
        """Get boss trainer stats from database.

        Retrieves trainer and their Pokemon team for boss trainer battles.

        Args:
            dungeon_id: The dungeon's database ID
            trainer_name: Optional specific trainer name to find

        Returns:
            TrainerBattleState or None if not found
        """
        from funbot.db.models.pokemon.dungeon_data import DungeonTrainer

        query = DungeonTrainer.filter(dungeon_id=dungeon_id, is_boss=True)
        if trainer_name:
            query = query.filter(trainer_name=trainer_name)

        trainer = await query.prefetch_related("pokemon").first()
        if not trainer:
            return None

        # Get Pokemon ordered by their position
        pokemon_list = [
            {
                "name": poke.pokemon_name,
                "health": poke.health,
                "max_health": poke.health,
                "level": poke.level,
            }
            for poke in sorted(trainer.pokemon, key=lambda p: p.order)
        ]

        return TrainerBattleState(
            trainer_class=trainer.trainer_class,
            trainer_name=trainer.trainer_name,
            pokemon_list=pokemon_list,
            is_boss=True,
        )

    @staticmethod
    def simulate_boss_battle(
        player_attack: int,
        boss_health: int,
        boss_name: str,
        boss_level: int,
        chests_opened: int = 0,
    ) -> DungeonBattleResult:
        """Simulate a boss battle.

        Uses predefined boss health from dungeon data.

        Args:
            player_attack: Total party attack power
            boss_health: Boss's predefined base health
            boss_name: Name of the boss Pokemon
            boss_level: Boss's level
            chests_opened: Number of chests opened (for health scaling)

        Returns:
            DungeonBattleResult with battle outcome
        """
        # Calculate actual boss health with chest bonus
        actual_health = DungeonBattleService.calculate_boss_health(
            boss_health, chests_opened
        )

        return DungeonBattleService.simulate_battle(
            player_attack=player_attack,
            enemy_health=actual_health,
            enemy_name=boss_name,
            is_boss=True,
        )

    @staticmethod
    def simulate_trainer_battle(
        player_attack: int,
        trainer_state: TrainerBattleState,
        dungeon_base_health: int,
        chests_opened: int = 0,
    ) -> list[DungeonBattleResult]:
        """Simulate a trainer battle with sequential Pokemon.

        Processes trainer Pokemon in order (Requirement 2.4).
        Each Pokemon must be defeated before the next is engaged.

        Args:
            player_attack: Total party attack power
            trainer_state: Current trainer battle state
            dungeon_base_health: Dungeon's base health for non-boss trainers
            chests_opened: Number of chests opened

        Returns:
            List of DungeonBattleResult for each Pokemon defeated
        """
        results = []
        team_size = len(trainer_state.pokemon_list)

        for pokemon in trainer_state.pokemon_list:
            # Use predefined health for boss trainers, calculate for non-boss
            if trainer_state.is_boss:
                health = DungeonBattleService.calculate_boss_health(
                    pokemon["health"], chests_opened
                )
            else:
                health = DungeonBattleService.calculate_trainer_pokemon_health(
                    dungeon_base_health,
                    chests_opened,
                    is_boss=False,
                    team_size=team_size,
                )

            result = DungeonBattleService.simulate_battle(
                player_attack=player_attack,
                enemy_health=health,
                enemy_name=pokemon["name"],
                is_boss=trainer_state.is_boss,
            )
            results.append(result)

        return results

    # =========================================================================
    # Reward Calculation (Task 5.7)
    # =========================================================================

    @staticmethod
    def calculate_dungeon_level(difficulty_route: int, region: int) -> int:
        """Calculate dungeon level based on difficulty route.

        Matches PokeClicker's PokemonFactory.routeLevel():
        level = floor(20 * route^(1/2.25))

        Args:
            difficulty_route: The dungeon's difficulty route value
            region: Region index (0=Kanto, 1=Johto, etc.)

        Returns:
            Calculated level
        """
        # Normalize route (simplified - in full implementation would use MapHelper)
        normalized_route = difficulty_route
        level = math.floor(20 * pow(normalized_route, 1 / 2.25))
        return max(1, level)

    @staticmethod
    def calculate_money_reward(difficulty_route: int, region: int) -> int:
        """Calculate money reward based on difficulty route.

        Matches PokeClicker's PokemonFactory.routeMoney():
        money = max(10, 3 * route + 5 * route^1.15 + deviation)

        Uses mean deviation (12) for consistent rewards.

        Args:
            difficulty_route: The dungeon's difficulty route value
            region: Region index

        Returns:
            Money reward amount
        """
        route = difficulty_route
        # Use mean deviation (12) for consistency
        deviation = 12
        money = 3 * route + 5 * pow(route, 1.15) + deviation
        return max(10, int(money))

    @staticmethod
    def calculate_dungeon_token_reward(difficulty_route: int, region: int) -> int:
        """Calculate dungeon token reward.

        Matches PokeClicker's PokemonFactory.routeDungeonTokens():
        tokens = max(1, 6 * (route * 2 / (2.8 / (1 + region / 3)))^1.08)

        Args:
            difficulty_route: The dungeon's difficulty route value
            region: Region index

        Returns:
            Dungeon token reward amount
        """
        route = difficulty_route
        tokens = 6 * pow(route * 2 / (2.8 / (1 + region / 3)), 1.08)
        return max(1, int(tokens))

    @staticmethod
    def calculate_exp_reward(
        enemies_defeated: int,
        is_boss_defeated: bool = False,
    ) -> int:
        """Calculate total experience reward for a dungeon run.

        Args:
            enemies_defeated: Number of regular enemies defeated
            is_boss_defeated: Whether the boss was defeated

        Returns:
            Total experience points earned
        """
        # Regular enemies give base EP * dungeon modifier
        regular_exp = enemies_defeated * BASE_EP_YIELD * DUNGEON_EP_MODIFIER

        # Boss gives base EP * boss modifier
        boss_exp = BASE_EP_YIELD * DUNGEON_BOSS_EP_MODIFIER if is_boss_defeated else 0

        return regular_exp + boss_exp

    @staticmethod
    def calculate_completion_rewards(
        dungeon_difficulty_route: int,
        dungeon_region: int,
        enemies_defeated: int,
        chests_opened: int,
        is_first_clear: bool = False,
    ) -> DungeonRewards:
        """Calculate all rewards for completing a dungeon.

        Scales rewards based on dungeon difficulty route (Requirement 7.2).

        Args:
            dungeon_difficulty_route: The dungeon's difficulty route value
            dungeon_region: Region the dungeon is in
            enemies_defeated: Number of enemies defeated
            chests_opened: Number of chests opened
            is_first_clear: Whether this is the player's first clear

        Returns:
            DungeonRewards with all calculated rewards
        """
        # Calculate base rewards scaled by difficulty
        money = DungeonBattleService.calculate_money_reward(
            dungeon_difficulty_route, dungeon_region
        )
        # Scale money by enemies defeated
        total_money = money * enemies_defeated

        # Calculate experience
        exp = DungeonBattleService.calculate_exp_reward(
            enemies_defeated, is_boss_defeated=True
        )

        # Calculate dungeon tokens earned
        tokens = DungeonBattleService.calculate_dungeon_token_reward(
            dungeon_difficulty_route, dungeon_region
        )

        # First clear bonus (if applicable)
        first_clear_bonus = None
        if is_first_clear:
            # First clear gives bonus tokens and money
            first_clear_bonus = {
                "bonus_tokens": tokens * 5,  # 5x tokens for first clear
                "bonus_money": total_money * 2,  # 2x money for first clear
            }

        return DungeonRewards(
            money=total_money,
            exp=exp,
            dungeon_tokens=tokens,
            first_clear_bonus=first_clear_bonus,
        )
