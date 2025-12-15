"""Hypothesis strategies for dungeon system property tests."""

from __future__ import annotations

from hypothesis import strategies as st

# Strategy for dungeon clear counts (0 to reasonable max)
clear_counts = st.integers(min_value=0, max_value=10000)

# Strategy for region numbers (0=Kanto to 8=Paldea)
region_numbers = st.integers(min_value=0, max_value=8)


# Strategy for loot tier weights (positive floats that sum to ~1)
@st.composite
def loot_tier_weights(draw: st.DrawFn) -> dict[str, float]:
    """Generate valid loot tier weight dictionaries."""
    from funbot.pokemon.services.dungeon_loot_service import LootTier

    # Generate weights for each tier
    common = draw(st.floats(min_value=0.1, max_value=0.9))
    rare = draw(st.floats(min_value=0.01, max_value=0.3))
    epic = draw(st.floats(min_value=0.001, max_value=0.1))
    legendary = draw(st.floats(min_value=0.0001, max_value=0.05))
    mythic = draw(st.floats(min_value=0.00001, max_value=0.01))

    return {
        LootTier.COMMON: common,
        LootTier.RARE: rare,
        LootTier.EPIC: epic,
        LootTier.LEGENDARY: legendary,
        LootTier.MYTHIC: mythic,
    }
