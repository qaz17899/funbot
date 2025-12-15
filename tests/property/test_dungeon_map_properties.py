"""Property-based tests for DungeonMapGenerator.

Tests correctness properties defined in the design document.
Uses Hypothesis for property-based testing with 100+ iterations.
"""

from __future__ import annotations

from hypothesis import given, settings, strategies as st

from funbot.pokemon.services.dungeon_map import (
    DungeonMapGenerator,
    TileType,
)


class TestMapGenerationInvariants:
    """Property tests for map generation invariants."""

    # **Feature: dungeon-system, Property 2: Map Generation Invariants**
    # **Validates: Requirements 1.2**
    @settings(max_examples=100)
    @given(
        size=st.integers(min_value=5, max_value=10),
        floor=st.integers(min_value=1, max_value=5),
    )
    def test_map_generation_invariants(self, size: int, floor: int) -> None:
        """For any generated dungeon map of size N, the map should contain:
        - Exactly one entrance tile at the bottom center
        - Exactly one boss tile (or ladder on non-final floors)
        - At least N enemy tiles
        - At least N chest tiles
        """
        # Ensure floor <= total_floors
        total_floors = max(floor, 1)

        dungeon_map = DungeonMapGenerator.generate(
            size=size,
            floor=floor,
            total_floors=total_floors,
        )

        # Invariant 1: Exactly one entrance tile
        entrance_count = dungeon_map.count_tiles_by_type(TileType.ENTRANCE)
        assert (
            entrance_count == 1
        ), f"Expected exactly 1 entrance tile, got {entrance_count}"

        # Invariant 2: Entrance at bottom center
        expected_entrance_x = size // 2
        expected_entrance_y = size - 1
        entrance_tile = dungeon_map.get_tile(expected_entrance_x, expected_entrance_y)
        assert entrance_tile is not None, "Entrance tile position is out of bounds"
        assert entrance_tile.tile_type == TileType.ENTRANCE, (
            f"Expected entrance at bottom center ({expected_entrance_x}, {expected_entrance_y}), "
            f"but found {entrance_tile.tile_type}"
        )

        # Invariant 3: Exactly one boss or ladder tile
        boss_count = dungeon_map.count_tiles_by_type(TileType.BOSS)
        ladder_count = dungeon_map.count_tiles_by_type(TileType.LADDER)

        if floor == total_floors:
            # Final floor should have boss
            assert (
                boss_count == 1
            ), f"Final floor should have exactly 1 boss tile, got {boss_count}"
            assert (
                ladder_count == 0
            ), f"Final floor should have no ladder tiles, got {ladder_count}"
        else:
            # Non-final floor should have ladder
            assert (
                ladder_count == 1
            ), f"Non-final floor should have exactly 1 ladder tile, got {ladder_count}"
            assert (
                boss_count == 0
            ), f"Non-final floor should have no boss tiles, got {boss_count}"

        # Invariant 4: At least N enemy tiles
        enemy_count = dungeon_map.count_tiles_by_type(TileType.ENEMY)
        assert (
            enemy_count >= size
        ), f"Expected at least {size} enemy tiles, got {enemy_count}"

        # Invariant 5: At least N chest tiles
        chest_count = dungeon_map.count_tiles_by_type(TileType.CHEST)
        assert (
            chest_count >= size
        ), f"Expected at least {size} chest tiles, got {chest_count}"

    @settings(max_examples=100)
    @given(size=st.integers(min_value=5, max_value=10))
    def test_boss_not_adjacent_to_entrance(self, size: int) -> None:
        """Boss/ladder tile should not be adjacent to entrance."""
        dungeon_map = DungeonMapGenerator.generate(size=size)

        # Find entrance position
        entrance_x, entrance_y = dungeon_map.entrance_position

        # Get adjacent positions to entrance
        adjacent_positions = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = entrance_x + dx, entrance_y + dy
            if 0 <= nx < size and 0 <= ny < size:
                adjacent_positions.append((nx, ny))

        # Check that boss/ladder is not in adjacent positions
        for x, y in adjacent_positions:
            tile = dungeon_map.get_tile(x, y)
            assert tile is not None
            assert tile.tile_type not in (TileType.BOSS, TileType.LADDER), (
                f"Boss/ladder at ({x}, {y}) is adjacent to entrance at "
                f"({entrance_x}, {entrance_y})"
            )

    @settings(max_examples=100)
    @given(size=st.integers(min_value=5, max_value=10))
    def test_map_size_matches_specification(self, size: int) -> None:
        """Generated map should have the specified size."""
        dungeon_map = DungeonMapGenerator.generate(size=size)

        assert (
            dungeon_map.size == size
        ), f"Map size should be {size}, got {dungeon_map.size}"
        assert (
            len(dungeon_map.tiles) == size
        ), f"Map should have {size} rows, got {len(dungeon_map.tiles)}"
        for row_idx, row in enumerate(dungeon_map.tiles):
            assert (
                len(row) == size
            ), f"Row {row_idx} should have {size} columns, got {len(row)}"

    @settings(max_examples=100)
    @given(size=st.integers(min_value=5, max_value=10))
    def test_player_starts_at_entrance(self, size: int) -> None:
        """Player should start at the entrance position."""
        dungeon_map = DungeonMapGenerator.generate(size=size)

        assert dungeon_map.player_position == dungeon_map.entrance_position, (
            f"Player should start at entrance {dungeon_map.entrance_position}, "
            f"but is at {dungeon_map.player_position}"
        )

    @settings(max_examples=100)
    @given(size=st.integers(min_value=5, max_value=10))
    def test_entrance_is_visible_and_visited(self, size: int) -> None:
        """Entrance tile should be visible and visited at start."""
        dungeon_map = DungeonMapGenerator.generate(size=size)

        entrance_tile = dungeon_map.get_tile(*dungeon_map.entrance_position)
        assert entrance_tile is not None
        assert entrance_tile.is_visible, "Entrance should be visible at start"
        assert entrance_tile.is_visited, "Entrance should be visited at start"

    @settings(max_examples=100)
    @given(size=st.integers(min_value=5, max_value=10))
    def test_all_tiles_have_valid_type(self, size: int) -> None:
        """All tiles should have a valid TileType."""
        dungeon_map = DungeonMapGenerator.generate(size=size)

        valid_types = set(TileType)
        for y in range(size):
            for x in range(size):
                tile = dungeon_map.get_tile(x, y)
                assert tile is not None, f"Tile at ({x}, {y}) should exist"
                assert (
                    tile.tile_type in valid_types
                ), f"Tile at ({x}, {y}) has invalid type: {tile.tile_type}"
