"""Dungeon service for dungeon operations.

Main service class for dungeon system, coordinating between
exploration, battle, and loot services.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from loguru import logger

from funbot.db.models.pokemon.dungeon_data import (
    DungeonData,
    PlayerDungeonProgress,
    PlayerDungeonRun,
)
from funbot.db.models.pokemon.player_wallet import PlayerWallet
from funbot.db.models.pokemon.route_requirement import RequirementType, RouteRequirement
from funbot.pokemon.services.battle_service import BattleService
from funbot.pokemon.services.dungeon_battle_service import DungeonRewards
from funbot.pokemon.services.dungeon_exploration_service import ExploreStepResult, MoveResult
from funbot.pokemon.services.dungeon_map import DungeonMap, DungeonMapGenerator

if TYPE_CHECKING:
    from funbot.pokemon.services.dungeon_battle_service import DungeonBattleResult
    from funbot.pokemon.services.dungeon_loot_service import LootItem


@dataclass
class DungeonInfo:
    """Information about a dungeon for display."""

    id: int
    name: str
    region: int
    token_cost: int
    base_health: int | None
    is_unlocked: bool
    unlock_hints: list[str]
    player_clears: int


@dataclass
class DungeonEntryResult:
    """Result of attempting to enter a dungeon."""

    success: bool
    reason: str | None = None
    run_id: int | None = None


@dataclass
class BossResult:
    """Result of a boss battle."""

    won: bool
    boss_name: str
    damage_dealt: int
    rewards: DungeonRewards


@dataclass
class DungeonExitResult:
    """Result of exiting a dungeon."""

    success: bool
    reason: str | None = None
    loot_preserved: list[dict] | None = None


class DungeonService:
    """Service for dungeon operations.

    Coordinates between exploration, battle, and loot services.
    Handles dungeon entry, availability checks, and run management.

    Requirements covered:
    - 1.1: Verify tokens and deduct entry cost
    - 1.2: Generate randomized map on entry
    - 1.5: Display unlock requirements for locked dungeons
    """

    # Default map size for dungeons
    DEFAULT_MAP_SIZE = 5

    # =========================================================================
    # Dungeon Availability Check (Task 10.1)
    # =========================================================================

    async def can_enter_dungeon(
        self, player_id: int, dungeon_id: int
    ) -> tuple[bool, str | None, list[str]]:
        """Check if a player can enter a dungeon.

        Checks:
        1. Dungeon exists
        2. Dungeon is unlocked for player
        3. Player has sufficient dungeon tokens
        4. Player doesn't have an active run in another dungeon

        Args:
            player_id: The player's user ID
            dungeon_id: The dungeon to check

        Returns:
            Tuple of (can_enter, reason_if_not, unlock_hints)
            - can_enter: True if player can enter
            - reason_if_not: Human-readable reason if cannot enter
            - unlock_hints: List of hints for unlocking (if locked)

        Requirements:
            - 1.1: Verify tokens
            - 1.5: Display unlock requirements
        """
        # Check dungeon exists
        dungeon = await DungeonData.filter(id=dungeon_id).first()
        if not dungeon:
            return False, "Dungeon not found", []

        # Check for active run in another dungeon
        active_run = await PlayerDungeonRun.filter(
            player_id=player_id, status="in_progress"
        ).first()
        if active_run:
            await active_run.fetch_related("dungeon")
            if active_run.dungeon.id != dungeon_id:
                return (
                    False,
                    f"You have an active run in {active_run.dungeon.name}. "
                    "Complete or abandon it first.",
                    [],
                )

        # Check if dungeon is unlocked
        is_unlocked, unlock_hints = await self._check_dungeon_unlocked(
            player_id, dungeon
        )
        if not is_unlocked:
            return False, "Dungeon is locked", unlock_hints

        # Check token balance
        wallet = await PlayerWallet.filter(user_id=player_id).first()
        if not wallet:
            return False, "No wallet found. Start your Pokemon journey first!", []

        token_cost = dungeon.token_cost or 0
        if wallet.dungeon_token < token_cost:
            return (
                False,
                f"Insufficient dungeon tokens. Need {token_cost:,}, have {wallet.dungeon_token:,}",
                [],
            )

        return True, None, []

    async def _check_dungeon_unlocked(
        self, player_id: int, dungeon: DungeonData
    ) -> tuple[bool, list[str]]:
        """Check if a dungeon is unlocked for a player.

        Args:
            player_id: The player's user ID
            dungeon: The dungeon to check

        Returns:
            Tuple of (is_unlocked, unlock_hints)
        """
        from funbot.pokemon.services.requirement_service import get_requirement_service

        # Get dungeon requirements (if any)
        # Dungeons use the same requirement system as routes
        requirements = await RouteRequirement.filter(
            parameters__contains={"dungeon": dungeon.name},
            requirement_type=RequirementType.DUNGEON_CLEAR,
        ).all()

        # If no requirements found, check if there's a direct requirement
        # For now, assume dungeons without explicit requirements are unlocked
        # based on region progression
        if not requirements:
            # Check if player has reached this region
            # For simplicity, assume first dungeon in each region is always available
            # More complex logic can be added later
            return True, []

        # Check each requirement
        requirement_service = get_requirement_service()
        unlock_hints = []

        for req in requirements:
            is_met = await requirement_service.check_requirement(player_id, req)
            if not is_met:
                hint = self._get_requirement_hint(req)
                if hint:
                    unlock_hints.append(hint)

        if unlock_hints:
            return False, unlock_hints

        return True, []

    def _get_requirement_hint(self, requirement: RouteRequirement) -> str | None:
        """Generate a human-readable hint for a requirement.

        Args:
            requirement: The requirement to describe

        Returns:
            Human-readable hint string

        Requirements:
            - 1.5: Display unlock requirement hints
            - 5.4: Show requirement hints for locked dungeons
        """
        params = requirement.parameters or {}
        req_type = RequirementType(requirement.requirement_type)

        match req_type:
            case RequirementType.GYM_BADGE:
                badge = params.get("badge", "Unknown")
                return f"Obtain the {badge} Badge"
            case RequirementType.DUNGEON_CLEAR:
                dungeon = params.get("dungeon", "Unknown")
                clears = params.get("clears", 1)
                if clears == 1:
                    return f"Clear {dungeon}"
                return f"Clear {dungeon} {clears} times"
            case RequirementType.TEMP_BATTLE:
                battle = params.get("battle", "Unknown")
                return f"Defeat {battle}"
            case RequirementType.QUEST_LINE_COMPLETED:
                quest = params.get("quest", "Unknown")
                return f"Complete the quest: {quest}"
            case RequirementType.ROUTE_KILL:
                route = params.get("route", "Unknown")
                amount = params.get("amount", 10)
                return f"Defeat {amount} Pokemon on Route {route}"
            case RequirementType.OBTAINED_POKEMON:
                pokemon = params.get("pokemon", "Unknown")
                return f"Obtain {pokemon}"
            case _:
                return None

    async def get_available_dungeons(
        self, player_id: int, region: int
    ) -> list[DungeonInfo]:
        """Get all dungeons in a region with their availability status.

        Args:
            player_id: The player's user ID
            region: The region number (0=Kanto, etc.)

        Returns:
            List of DungeonInfo with unlock status and hints

        Requirements:
            - 5.1: Display all dungeons with unlock status
            - 5.2: Show entry cost, region, clear count
        """
        dungeons = await DungeonData.filter(region=region).all()
        result = []

        for dungeon in dungeons:
            # Check unlock status
            is_unlocked, unlock_hints = await self._check_dungeon_unlocked(
                player_id, dungeon
            )

            # Get player's clear count
            progress = await PlayerDungeonProgress.filter(
                player_id=player_id, dungeon_id=dungeon.id
            ).first()
            player_clears = progress.clears if progress else 0

            result.append(
                DungeonInfo(
                    id=dungeon.id,
                    name=dungeon.name,
                    region=dungeon.region,
                    token_cost=dungeon.token_cost or 0,
                    base_health=dungeon.base_health,
                    is_unlocked=is_unlocked,
                    unlock_hints=unlock_hints,
                    player_clears=player_clears,
                )
            )

        return result

    async def get_dungeon_info(
        self, player_id: int, dungeon_id: int
    ) -> DungeonInfo | None:
        """Get detailed info about a specific dungeon.

        Args:
            player_id: The player's user ID
            dungeon_id: The dungeon ID

        Returns:
            DungeonInfo or None if not found
        """
        dungeon = await DungeonData.filter(id=dungeon_id).first()
        if not dungeon:
            return None

        is_unlocked, unlock_hints = await self._check_dungeon_unlocked(
            player_id, dungeon
        )

        progress = await PlayerDungeonProgress.filter(
            player_id=player_id, dungeon_id=dungeon.id
        ).first()
        player_clears = progress.clears if progress else 0

        return DungeonInfo(
            id=dungeon.id,
            name=dungeon.name,
            region=dungeon.region,
            token_cost=dungeon.token_cost or 0,
            base_health=dungeon.base_health,
            is_unlocked=is_unlocked,
            unlock_hints=unlock_hints,
            player_clears=player_clears,
        )

    # =========================================================================
    # Dungeon Entry (Task 10.3)
    # =========================================================================

    async def start_dungeon_run(
        self, player_id: int, dungeon_id: int
    ) -> DungeonEntryResult:
        """Start a new dungeon run.

        This method:
        1. Verifies entry requirements
        2. Deducts dungeon tokens
        3. Generates the dungeon map
        4. Creates a PlayerDungeonRun record

        Args:
            player_id: The player's user ID
            dungeon_id: The dungeon to enter

        Returns:
            DungeonEntryResult with success status and run ID

        Requirements:
            - 1.1: Verify tokens and deduct entry cost
            - 1.2: Generate randomized map on entry
        """
        # Check if player can enter
        can_enter, reason, _ = await self.can_enter_dungeon(player_id, dungeon_id)
        if not can_enter:
            return DungeonEntryResult(success=False, reason=reason)

        # Get dungeon data
        dungeon = await DungeonData.filter(id=dungeon_id).first()
        if not dungeon:
            return DungeonEntryResult(success=False, reason="Dungeon not found")

        # Check for existing active run in this dungeon (resume it)
        existing_run = await PlayerDungeonRun.filter(
            player_id=player_id, dungeon_id=dungeon_id, status="in_progress"
        ).first()
        if existing_run:
            return DungeonEntryResult(
                success=True,
                run_id=existing_run.id,
                reason="Resuming existing run",
            )

        # Deduct tokens
        wallet = await PlayerWallet.filter(user_id=player_id).first()
        if not wallet:
            return DungeonEntryResult(success=False, reason="No wallet found")

        token_cost = dungeon.token_cost or 0
        if token_cost > 0:
            await wallet.add_dungeon_token(-token_cost)
            logger.info(
                "Player {} paid {} tokens to enter dungeon {}",
                player_id,
                token_cost,
                dungeon.name,
            )

        # Generate map
        dungeon_map = DungeonMapGenerator.generate(
            size=self.DEFAULT_MAP_SIZE,
            floor=1,
            total_floors=1,  # Single floor for now
        )

        # Create run record
        run = await PlayerDungeonRun.create(
            player_id=player_id,
            dungeon_id=dungeon_id,
            map_data=dungeon_map.to_dict(),
            current_position={
                "x": dungeon_map.player_position[0],
                "y": dungeon_map.player_position[1],
                "floor": 1,
            },
            chests_opened=0,
            enemies_defeated=0,
            loot_collected=[],
            status="in_progress",
        )

        logger.info(
            "Player {} started dungeon run {} in {}",
            player_id,
            run.id,
            dungeon.name,
        )

        return DungeonEntryResult(success=True, run_id=run.id)

    async def get_active_run(self, player_id: int) -> PlayerDungeonRun | None:
        """Get the player's active dungeon run if any.

        Args:
            player_id: The player's user ID

        Returns:
            Active PlayerDungeonRun or None
        """
        return (
            await PlayerDungeonRun.filter(player_id=player_id, status="in_progress")
            .prefetch_related("dungeon")
            .first()
        )

    async def get_run_by_id(self, run_id: int) -> PlayerDungeonRun | None:
        """Get a dungeon run by ID.

        Args:
            run_id: The run ID

        Returns:
            PlayerDungeonRun or None
        """
        return (
            await PlayerDungeonRun.filter(id=run_id).prefetch_related("dungeon").first()
        )

    # =========================================================================
    # Exploration Step (Task 10.5)
    # =========================================================================

    async def explore_step(
        self, run_id: int, target_x: int, target_y: int
    ) -> ExploreStepResult:
        """Process one exploration step (movement + event handling).

        This method:
        1. Validates and executes movement
        2. Handles enemy encounters (battle + catch attempt)
        3. Handles chest opening (loot selection)
        4. Updates run state

        Args:
            run_id: The active run ID
            target_x: Target X coordinate
            target_y: Target Y coordinate

        Returns:
            ExploreStepResult with step outcome

        Requirements:
            - 1.3: Move to adjacent tile, reveal content
            - 1.4: Enemy tile triggers battle
            - 2.2: Award exp after defeating enemy
            - 2.3: Attempt catch after defeating wild Pokemon
            - 3.3: Chest triggers loot selection
            - 3.4: Track chest count
        """
        from funbot.pokemon.services.dungeon_exploration_service import (
            DungeonExplorationService,
            ExplorationStatus,
            TileEventType,
        )
        from funbot.pokemon.services.dungeon_map import DungeonMap

        # Get run
        run = await self.get_run_by_id(run_id)
        if not run:
            return ExploreStepResult(
                move_result=MoveResult.INVALID_POSITION,
                map_updated=False,
                can_continue=False,
            )

        # Deserialize map
        dungeon_map = DungeonMap.from_dict(run.map_data)

        # Execute exploration step
        dungeon_map, result = DungeonExplorationService.reveal_and_trigger_event(
            dungeon_map,
            target_x,
            target_y,
            ExplorationStatus.EXPLORING,
        )

        if not result.map_updated:
            return result

        # Handle tile events
        if result.tile_event:
            event_type = result.tile_event.event_type

            if event_type == TileEventType.BATTLE:
                # Handle enemy battle
                battle_result = await self._handle_enemy_battle(
                    run, dungeon_map, target_x, target_y
                )
                result.battle_result = battle_result

                # Clear the tile after battle
                dungeon_map = DungeonExplorationService.clear_tile(
                    dungeon_map, target_x, target_y
                )

                # Update enemies defeated count
                run.enemies_defeated += 1

            elif event_type == TileEventType.CHEST:
                # Handle chest opening
                chest_result = await self._handle_chest_opening(run)
                result.chest_result = chest_result

                # Clear the tile after opening
                dungeon_map = DungeonExplorationService.clear_tile(
                    dungeon_map, target_x, target_y
                )

                # Update chests opened count (Requirement 3.4)
                run.chests_opened += 1

        # Update run state
        run.map_data = dungeon_map.to_dict()
        run.current_position = {
            "x": dungeon_map.player_position[0],
            "y": dungeon_map.player_position[1],
            "floor": dungeon_map.floor,
        }
        await run.save()

        return result

    async def _handle_enemy_battle(
        self,
        run: PlayerDungeonRun,
        dungeon_map: DungeonMap,
        x: int,
        y: int,
    ) -> DungeonBattleResult:
        """Handle an enemy battle encounter.

        Args:
            run: The active dungeon run
            dungeon_map: Current map state
            x: Enemy tile X coordinate
            y: Enemy tile Y coordinate

        Returns:
            DungeonBattleResult with battle outcome
        """
        from funbot.pokemon.services.dungeon_battle_service import DungeonBattleService

        # Fetch related data
        await run.fetch_related("dungeon", "player")
        player_id = run.player.id
        dungeon_id = run.dungeon.id

        # Get player's party attack using centralized BattleService
        party_attack = await BattleService.get_player_party_attack(player_id)

        # Get dungeon base health
        base_health = run.dungeon.base_health or 1000

        # Calculate enemy health
        enemy_health = DungeonBattleService.calculate_enemy_health(
            base_health, run.chests_opened
        )

        # Get random enemy name from dungeon
        enemy_name = await self._get_random_enemy_name(dungeon_id)

        # Simulate battle
        battle_result = DungeonBattleService.simulate_battle(
            player_attack=party_attack,
            enemy_health=enemy_health,
            enemy_name=enemy_name,
            is_boss=False,
        )

        # Attempt catch for wild Pokemon (Requirement 2.3)
        if battle_result.defeated:
            catch_success = await self._attempt_catch(player_id, enemy_name)
            battle_result.catch_attempted = True
            battle_result.catch_success = catch_success

        return battle_result

    async def _handle_chest_opening(self, run: PlayerDungeonRun) -> LootItem | None:
        """Handle opening a chest.

        Args:
            run: The active dungeon run

        Returns:
            LootItem from the chest, or None if no loot available
        """
        from funbot.pokemon.services.dungeon_loot_service import DungeonLootService

        # Fetch related data
        await run.fetch_related("dungeon", "player")
        player_id = run.player.id
        dungeon_id = run.dungeon.id

        # Get player's highest region for debuff check
        player_region = await self._get_player_highest_region(player_id)

        # Get dungeon region
        dungeon_region = run.dungeon.region

        # Check if debuffed
        is_debuffed = DungeonLootService.is_dungeon_debuffed(
            dungeon_region, player_region
        )

        # Get player's clear count for this dungeon
        progress = await PlayerDungeonProgress.filter(
            player_id=player_id, dungeon_id=dungeon_id
        ).first()
        clears = progress.clears if progress else 0

        # Get loot tier weights
        weights = DungeonLootService.get_loot_tier_weights(clears, is_debuffed)

        # Select loot tier
        tier = DungeonLootService.select_loot_tier(weights)

        # Select loot item
        loot_item = await DungeonLootService.select_loot_item(dungeon_id, tier)

        if loot_item is None:
            return None

        # Add to collected loot
        loot_collected = run.loot_collected or []
        loot_collected.append(
            {
                "item_name": loot_item.item_name,
                "tier": loot_item.tier,
                "amount": loot_item.amount,
            }
        )
        run.loot_collected = loot_collected

        return loot_item

    async def _get_random_enemy_name(self, dungeon_id: int) -> str:
        """Get a random enemy Pokemon name from dungeon.

        Args:
            dungeon_id: The dungeon ID

        Returns:
            Random enemy Pokemon name
        """
        import random

        from funbot.db.models.pokemon.dungeon_data import DungeonPokemon

        enemies = await DungeonPokemon.filter(
            dungeon_id=dungeon_id, is_boss=False
        ).all()

        if not enemies:
            return "Unknown Pokemon"

        # Weighted random selection
        total_weight = sum(e.weight for e in enemies)
        if total_weight <= 0:
            return random.choice(enemies).pokemon_name

        roll = random.randint(1, total_weight)
        cumulative = 0
        for enemy in enemies:
            cumulative += enemy.weight
            if roll <= cumulative:
                return enemy.pokemon_name

        return enemies[0].pokemon_name

    async def _attempt_catch(self, player_id: int, pokemon_name: str) -> bool:
        """Attempt to catch a Pokemon after battle.

        Uses the same catch logic as route exploration:
        - Check pokeball settings
        - Use available pokeballs
        - Calculate catch rate based on Pokemon's catch_rate
        - Create PlayerPokemon record on success (if new)

        Args:
            player_id: The player's user ID
            pokemon_name: Name of the Pokemon to catch

        Returns:
            True if catch was successful
        """
        from funbot.db.models.pokemon import PlayerPokeballSettings, PlayerPokemon
        from funbot.db.models.pokemon.player_ball_inventory import PlayerBallInventory
        from funbot.db.models.pokemon.pokemon_data import PokemonData
        from funbot.pokemon.constants.enums import Pokeball
        from funbot.pokemon.constants.game_constants import SHINY_CHANCE_DUNGEON
        from funbot.pokemon.services.catch_service import CatchService

        # Get Pokemon data
        pokemon_data = await PokemonData.filter(name=pokemon_name).first()
        if not pokemon_data:
            logger.warning("Pokemon not found: {}", pokemon_name)
            return False

        # Check if player already owns this Pokemon
        existing = await PlayerPokemon.filter(
            user_id=player_id, pokemon_data_id=pokemon_data.id
        ).first()
        is_new = existing is None

        # Roll for shiny (dungeon has better shiny rate: 1/4096 vs 1/8192)
        is_shiny = CatchService.roll_shiny(SHINY_CHANCE_DUNGEON)

        # Get player's pokeball settings
        settings, _ = await PlayerPokeballSettings.get_or_create(user_id=player_id)

        # Determine which ball to use based on settings
        if is_new and is_shiny:
            preferred_ball = settings.new_shiny
        elif is_new:
            preferred_ball = settings.new_pokemon
        elif is_shiny:
            preferred_ball = settings.caught_shiny
        else:
            preferred_ball = settings.caught_pokemon

        if preferred_ball == Pokeball.NONE:
            # Player doesn't want to catch this type
            return False

        # Get ball inventory
        inventory, _ = await PlayerBallInventory.get_or_create(user_id=player_id)

        # Find available ball (fallback to lower tier)
        actual_ball = None
        for ball_type in [
            preferred_ball,
            Pokeball.ULTRABALL,
            Pokeball.GREATBALL,
            Pokeball.POKEBALL,
        ]:
            if ball_type <= preferred_ball and inventory.get_quantity(ball_type) > 0:
                actual_ball = ball_type
                break

        if actual_ball is None:
            # No balls available
            return False

        # Use the ball
        await inventory.use_ball(actual_ball)

        # Attempt catch using Pokemon's actual catch_rate
        catch_result = CatchService.attempt_catch(pokemon_data.catch_rate, actual_ball)

        if not catch_result.success:
            return False

        # Catch successful - create PlayerPokemon record if new
        if is_new:
            await PlayerPokemon.create(
                user_id=player_id,
                pokemon_data_id=pokemon_data.id,
                shiny=is_shiny,
            )
            logger.info(
                "Player {} caught new {} in dungeon (shiny={})",
                player_id,
                pokemon_name,
                is_shiny,
            )

        return True

    async def _get_player_highest_region(self, player_id: int) -> int:
        """Get the highest region the player has reached.

        Args:
            player_id: The player's user ID

        Returns:
            Highest region number (0=Kanto, etc.)
        """
        from funbot.db.models.pokemon.player_route_progress import PlayerRouteProgress

        # Get highest region from route progress
        progress = (
            await PlayerRouteProgress.filter(user_id=player_id)
            .order_by("-route__region")
            .first()
        )

        if progress:
            await progress.fetch_related("route")
            return progress.route.region

        return 0  # Default to Kanto

    # =========================================================================
    # Dungeon Completion Flow (Task 11)
    # =========================================================================

    async def fight_boss(self, run_id: int) -> BossResult:
        """Fight the dungeon boss.

        Args:
            run_id: The active run ID

        Returns:
            BossResult with battle outcome

        Requirements:
            - 4.1: Boss tile triggers boss battle
            - 4.2: Use predefined boss health
            - 4.3: Mark dungeon as cleared on victory
            - 4.5: Increment clear count
        """
        from funbot.pokemon.services.dungeon_battle_service import DungeonBattleService

        # Get run
        run = await self.get_run_by_id(run_id)
        if not run:
            return BossResult(
                won=False,
                boss_name="Unknown",
                damage_dealt=0,
                rewards=DungeonRewards(),
            )

        # Fetch related data
        await run.fetch_related("dungeon", "player")
        player_id = run.player.id
        dungeon_id = run.dungeon.id

        # Get player's party attack using centralized BattleService
        party_attack = await BattleService.get_player_party_attack(player_id)

        # Get boss stats
        boss_stats = await DungeonBattleService.get_boss_stats(dungeon_id)

        if not boss_stats:
            # No boss found, use default
            boss_stats = {
                "name": "Unknown Boss",
                "health": run.dungeon.base_health or 10000,
                "level": 50,
            }

        # Simulate boss battle
        battle_result = DungeonBattleService.simulate_boss_battle(
            player_attack=party_attack,
            boss_health=boss_stats["health"],
            boss_name=boss_stats["name"],
            boss_level=boss_stats["level"],
            chests_opened=run.chests_opened,
        )

        if battle_result.defeated:
            # Complete the dungeon
            rewards = await self._complete_dungeon_run(run)

            return BossResult(
                won=True,
                boss_name=boss_stats["name"],
                damage_dealt=battle_result.damage_dealt,
                rewards=rewards,
            )

        return BossResult(
            won=False,
            boss_name=boss_stats["name"],
            damage_dealt=battle_result.damage_dealt,
            rewards=DungeonRewards(),
        )

    async def _complete_dungeon_run(self, run: PlayerDungeonRun) -> DungeonRewards:
        """Complete a dungeon run and calculate rewards.

        Args:
            run: The dungeon run to complete

        Returns:
            DungeonRewards with all rewards

        Requirements:
            - 4.3: Mark dungeon as cleared
            - 4.4: Award first-clear bonus
            - 4.5: Increment clear count
        """
        from funbot.pokemon.services.dungeon_battle_service import DungeonBattleService

        await run.fetch_related("dungeon", "player")
        player_id = run.player.id
        dungeon_id = run.dungeon.id

        # Check if this is first clear (Requirement 4.4)
        progress = await PlayerDungeonProgress.filter(
            player_id=player_id, dungeon_id=dungeon_id
        ).first()

        is_first_clear = progress is None or progress.clears == 0

        # Calculate rewards
        # Use a default difficulty route based on region
        difficulty_route = (run.dungeon.region + 1) * 5
        rewards = DungeonBattleService.calculate_completion_rewards(
            dungeon_difficulty_route=difficulty_route,
            dungeon_region=run.dungeon.region,
            enemies_defeated=run.enemies_defeated,
            chests_opened=run.chests_opened,
            is_first_clear=is_first_clear,
        )

        # Update or create progress (Requirement 4.5)
        if progress:
            progress.clears += 1
            progress.last_cleared = datetime.now(UTC)
            await progress.save()
        else:
            await PlayerDungeonProgress.create(
                player_id=player_id,
                dungeon_id=dungeon_id,
                clears=1,
                last_cleared=datetime.now(UTC),
            )

        # Mark run as completed (Requirement 4.3)
        run.status = "completed"
        await run.save()

        # Award rewards to player
        await self._award_rewards(player_id, rewards)

        logger.info(
            "Player {} completed dungeon {} (first_clear={})",
            player_id,
            run.dungeon.name,
            is_first_clear,
        )

        return rewards

    async def _award_rewards(self, player_id: int, rewards: DungeonRewards) -> None:
        """Award dungeon rewards to player.

        Args:
            player_id: The player's user ID
            rewards: Rewards to award
        """
        wallet = await PlayerWallet.filter(user_id=player_id).first()
        if not wallet:
            return

        # Award money
        if rewards.money > 0:
            await wallet.add_pokedollar(rewards.money)

        # Award dungeon tokens
        if rewards.dungeon_tokens > 0:
            await wallet.add_dungeon_token(rewards.dungeon_tokens)

        # Award first clear bonus
        if rewards.first_clear_bonus:
            bonus_tokens = rewards.first_clear_bonus.get("bonus_tokens", 0)
            bonus_money = rewards.first_clear_bonus.get("bonus_money", 0)
            if bonus_tokens > 0:
                await wallet.add_dungeon_token(bonus_tokens)
            if bonus_money > 0:
                await wallet.add_pokedollar(bonus_money)

    # =========================================================================
    # Early Exit Handling (Task 11.5)
    # =========================================================================

    async def exit_dungeon(self, run_id: int) -> DungeonExitResult:
        """Exit a dungeon early.

        This method:
        1. Checks if player is at entrance
        2. Preserves collected loot
        3. Does NOT increment clear count
        4. Does NOT refund tokens

        Args:
            run_id: The active run ID

        Returns:
            DungeonExitResult with exit outcome

        Requirements:
            - 8.1: Exit only at entrance tile
            - 8.2: Preserve collected loot
            - 8.3: Do not count as clear
            - 8.4: Do not refund tokens
            - 8.5: Cannot exit while in battle
        """
        from funbot.pokemon.services.dungeon_exploration_service import (
            DungeonExplorationService,
            ExplorationStatus,
        )

        # Get run
        run = await self.get_run_by_id(run_id)
        if not run:
            return DungeonExitResult(
                success=False,
                reason="Run not found",
                loot_preserved=[],
            )

        # Deserialize map
        dungeon_map = DungeonMap.from_dict(run.map_data)

        # Check if can exit (Requirement 8.1, 8.5)
        can_exit, reason = DungeonExplorationService.can_exit(
            dungeon_map, ExplorationStatus.EXPLORING
        )

        if not can_exit:
            return DungeonExitResult(
                success=False,
                reason=reason,
                loot_preserved=[],
            )

        # Fetch related data
        await run.fetch_related("dungeon", "player")
        player_id = run.player.id

        # Preserve collected loot (Requirement 8.2)
        loot_preserved = run.loot_collected or []

        # Award preserved loot to player
        await self._award_loot(player_id, loot_preserved)

        # Mark run as abandoned (Requirement 8.3 - no clear count)
        run.status = "abandoned"
        await run.save()

        logger.info(
            "Player {} exited dungeon {} early with {} items",
            player_id,
            run.dungeon.name,
            len(loot_preserved),
        )

        # Note: No token refund (Requirement 8.4)

        return DungeonExitResult(
            success=True,
            reason=None,
            loot_preserved=loot_preserved,
        )

    async def _award_loot(self, player_id: int, loot_items: list[dict]) -> None:
        """Award collected loot items to player.

        Args:
            player_id: The player's user ID
            loot_items: List of loot item dicts
        """
        # In full implementation, this would add items to player inventory
        # For now, just log the loot
        for item in loot_items:
            logger.debug(
                "Player {} received loot: {} ({})",
                player_id,
                item.get("item_name"),
                item.get("tier"),
            )

    async def abandon_run(self, run_id: int) -> bool:
        """Abandon a dungeon run without preserving loot.

        Used when player wants to completely abandon a run.

        Args:
            run_id: The run ID to abandon

        Returns:
            True if successfully abandoned
        """
        run = await self.get_run_by_id(run_id)
        if not run:
            return False

        run.status = "abandoned"
        await run.save()

        await run.fetch_related("dungeon", "player")
        logger.info(
            "Player {} abandoned dungeon run in {}",
            run.player.id,
            run.dungeon.name,
        )

        return True
