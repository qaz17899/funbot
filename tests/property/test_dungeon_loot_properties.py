"""Property-based tests for DungeonLootService.

Tests correctness properties defined in the design document.
Uses Hypothesis for property-based testing with 100+ iterations.
"""

from __future__ import annotations

from hypothesis import given, settings, strategies as st

from funbot.pokemon.services.dungeon_loot_service import (
    BASE_LOOT_TIER_CHANCE,
    LOOT_REDISTRIBUTE_AMOUNT,
    NERFED_LOOT_TIER_CHANCE,
    DungeonLootService,
    LootTier,
)


class TestLootTierWeights:
    """Property tests for loot tier weight calculations."""

    # **Feature: dungeon-system, Property 11: Clear Count Loot Probability Shift**
    # **Validates: Requirements 3.5**
    @settings(max_examples=100)
    @given(
        clears_low=st.integers(min_value=0, max_value=499),
        clears_high=st.integers(min_value=1, max_value=500),
    )
    def test_clear_count_loot_probability_shift(
        self, clears_low: int, clears_high: int
    ) -> None:
        """For any player with clear count C1 < C2, the probability weights
        for rare+ tiers should be higher (or equal) for C2 compared to C1.
        """
        # Ensure clears_high > clears_low
        if clears_high <= clears_low:
            clears_high = clears_low + 1

        weights_low = DungeonLootService.get_loot_tier_weights(
            clears_low, debuffed=False
        )
        weights_high = DungeonLootService.get_loot_tier_weights(
            clears_high, debuffed=False
        )

        # Rare+ tiers should have higher or equal probability with more clears
        for tier in [LootTier.RARE, LootTier.EPIC, LootTier.LEGENDARY, LootTier.MYTHIC]:
            assert weights_high[tier] >= weights_low[tier], (
                f"Tier {tier} should have higher probability with more clears. "
                f"Got {weights_high[tier]} < {weights_low[tier]} for clears {clears_high} vs {clears_low}"
            )

    # Additional property: weights should sum to approximately 1 (or less)
    @settings(max_examples=100)
    @given(clears=st.integers(min_value=0, max_value=10000))
    def test_weights_sum_valid(self, clears: int) -> None:
        """Weights should sum to a valid probability (0 < sum <= 1)."""
        weights = DungeonLootService.get_loot_tier_weights(clears, debuffed=False)
        total = sum(weights.values())

        # Total should be positive and not exceed 1 significantly
        assert total > 0, "Total weight should be positive"
        assert total <= 1.01, f"Total weight {total} exceeds 1"

    # Property: debuffed weights should match nerfed constants
    @settings(max_examples=100)
    @given(clears=st.integers(min_value=0, max_value=10000))
    def test_debuffed_uses_nerfed_weights(self, clears: int) -> None:
        """When debuffed, weights should match NERFED_LOOT_TIER_CHANCE."""
        weights = DungeonLootService.get_loot_tier_weights(clears, debuffed=True)

        for tier in LootTier:
            assert (
                weights[tier] == NERFED_LOOT_TIER_CHANCE[tier]
            ), f"Debuffed tier {tier} should match nerfed constant"


class TestLootTierSelection:
    """Property tests for loot tier selection."""

    # **Feature: dungeon-system, Property 9: Loot Tier Selection Validity**
    # **Validates: Requirements 3.1, 3.2**
    @settings(max_examples=100)
    @given(clears=st.integers(min_value=0, max_value=1000))
    def test_loot_tier_selection_validity(self, clears: int) -> None:
        """For any chest opening, the selected loot tier should be one of
        the valid tiers (common, rare, epic, legendary, mythic).
        """
        weights = DungeonLootService.get_loot_tier_weights(clears, debuffed=False)
        selected_tier = DungeonLootService.select_loot_tier(weights)

        valid_tiers = {tier.value for tier in LootTier}
        assert selected_tier in valid_tiers, (
            f"Selected tier '{selected_tier}' is not a valid tier. "
            f"Valid tiers: {valid_tiers}"
        )

    # Property: selection should only return tiers present in weights
    @settings(max_examples=100)
    @given(clears=st.integers(min_value=0, max_value=1000))
    def test_selection_respects_available_tiers(self, clears: int) -> None:
        """Selected tier should be one that exists in the weights dict."""
        weights = DungeonLootService.get_loot_tier_weights(clears, debuffed=False)
        selected_tier = DungeonLootService.select_loot_tier(weights)

        assert (
            selected_tier in weights
        ), f"Selected tier '{selected_tier}' not in weights: {weights.keys()}"


class TestDebuffDetection:
    """Property tests for dungeon debuff detection."""

    # **Feature: dungeon-system, Property 20: Loot Debuff Application**
    # **Validates: Requirements 7.3**
    @settings(max_examples=100)
    @given(
        dungeon_region=st.integers(min_value=0, max_value=8),
        player_region=st.integers(min_value=0, max_value=8),
    )
    def test_loot_debuff_application(
        self, dungeon_region: int, player_region: int
    ) -> None:
        """For any dungeon where player's highest region > dungeon region + 2,
        the loot tier probabilities should use the debuffed weights.
        """
        is_debuffed = DungeonLootService.is_dungeon_debuffed(
            dungeon_region, player_region
        )

        expected_debuffed = player_region > dungeon_region + 2
        assert is_debuffed == expected_debuffed, (
            f"Debuff detection incorrect. "
            f"dungeon_region={dungeon_region}, player_region={player_region}. "
            f"Expected debuffed={expected_debuffed}, got {is_debuffed}"
        )

    # Property: debuff should never apply when player is at or below dungeon region + 2
    @settings(max_examples=100)
    @given(dungeon_region=st.integers(min_value=0, max_value=8))
    def test_no_debuff_at_appropriate_level(self, dungeon_region: int) -> None:
        """Player at dungeon_region + 2 or below should not be debuffed."""
        for offset in range(3):  # 0, 1, 2
            player_region = dungeon_region + offset
            is_debuffed = DungeonLootService.is_dungeon_debuffed(
                dungeon_region, player_region
            )
            assert not is_debuffed, (
                f"Should not be debuffed at offset {offset}. "
                f"dungeon_region={dungeon_region}, player_region={player_region}"
            )

    # Property: debuff should always apply when player is 3+ regions ahead
    @settings(max_examples=100)
    @given(
        dungeon_region=st.integers(min_value=0, max_value=5),
        extra_regions=st.integers(min_value=3, max_value=8),
    )
    def test_debuff_when_overleveled(
        self, dungeon_region: int, extra_regions: int
    ) -> None:
        """Player 3+ regions ahead should always be debuffed."""
        player_region = dungeon_region + extra_regions
        is_debuffed = DungeonLootService.is_dungeon_debuffed(
            dungeon_region, player_region
        )
        assert is_debuffed, (
            f"Should be debuffed when {extra_regions} regions ahead. "
            f"dungeon_region={dungeon_region}, player_region={player_region}"
        )
