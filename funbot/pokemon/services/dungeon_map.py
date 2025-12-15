"""Dungeon map data structures and generation.

Defines the map structure for dungeon exploration including tiles,
map generation, and serialization for persistence.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class TileType(StrEnum):
    """Types of tiles in a dungeon map.

    Matches PokeClicker's DungeonTile types.
    """

    ENTRANCE = "entrance"  # Starting position, can exit here
    ENEMY = "enemy"  # Wild Pokemon or trainer encounter
    CHEST = "chest"  # Treasure chest with loot
    BOSS = "boss"  # Boss encounter (final floor)
    EMPTY = "empty"  # Empty tile, no encounter
    LADDER = "ladder"  # Ladder to next floor (multi-floor dungeons)


@dataclass
class DungeonTile:
    """Single tile in a dungeon map.

    Attributes:
        x: X coordinate (column)
        y: Y coordinate (row)
        tile_type: Type of tile (entrance, enemy, chest, boss, empty, ladder)
        is_visible: Whether the tile has been revealed
        is_visited: Whether the player has stepped on this tile
        metadata: Additional data (enemy info, loot info, etc.)
    """

    x: int
    y: int
    tile_type: TileType
    is_visible: bool = False
    is_visited: bool = False
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize tile to dictionary for JSON storage."""
        return {
            "x": self.x,
            "y": self.y,
            "tile_type": self.tile_type.value,
            "is_visible": self.is_visible,
            "is_visited": self.is_visited,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DungeonTile:
        """Deserialize tile from dictionary."""
        return cls(
            x=data["x"],
            y=data["y"],
            tile_type=TileType(data["tile_type"]),
            is_visible=data.get("is_visible", False),
            is_visited=data.get("is_visited", False),
            metadata=data.get("metadata"),
        )


@dataclass
class DungeonMap:
    """Complete dungeon map state.

    Attributes:
        size: Size of the map (NxN grid)
        tiles: 2D grid of tiles [y][x]
        player_position: Current player position (x, y)
        floor: Current floor number (1-indexed)
        total_floors: Total number of floors in dungeon
        entrance_position: Position of entrance tile
    """

    size: int
    tiles: list[list[DungeonTile]]
    player_position: tuple[int, int]
    floor: int = 1
    total_floors: int = 1
    entrance_position: tuple[int, int] = field(default_factory=lambda: (0, 0))

    def get_tile(self, x: int, y: int) -> DungeonTile | None:
        """Get tile at position, or None if out of bounds."""
        if 0 <= x < self.size and 0 <= y < self.size:
            return self.tiles[y][x]
        return None

    def get_current_tile(self) -> DungeonTile | None:
        """Get the tile at player's current position."""
        x, y = self.player_position
        return self.get_tile(x, y)

    def is_adjacent(self, x: int, y: int) -> bool:
        """Check if position is adjacent to player's current position."""
        px, py = self.player_position
        dx = abs(x - px)
        dy = abs(y - py)
        # Adjacent means exactly 1 step in cardinal direction (no diagonals)
        return (dx == 1 and dy == 0) or (dx == 0 and dy == 1)

    def get_adjacent_tiles(self) -> list[DungeonTile]:
        """Get all tiles adjacent to player's current position."""
        px, py = self.player_position
        adjacent = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            tile = self.get_tile(px + dx, py + dy)
            if tile:
                adjacent.append(tile)
        return adjacent

    def count_tiles_by_type(self, tile_type: TileType) -> int:
        """Count tiles of a specific type."""
        count = 0
        for row in self.tiles:
            for tile in row:
                if tile.tile_type == tile_type:
                    count += 1
        return count

    def to_dict(self) -> dict[str, Any]:
        """Serialize map to dictionary for JSON storage."""
        return {
            "size": self.size,
            "tiles": [[tile.to_dict() for tile in row] for row in self.tiles],
            "player_position": list(self.player_position),
            "floor": self.floor,
            "total_floors": self.total_floors,
            "entrance_position": list(self.entrance_position),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DungeonMap:
        """Deserialize map from dictionary."""
        tiles = [
            [DungeonTile.from_dict(tile_data) for tile_data in row]
            for row in data["tiles"]
        ]
        return cls(
            size=data["size"],
            tiles=tiles,
            player_position=tuple(data["player_position"]),
            floor=data.get("floor", 1),
            total_floors=data.get("total_floors", 1),
            entrance_position=tuple(data.get("entrance_position", [0, 0])),
        )

    def to_json(self) -> str:
        """Serialize map to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> DungeonMap:
        """Deserialize map from JSON string."""
        return cls.from_dict(json.loads(json_str))


class DungeonMapGenerator:
    """Generator for dungeon maps.

    Creates randomized dungeon maps following PokeClicker's layout rules:
    - Entrance at bottom center
    - Boss/ladder at random position (not adjacent to entrance)
    - Enemies and chests distributed randomly
    - Remaining tiles are empty
    """

    # Default distribution ratios
    DEFAULT_ENEMY_RATIO = 0.3  # 30% of non-special tiles are enemies
    DEFAULT_CHEST_RATIO = 0.2  # 20% of non-special tiles are chests

    @staticmethod
    def generate(
        size: int,
        floor: int = 1,
        total_floors: int = 1,
        enemy_count: int | None = None,
        chest_count: int | None = None,
    ) -> DungeonMap:
        """Generate a new dungeon map.

        Args:
            size: Size of the map (NxN grid), minimum 5
            floor: Current floor number (1-indexed)
            total_floors: Total number of floors
            enemy_count: Number of enemy tiles (default: size)
            chest_count: Number of chest tiles (default: size)

        Returns:
            Generated DungeonMap with all tiles placed

        Raises:
            ValueError: If size is too small or counts exceed available tiles
        """
        min_size = 5
        if size < min_size:
            msg = f"Map size must be at least {min_size}"
            raise ValueError(msg)

        # Default counts based on size (matching design doc: at least N enemies and N chests)
        if enemy_count is None:
            enemy_count = size
        if chest_count is None:
            chest_count = size

        # Calculate available tiles (total - entrance - boss/ladder)
        total_tiles = size * size
        special_tiles = 2  # entrance + boss/ladder
        available_tiles = total_tiles - special_tiles

        if enemy_count + chest_count > available_tiles:
            msg = (
                f"Cannot fit {enemy_count} enemies and {chest_count} chests "
                f"in {available_tiles} available tiles"
            )
            raise ValueError(msg)

        # Initialize all tiles as empty
        tiles: list[list[DungeonTile]] = [
            [
                DungeonTile(
                    x=x,
                    y=y,
                    tile_type=TileType.EMPTY,
                    is_visible=False,
                    is_visited=False,
                )
                for x in range(size)
            ]
            for y in range(size)
        ]

        # Place entrance at bottom center
        entrance_x = size // 2
        entrance_y = size - 1
        tiles[entrance_y][entrance_x].tile_type = TileType.ENTRANCE
        tiles[entrance_y][entrance_x].is_visible = True
        tiles[entrance_y][entrance_x].is_visited = True

        # Get positions adjacent to entrance (to exclude for boss placement)
        entrance_adjacent = DungeonMapGenerator._get_adjacent_positions(
            entrance_x, entrance_y, size
        )

        # Place boss (final floor) or ladder (non-final floor)
        boss_tile_type = TileType.BOSS if floor == total_floors else TileType.LADDER

        # Find valid positions for boss (not entrance, not adjacent to entrance)
        valid_boss_positions = [
            (x, y)
            for y in range(size)
            for x in range(size)
            if (x, y) != (entrance_x, entrance_y) and (x, y) not in entrance_adjacent
        ]

        if not valid_boss_positions:
            msg = "No valid position for boss/ladder"
            raise ValueError(msg)

        boss_x, boss_y = random.choice(valid_boss_positions)
        tiles[boss_y][boss_x].tile_type = boss_tile_type

        # Collect remaining empty positions for enemies and chests
        empty_positions = [
            (x, y)
            for y in range(size)
            for x in range(size)
            if tiles[y][x].tile_type == TileType.EMPTY
        ]

        # Shuffle and distribute enemies and chests
        random.shuffle(empty_positions)

        # Place enemies
        for i in range(min(enemy_count, len(empty_positions))):
            x, y = empty_positions[i]
            tiles[y][x].tile_type = TileType.ENEMY

        # Place chests
        remaining_positions = empty_positions[enemy_count:]
        for i in range(min(chest_count, len(remaining_positions))):
            x, y = remaining_positions[i]
            tiles[y][x].tile_type = TileType.CHEST

        return DungeonMap(
            size=size,
            tiles=tiles,
            player_position=(entrance_x, entrance_y),
            floor=floor,
            total_floors=total_floors,
            entrance_position=(entrance_x, entrance_y),
        )

    @staticmethod
    def _get_adjacent_positions(x: int, y: int, size: int) -> list[tuple[int, int]]:
        """Get all valid adjacent positions (cardinal directions only)."""
        adjacent = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < size and 0 <= ny < size:
                adjacent.append((nx, ny))
        return adjacent
