"""Dungeon database models."""

from __future__ import annotations

from tortoise import fields

from funbot.db.models.base import BaseModel


class DungeonData(BaseModel):
    """Storage for dungeon data parsed from Pokeclicker Dungeon.ts."""

    class Meta:
        table = "pokemon_dungeon_data"

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100, unique=True)
    region = fields.IntField(default=0)
    base_health = fields.IntField(null=True)
    token_cost = fields.IntField(null=True)

    # Reverse relations
    pokemon: fields.ReverseRelation[DungeonPokemon]
    loot: fields.ReverseRelation[DungeonLoot]

    def __str__(self) -> str:
        return f"Dungeon: {self.name}"


class DungeonPokemon(BaseModel):
    """Pokemon encounters in a dungeon."""

    class Meta:
        table = "pokemon_dungeon_pokemon"

    id = fields.IntField(primary_key=True)
    dungeon = fields.ForeignKeyField(
        "models.DungeonData", related_name="pokemon", on_delete=fields.CASCADE
    )
    pokemon_name = fields.CharField(max_length=100)
    weight = fields.IntField(default=1)
    is_boss = fields.BooleanField(default=False)
    health = fields.IntField(null=True)  # For bosses
    level = fields.IntField(null=True)  # For bosses

    def __str__(self) -> str:
        prefix = "[BOSS] " if self.is_boss else ""
        return f"{prefix}{self.pokemon_name}"


class DungeonLoot(BaseModel):
    """Loot drops in a dungeon."""

    class Meta:
        table = "pokemon_dungeon_loot"

    id = fields.IntField(primary_key=True)
    dungeon = fields.ForeignKeyField(
        "models.DungeonData", related_name="loot", on_delete=fields.CASCADE
    )
    item_name = fields.CharField(max_length=100)
    tier = fields.CharField(max_length=20)  # common/rare/epic/legendary/mythic
    weight = fields.IntField(default=1)

    def __str__(self) -> str:
        return f"{self.tier}: {self.item_name}"


class PlayerDungeonProgress(BaseModel):
    """Track player's dungeon clear counts."""

    class Meta:
        table = "pokemon_player_dungeon_progress"
        unique_together = (("player", "dungeon"),)

    id = fields.IntField(primary_key=True)
    player = fields.ForeignKeyField(
        "models.User", related_name="dungeon_progress", on_delete=fields.CASCADE
    )
    dungeon = fields.ForeignKeyField(
        "models.DungeonData", related_name="player_progress", on_delete=fields.CASCADE
    )
    clears = fields.IntField(default=0)
    last_cleared = fields.DatetimeField(null=True)

    def __str__(self) -> str:
        return f"{self.dungeon.name}: {self.clears} clears"
