"""Database models."""

from __future__ import annotations

from funbot.db.models.base import BaseModel, CachedModel
from funbot.db.models.pokemon import (
    # Dungeon system
    DungeonData,
    DungeonLoot,
    DungeonPokemon,
    # Gym system
    GymData,
    GymPokemon,
    KeyItemType,
    PlayerBadge,
    # Player progress
    PlayerBattleProgress,
    PlayerDungeonProgress,
    PlayerKeyItem,
    PlayerPokeballSettings,
    PlayerPokemon,
    PlayerQuestProgress,
    PlayerRouteProgress,
    PlayerWallet,
    PokemonData,
    # QuestLine system
    QuestData,
    QuestLineData,
    QuestLineState,
    RequirementType,
    RoamingPokemon,
    RouteData,
    RouteRequirement,
    SpecialRoutePokemon,
    # TemporaryBattle system
    TemporaryBattleData,
    TemporaryBattlePokemon,
)
from funbot.db.models.user import User

__all__ = (
    "BaseModel",
    "CachedModel",
    "User",
    # Pokemon models
    "PlayerPokeballSettings",
    "PlayerPokemon",
    "PlayerWallet",
    "PokemonData",
    # Route system models
    "RouteData",
    "RouteRequirement",
    "SpecialRoutePokemon",
    "RoamingPokemon",
    "PlayerRouteProgress",
    "KeyItemType",
    "PlayerKeyItem",
    "RequirementType",
    # Gym system models
    "GymData",
    "GymPokemon",
    "PlayerBadge",
    # Dungeon system models
    "DungeonData",
    "DungeonPokemon",
    "DungeonLoot",
    "PlayerDungeonProgress",
    # TemporaryBattle system models
    "TemporaryBattleData",
    "TemporaryBattlePokemon",
    "PlayerBattleProgress",
    # QuestLine system models
    "QuestLineData",
    "QuestData",
    "PlayerQuestProgress",
    "QuestLineState",
)
