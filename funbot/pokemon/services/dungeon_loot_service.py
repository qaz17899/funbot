"""Dungeon loot service for loot generation.

Handles loot tier weight calculation and item selection.
Matches PokeClicker's Dungeon.ts loot mechanics.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from funbot.db.models.pokemon.dungeon_data import DungeonLoot


class LootTier(StrEnum):
    """Loot tier classifications matching PokeClicker."""

    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"


# Base loot tier chances from PokeClicker's Dungeon.ts
# These should add up to 1.0
BASE_LOOT_TIER_CHANCE: dict[str, float] = {
    LootTier.COMMON: 0.75,
    LootTier.RARE: 0.2,
    LootTier.EPIC: 0.04,
    LootTier.LEGENDARY: 0.0099,
    LootTier.MYTHIC: 0.0001,
}

# Nerfed/debuffed loot tier chances for overleveled players
# From PokeClicker's Dungeon.ts nerfedLootTierChance
NERFED_LOOT_TIER_CHANCE: dict[str, float] = {
    LootTier.COMMON: 0.75,
    LootTier.RARE: 0.24,
    LootTier.EPIC: 0.009,
    LootTier.LEGENDARY: 0.00099,
    LootTier.MYTHIC: 0.00001,
}

# Loot redistribution factors based on clear count
# Should sum to 0 (takes from common, gives to others)
# From PokeClicker's Dungeon.ts lootRedistribution
LOOT_REDISTRIBUTION: dict[str, float] = {
    LootTier.COMMON: -1.0,
    LootTier.RARE: 0.33,
    LootTier.EPIC: 0.4,
    LootTier.LEGENDARY: 0.2,
    LootTier.MYTHIC: 0.07,
}

# Max amount to take from common and redistribute @ 500 clears
# From PokeClicker's Dungeon.ts lootRedistibuteAmount
LOOT_REDISTRIBUTE_AMOUNT = 0.15


@dataclass
class LootItem:
    """Represents a loot item from a dungeon chest."""

    item_name: str
    tier: str
    amount: int = 1
    is_pokemon: bool = False


class DungeonLootService:
    """Service for dungeon loot generation.

    Matches PokeClicker's loot mechanics:
    - Tier weight calculation based on clear count (Dungeon.ts:283-307)
    - Debuff detection for overleveled players (DungeonRunner.ts:321)
    - Weighted random selection for tiers and items
    """

    @staticmethod
    def get_loot_tier_weights(clears: int, debuffed: bool = False) -> dict[str, float]:
        """Calculate loot tier weights based on clear count and debuff status.

        Matches PokeClicker's Dungeon.ts getLootTierWeights() method.

        The algorithm:
        1. If debuffed, use nerfed tier chances directly
        2. Otherwise, calculate redistribution based on clears:
           - redistribution = LOOT_REDISTRIBUTE_AMOUNT * min(clears, 500) / 500
           - For each tier: base_chance + (redistribution * tier_factor)

        Args:
            clears: Number of times the player has cleared this dungeon
            debuffed: Whether loot should be debuffed (player overleveled)

        Returns:
            Dictionary mapping tier names to their probability weights
        """
        if debuffed:
            # Use nerfed chances directly for debuffed dungeons
            return dict(NERFED_LOOT_TIER_CHANCE)

        # Calculate redistribution amount based on clears
        # Caps at 500 clears for max redistribution
        times_cleared = min(clears, 500)
        redist = LOOT_REDISTRIBUTE_AMOUNT * times_cleared / 500

        # Apply redistribution to base chances
        updated_chances: dict[str, float] = {}
        for tier, base_chance in BASE_LOOT_TIER_CHANCE.items():
            # chance + (redist * redistribution_factor)
            # Common loses, others gain proportionally
            redistribution_factor = LOOT_REDISTRIBUTION[tier]
            updated_chances[tier] = base_chance + (redist * redistribution_factor)

        return updated_chances

    @staticmethod
    def select_loot_tier(weights: dict[str, float]) -> str:
        """Select a random loot tier based on weights.

        Uses weighted random selection matching PokeClicker's
        Rand.fromWeightedArray() behavior.

        Args:
            weights: Dictionary mapping tier names to probability weights

        Returns:
            Selected tier name (common/rare/epic/legendary/mythic)
        """
        if not weights:
            return LootTier.COMMON

        tiers = list(weights.keys())
        tier_weights = list(weights.values())

        # Use random.choices for weighted selection
        selected = random.choices(tiers, weights=tier_weights, k=1)
        return selected[0]

    @staticmethod
    async def select_loot_item(dungeon_id: int, tier: str) -> LootItem | None:
        """Select a random loot item from the dungeon's loot table.

        Args:
            dungeon_id: The dungeon's database ID
            tier: The loot tier to select from

        Returns:
            LootItem if found, None if no items available for tier
        """
        from funbot.db.models.pokemon.dungeon_data import DungeonLoot

        # Get all loot items for this dungeon and tier
        loot_items: list[DungeonLoot] = await DungeonLoot.filter(
            dungeon_id=dungeon_id, tier=tier
        ).all()

        if not loot_items:
            # Fall back to common tier if requested tier is empty
            if tier != LootTier.COMMON:
                loot_items = await DungeonLoot.filter(
                    dungeon_id=dungeon_id, tier=LootTier.COMMON
                ).all()

            if not loot_items:
                return None

        # Weighted random selection based on item weights
        weights = [item.weight for item in loot_items]
        selected = random.choices(loot_items, weights=weights, k=1)[0]

        # Check if this is a Pokemon (would need battle encounter)
        # For now, we'll determine this based on item naming convention
        is_pokemon = DungeonLootService._is_pokemon_loot(selected.item_name)

        return LootItem(
            item_name=selected.item_name,
            tier=selected.tier,
            amount=1,
            is_pokemon=is_pokemon,
        )

    @staticmethod
    def _is_pokemon_loot(item_name: str) -> bool:
        """Check if a loot item is a Pokemon (requires battle encounter).

        In PokeClicker, Pokemon loot triggers a battle encounter.
        This is a simplified check - in production, would check against
        Pokemon database.

        Args:
            item_name: Name of the loot item

        Returns:
            True if this is a Pokemon encounter
        """
        # Common item prefixes/suffixes that indicate non-Pokemon items
        non_pokemon_indicators = [
            "Stone",
            "Berry",
            "Ball",
            "Shard",
            "Plate",
            "Gem",
            "Token",
            "Fossil",
            "Item",
            "Key",
            "TM",
            "HM",
            "Candy",
            "Vitamin",
            "Incense",
            "Mail",
            "Held",
        ]

        for indicator in non_pokemon_indicators:
            if indicator.lower() in item_name.lower():
                return False

        # If no non-Pokemon indicators found, assume it could be a Pokemon
        # This is a heuristic - proper implementation would check Pokemon DB
        return True

    @staticmethod
    def is_dungeon_debuffed(dungeon_region: int, player_region: int) -> bool:
        """Check if dungeon loot should be debuffed.

        Matches PokeClicker's DungeonRunner.isDungeonDebuffed():
        Returns True if player's highest region > dungeon region + 2

        This prevents overleveled players from farming low-level dungeons
        for rare loot.

        Args:
            dungeon_region: The region the dungeon is in (0=Kanto, 1=Johto, etc.)
            player_region: The player's highest unlocked region

        Returns:
            True if loot should be debuffed (nerfed chances)
        """
        return player_region > dungeon_region + 2
