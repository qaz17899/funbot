"""Key Items model for important progression items.

Based on Pokeclicker's KeyItemType:
- Super_rod: unlocks water Pokemon
- Dungeon_ticket: access dungeons
- etc.
"""

from __future__ import annotations

from enum import IntEnum

from tortoise import fields
from tortoise.models import Model


class KeyItemType(IntEnum):
    """Key items from Pokeclicker."""

    TEACHY_TV = 0
    COIN_CASE = 1
    POKEBALL_BAG = 2
    TOWN_MAP = 3
    DUNGEON_TICKET = 4
    SUPER_ROD = 5  # Unlocks water Pokemon!
    HOLO_CASTER = 6
    MYSTERY_EGG = 7
    SAFARI_TICKET = 8
    WAILMER_PAIL = 9
    EXPLORER_KIT = 10
    EON_TICKET = 11
    EVENT_CALENDAR = 12
    GEM_CASE = 13
    DNA_SPLICERS = 14
    REINS_OF_UNITY = 15
    POKERUS_VIRUS = 16
    Z_POWER_RING = 17


class PlayerKeyItem(Model):
    """Key items owned by a player."""

    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="key_items", on_delete=fields.CASCADE
    )
    key_item = fields.SmallIntField(description="KeyItemType enum value")
    obtained_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "pokemon_player_key_item"
        unique_together = (("user", "key_item"),)

    def __str__(self) -> str:
        return KeyItemType(self.key_item).name
