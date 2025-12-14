"""Gym and Badge database models."""

from __future__ import annotations

from tortoise import fields

from funbot.db.models.base import BaseModel


class GymData(BaseModel):
    """Storage for gym data parsed from Pokeclicker GymList.ts."""

    class Meta:
        table = "pokemon_gym_data"

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100, unique=True)  # Town name
    leader = fields.CharField(max_length=50)
    region = fields.IntField(default=0)
    badge = fields.CharField(max_length=50)  # Badge name (e.g., "Boulder")
    badge_id = fields.IntField(null=True)  # Badge enum value
    money_reward = fields.IntField(default=0)
    defeat_message = fields.TextField(null=True)
    is_elite = fields.BooleanField(default=False)

    # Reverse relation for gym Pokemon
    pokemon: fields.ReverseRelation[GymPokemon]

    def __str__(self) -> str:
        return f"{self.name} ({self.leader})"


class GymPokemon(BaseModel):
    """Pokemon in a gym leader's team."""

    class Meta:
        table = "pokemon_gym_pokemon"

    id = fields.IntField(primary_key=True)
    gym = fields.ForeignKeyField("models.GymData", related_name="pokemon", on_delete=fields.CASCADE)
    pokemon_name = fields.CharField(max_length=100)
    max_health = fields.IntField()
    level = fields.IntField()
    order = fields.IntField(default=0)  # Position in team

    def __str__(self) -> str:
        return f"{self.pokemon_name} (Lv.{self.level})"


class PlayerBadge(BaseModel):
    """Badges earned by a player."""

    class Meta:
        table = "pokemon_player_badges"
        unique_together = (("user", "badge"),)

    id = fields.IntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="badges", on_delete=fields.CASCADE)
    badge = fields.CharField(max_length=50)  # Badge name
    badge_id = fields.IntField(null=True)  # Badge enum value
    earned_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Badge: {self.badge}"
