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
    trainers: fields.ReverseRelation[DungeonTrainer]

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


class DungeonTrainer(BaseModel):
    """Trainer encounters in a dungeon.

    Trainers are NPCs that the player can battle in dungeons.
    Each trainer has a team of Pokemon that must be defeated sequentially.
    """

    class Meta:
        table = "pokemon_dungeon_trainer"

    id = fields.IntField(primary_key=True)
    dungeon = fields.ForeignKeyField(
        "models.DungeonData", related_name="trainers", on_delete=fields.CASCADE
    )
    trainer_class = fields.CharField(
        max_length=100
    )  # e.g., "Bug Catcher", "Team Rocket Grunt"
    trainer_name = fields.CharField(max_length=100, null=True)  # Optional specific name
    weight = fields.IntField(default=1)  # Encounter weight
    is_boss = fields.BooleanField(default=False)  # Whether this is a boss trainer

    # Reverse relation for trainer's Pokemon
    pokemon: fields.ReverseRelation[DungeonTrainerPokemon]

    def __str__(self) -> str:
        prefix = "[BOSS] " if self.is_boss else ""
        name = self.trainer_name or self.trainer_class
        return f"{prefix}{name}"


class DungeonTrainerPokemon(BaseModel):
    """Pokemon in a dungeon trainer's team.

    Each Pokemon must be defeated in order before the trainer is considered defeated.
    """

    class Meta:
        table = "pokemon_dungeon_trainer_pokemon"

    id = fields.IntField(primary_key=True)
    trainer = fields.ForeignKeyField(
        "models.DungeonTrainer", related_name="pokemon", on_delete=fields.CASCADE
    )
    pokemon_name = fields.CharField(max_length=100)
    health = fields.BigIntField()  # BigInt for large health values
    level = fields.IntField()
    order = fields.IntField(default=0)  # Position in team (0 = first)

    def __str__(self) -> str:
        return f"{self.pokemon_name} (Lv.{self.level})"


class PlayerDungeonRun(BaseModel):
    """Active dungeon run session.

    Tracks the state of a player's current dungeon exploration.
    Allows resuming interrupted runs and preserves collected loot.
    """

    class Meta:
        table = "pokemon_player_dungeon_run"

    id = fields.IntField(primary_key=True)
    player = fields.ForeignKeyField(
        "models.User", related_name="dungeon_runs", on_delete=fields.CASCADE
    )
    dungeon = fields.ForeignKeyField(
        "models.DungeonData", related_name="active_runs", on_delete=fields.CASCADE
    )
    started_at = fields.DatetimeField(auto_now_add=True)

    # Map state - serialized DungeonMap
    map_data = fields.JSONField(
        description="Serialized map state with tiles and visibility"
    )

    # Current position - {x, y, floor}
    current_position = fields.JSONField(description="Player position {x, y, floor}")

    # Progress tracking
    chests_opened = fields.IntField(default=0)
    enemies_defeated = fields.IntField(default=0)

    # Collected loot - list of {item_name, tier, amount}
    loot_collected = fields.JSONField(
        default=list, description="List of collected loot items"
    )

    # Run status: "in_progress", "completed", "abandoned"
    status = fields.CharField(max_length=20, default="in_progress")

    def __str__(self) -> str:
        return f"Run #{self.id}: {self.dungeon.name} ({self.status})"
