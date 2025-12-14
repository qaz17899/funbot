"""Key Items model for important progression items.

Based on Pokeclicker's KeyItemType:
- Super_rod: unlocks water Pokemon
- Dungeon_ticket: access dungeons
- etc.
"""

from __future__ import annotations

from tortoise import fields

from funbot.db.models.base import BaseModel
from funbot.pokemon.constants import KeyItemType

# Re-export for backward compatibility
__all__ = ["KeyItemType", "PlayerKeyItem"]


class PlayerKeyItem(BaseModel):
    """Key items owned by a player."""

    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="key_items", on_delete=fields.CASCADE)
    key_item = fields.SmallIntField(description="KeyItemType enum value")
    obtained_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "pokemon_player_key_item"
        unique_together = (("user", "key_item"),)

    def __str__(self) -> str:
        return KeyItemType(self.key_item).name
