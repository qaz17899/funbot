"""TemporaryBattle database models.

Stores NPC battles that are not gym leaders (rivals, story battles, etc.)
"""

from __future__ import annotations

from tortoise import fields

from funbot.db.models.base import BaseModel


class TemporaryBattleData(BaseModel):
    """Storage for temporary battle data parsed from Pokeclicker TemporaryBattleList.ts.

    Temporary battles include:
    - Rival battles (Blue 1-6, Silver 1-7, May 1-4, etc.)
    - Story NPC battles (Team Rocket, Plasma, etc.)
    - Wild Pokemon encounters (Snorlax, Suicune, Red Gyarados)
    - Special event battles (Santa Jynx, etc.)
    """

    class Meta:
        table = "pokemon_temporary_battle_data"

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100, unique=True)  # Internal name (e.g., "Blue 1")
    display_name = fields.CharField(max_length=100)  # Display name (e.g., "Rival Blue")
    region = fields.IntField(default=-1)
    defeat_message = fields.TextField(null=True)
    return_town = fields.CharField(max_length=100, null=True)
    image_name = fields.CharField(max_length=100, null=True)
    reset_daily = fields.BooleanField(default=False)  # Battle resets daily

    # Reverse relation for battle Pokemon
    pokemon: fields.ReverseRelation["TemporaryBattlePokemon"]

    def __str__(self) -> str:
        return f"{self.display_name}"


class TemporaryBattlePokemon(BaseModel):
    """Pokemon in a temporary battle."""

    class Meta:
        table = "pokemon_temporary_battle_pokemon"

    id = fields.IntField(primary_key=True)
    battle = fields.ForeignKeyField(
        "models.TemporaryBattleData", related_name="pokemon", on_delete=fields.CASCADE
    )
    pokemon_name = fields.CharField(max_length=100)
    health = fields.BigIntField()  # BigInt needed for large health values (e.g., 728176260)
    level = fields.IntField()
    shiny = fields.BooleanField(default=False)
    order = fields.IntField(default=0)  # Position in team

    def __str__(self) -> str:
        shiny_mark = "✨" if self.shiny else ""
        return f"{shiny_mark}{self.pokemon_name} (Lv.{self.level})"


class PlayerBattleProgress(BaseModel):
    """Track player's temporary battle defeats."""

    class Meta:
        table = "pokemon_player_battle_progress"
        unique_together = (("player", "battle"),)

    id = fields.IntField(primary_key=True)
    player = fields.ForeignKeyField(
        "models.User", related_name="battle_progress", on_delete=fields.CASCADE
    )
    battle = fields.ForeignKeyField(
        "models.TemporaryBattleData", related_name="player_progress", on_delete=fields.CASCADE
    )
    defeats = fields.IntField(default=0)  # Times defeated
    last_defeated = fields.DatetimeField(null=True)

    def __str__(self) -> str:
        return f"{self.battle.name}: {self.defeats} defeats"
