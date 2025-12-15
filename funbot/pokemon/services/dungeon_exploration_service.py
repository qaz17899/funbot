"""Dungeon exploration service for movement and tile interactions.

Handles player movement validation, tile reveal, and event triggering
during dungeon exploration.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from funbot.pokemon.services.dungeon_map import DungeonMap, DungeonTile, TileType

if TYPE_CHECKING:
    from funbot.pokemon.services.dungeon_battle_service import DungeonBattleResult
    from funbot.pokemon.services.dungeon_loot_service import LootItem


class ExplorationStatus(StrEnum):
    """Status of the exploration session."""

    EXPLORING = "exploring"  # Player can move freely
    IN_BATTLE = "in_battle"  # Player is in a battle encounter
    AT_BOSS = "at_boss"  # Player is at boss tile
    COMPLETED = "completed"  # Dungeon completed
    EXITED = "exited"  # Player exited early


class MoveResult(StrEnum):
    """Result of a movement attempt."""

    SUCCESS = "success"  # Move successful
    INVALID_POSITION = "invalid_position"  # Target not adjacent or out of bounds
    IN_BATTLE = "in_battle"  # Cannot move while in battle
    ALREADY_THERE = "already_there"  # Already at target position


class TileEventType(StrEnum):
    """Type of event triggered when stepping on a tile."""

    NONE = "none"  # Empty tile, no event
    BATTLE = "battle"  # Enemy encounter
    CHEST = "chest"  # Chest to open
    BOSS = "boss"  # Boss encounter
    LADDER = "ladder"  # Ladder to next floor
    ENTRANCE = "entrance"  # Back at entrance (can exit)


@dataclass
class MoveValidationResult:
    """Result of movement validation."""

    valid: bool
    result: MoveResult
    message: str | None = None


@dataclass
class TileEvent:
    """Event triggered when stepping on a tile."""

    event_type: TileEventType
    tile: DungeonTile
    metadata: dict | None = None


@dataclass
class ExploreStepResult:
    """Result of one exploration step (move + event)."""

    move_result: MoveResult
    tile_event: TileEvent | None = None
    battle_result: DungeonBattleResult | None = None
    chest_result: LootItem | None = None
    map_updated: bool = False
    can_continue: bool = True


class DungeonExplorationService:
    """Service for dungeon exploration mechanics.

    Handles:
    - Movement validation (Task 8.1)
    - Tile reveal and event triggering (Task 8.2)

    Requirements covered:
    - 1.3: Player movement to adjacent tiles
    - 1.4: Enemy tile triggers battle
    - 4.1: Boss tile triggers boss battle
    """

    # =========================================================================
    # Movement Validation (Task 8.1)
    # =========================================================================

    @staticmethod
    def validate_move(
        dungeon_map: DungeonMap,
        target_x: int,
        target_y: int,
        exploration_status: ExplorationStatus = ExplorationStatus.EXPLORING,
    ) -> MoveValidationResult:
        """Validate if a move to the target position is allowed.

        Checks:
        1. Target position is within map bounds
        2. Target position is adjacent to current position (cardinal directions only)
        3. Player is not currently in battle

        Args:
            dungeon_map: Current dungeon map state
            target_x: Target X coordinate
            target_y: Target Y coordinate
            exploration_status: Current exploration status

        Returns:
            MoveValidationResult with validation outcome

        Requirements:
            - 1.3: WHEN a player moves to an adjacent tile
        """
        # Check if player is in battle
        if exploration_status == ExplorationStatus.IN_BATTLE:
            return MoveValidationResult(
                valid=False,
                result=MoveResult.IN_BATTLE,
                message="Cannot move while in battle",
            )

        # Check if already at target position
        current_x, current_y = dungeon_map.player_position
        if current_x == target_x and current_y == target_y:
            return MoveValidationResult(
                valid=False,
                result=MoveResult.ALREADY_THERE,
                message="Already at this position",
            )

        # Check if target is within bounds
        if not (0 <= target_x < dungeon_map.size and 0 <= target_y < dungeon_map.size):
            return MoveValidationResult(
                valid=False,
                result=MoveResult.INVALID_POSITION,
                message="Target position is out of bounds",
            )

        # Check if target is adjacent (cardinal directions only)
        if not dungeon_map.is_adjacent(target_x, target_y):
            return MoveValidationResult(
                valid=False,
                result=MoveResult.INVALID_POSITION,
                message="Target position is not adjacent",
            )

        return MoveValidationResult(
            valid=True,
            result=MoveResult.SUCCESS,
        )

    @staticmethod
    def get_valid_moves(
        dungeon_map: DungeonMap,
        exploration_status: ExplorationStatus = ExplorationStatus.EXPLORING,
    ) -> list[tuple[int, int]]:
        """Get all valid move positions from current position.

        Args:
            dungeon_map: Current dungeon map state
            exploration_status: Current exploration status

        Returns:
            List of (x, y) tuples for valid move targets
        """
        if exploration_status == ExplorationStatus.IN_BATTLE:
            return []

        valid_moves = []
        current_x, current_y = dungeon_map.player_position

        # Check all cardinal directions
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            target_x = current_x + dx
            target_y = current_y + dy

            # Check bounds
            if 0 <= target_x < dungeon_map.size and 0 <= target_y < dungeon_map.size:
                valid_moves.append((target_x, target_y))

        return valid_moves

    # =========================================================================
    # Tile Reveal and Event Triggering (Task 8.2)
    # =========================================================================

    @staticmethod
    def move_player(
        dungeon_map: DungeonMap,
        target_x: int,
        target_y: int,
        exploration_status: ExplorationStatus = ExplorationStatus.EXPLORING,
    ) -> tuple[DungeonMap, MoveValidationResult]:
        """Move player to target position if valid.

        This method validates the move and updates the map state.
        Does NOT trigger events - use reveal_and_trigger_event for that.

        Args:
            dungeon_map: Current dungeon map state
            target_x: Target X coordinate
            target_y: Target Y coordinate
            exploration_status: Current exploration status

        Returns:
            Tuple of (updated_map, validation_result)
        """
        validation = DungeonExplorationService.validate_move(
            dungeon_map, target_x, target_y, exploration_status
        )

        if not validation.valid:
            return dungeon_map, validation

        # Update player position
        dungeon_map.player_position = (target_x, target_y)

        return dungeon_map, validation

    @staticmethod
    def reveal_tile(dungeon_map: DungeonMap, x: int, y: int) -> DungeonMap:
        """Mark a tile as visible and visited.

        Args:
            dungeon_map: Current dungeon map state
            x: Tile X coordinate
            y: Tile Y coordinate

        Returns:
            Updated dungeon map

        Requirements:
            - 1.3: Reveal tile content on move
        """
        tile = dungeon_map.get_tile(x, y)
        if tile:
            tile.is_visible = True
            tile.is_visited = True
        return dungeon_map

    @staticmethod
    def reveal_adjacent_tiles(dungeon_map: DungeonMap) -> DungeonMap:
        """Reveal all tiles adjacent to player's current position.

        This provides visibility of surrounding tiles without visiting them.

        Args:
            dungeon_map: Current dungeon map state

        Returns:
            Updated dungeon map with adjacent tiles visible
        """
        for tile in dungeon_map.get_adjacent_tiles():
            tile.is_visible = True
        return dungeon_map

    @staticmethod
    def get_tile_event(tile: DungeonTile) -> TileEvent:
        """Determine what event should trigger for a tile.

        Args:
            tile: The tile to check

        Returns:
            TileEvent describing what should happen

        Requirements:
            - 1.3: Trigger appropriate events based on tile type
            - 1.4: Enemy tile triggers battle
            - 4.1: Boss tile triggers boss battle
        """
        event_mapping = {
            TileType.EMPTY: TileEventType.NONE,
            TileType.ENTRANCE: TileEventType.ENTRANCE,
            TileType.ENEMY: TileEventType.BATTLE,
            TileType.CHEST: TileEventType.CHEST,
            TileType.BOSS: TileEventType.BOSS,
            TileType.LADDER: TileEventType.LADDER,
        }

        event_type = event_mapping.get(tile.tile_type, TileEventType.NONE)

        return TileEvent(
            event_type=event_type,
            tile=tile,
            metadata=tile.metadata,
        )

    @staticmethod
    def reveal_and_trigger_event(
        dungeon_map: DungeonMap,
        target_x: int,
        target_y: int,
        exploration_status: ExplorationStatus = ExplorationStatus.EXPLORING,
    ) -> tuple[DungeonMap, ExploreStepResult]:
        """Move to a tile, reveal it, and determine the triggered event.

        This is the main exploration step method that combines:
        1. Movement validation
        2. Player position update
        3. Tile reveal (visible + visited)
        4. Event determination

        Args:
            dungeon_map: Current dungeon map state
            target_x: Target X coordinate
            target_y: Target Y coordinate
            exploration_status: Current exploration status

        Returns:
            Tuple of (updated_map, ExploreStepResult)

        Requirements:
            - 1.3: Move to adjacent tile, reveal content, trigger events
            - 1.4: Enemy tile triggers battle
            - 4.1: Boss tile triggers boss battle
        """
        # Validate and execute move
        dungeon_map, validation = DungeonExplorationService.move_player(
            dungeon_map, target_x, target_y, exploration_status
        )

        if not validation.valid:
            return dungeon_map, ExploreStepResult(
                move_result=validation.result,
                tile_event=None,
                map_updated=False,
                can_continue=True,
            )

        # Reveal the tile we moved to
        dungeon_map = DungeonExplorationService.reveal_tile(
            dungeon_map, target_x, target_y
        )

        # Also reveal adjacent tiles for visibility
        dungeon_map = DungeonExplorationService.reveal_adjacent_tiles(dungeon_map)

        # Get the tile and determine event
        tile = dungeon_map.get_tile(target_x, target_y)
        if not tile:
            return dungeon_map, ExploreStepResult(
                move_result=MoveResult.INVALID_POSITION,
                tile_event=None,
                map_updated=False,
                can_continue=True,
            )

        tile_event = DungeonExplorationService.get_tile_event(tile)

        # Determine if exploration can continue
        # Battle, boss, and chest tiles pause exploration for interaction
        # Requirements 1.4: Enemy tile triggers battle
        # Requirements 4.1: Boss tile triggers boss battle
        # Requirements 3.1: Chest triggers loot selection
        can_continue = tile_event.event_type not in {
            TileEventType.BOSS,
            TileEventType.BATTLE,
            TileEventType.CHEST,
        }

        return dungeon_map, ExploreStepResult(
            move_result=MoveResult.SUCCESS,
            tile_event=tile_event,
            map_updated=True,
            can_continue=can_continue,
        )

    @staticmethod
    def clear_tile(dungeon_map: DungeonMap, x: int, y: int) -> DungeonMap:
        """Clear a tile after its event has been handled.

        Changes enemy/chest tiles to empty after battle/loot collection.

        Args:
            dungeon_map: Current dungeon map state
            x: Tile X coordinate
            y: Tile Y coordinate

        Returns:
            Updated dungeon map

        Requirements:
            - 2.2: Mark tile as cleared after defeating enemy
        """
        tile = dungeon_map.get_tile(x, y)
        if tile and tile.tile_type in {TileType.ENEMY, TileType.CHEST}:
            tile.tile_type = TileType.EMPTY
            tile.metadata = None
        return dungeon_map

    @staticmethod
    def is_at_entrance(dungeon_map: DungeonMap) -> bool:
        """Check if player is at the entrance tile.

        Args:
            dungeon_map: Current dungeon map state

        Returns:
            True if player is at entrance

        Requirements:
            - 8.1: Exit only allowed at entrance
        """
        return dungeon_map.player_position == dungeon_map.entrance_position

    @staticmethod
    def can_exit(
        dungeon_map: DungeonMap,
        exploration_status: ExplorationStatus,
    ) -> tuple[bool, str | None]:
        """Check if player can exit the dungeon.

        Args:
            dungeon_map: Current dungeon map state
            exploration_status: Current exploration status

        Returns:
            Tuple of (can_exit, reason_if_not)

        Requirements:
            - 8.1: Exit only at entrance tile
            - 8.5: Cannot exit while in battle
        """
        if exploration_status == ExplorationStatus.IN_BATTLE:
            return False, "Cannot exit while in battle"

        if not DungeonExplorationService.is_at_entrance(dungeon_map):
            return False, "Must be at entrance to exit"

        return True, None
