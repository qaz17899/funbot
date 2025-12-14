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
    # Dungeon system models
    "DungeonData",
    "DungeonLoot",
    "DungeonPokemon",
    # Gym system models
    "GymData",
    "GymPokemon",
    "KeyItemType",
    "PlayerBadge",
    "PlayerBattleProgress",
    "PlayerDungeonProgress",
    "PlayerKeyItem",
    # Pokemon models
    "PlayerPokeballSettings",
    "PlayerPokemon",
    "PlayerQuestProgress",
    "PlayerRouteProgress",
    "PlayerWallet",
    "PokemonData",
    "QuestData",
    # QuestLine system models
    "QuestLineData",
    "QuestLineState",
    "RequirementType",
    "RoamingPokemon",
    # Route system models
    "RouteData",
    "RouteRequirement",
    "SpecialRoutePokemon",
    # TemporaryBattle system models
    "TemporaryBattleData",
    "TemporaryBattlePokemon",
    "User",
)
