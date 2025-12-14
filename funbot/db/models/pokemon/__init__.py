# Pokemon Database Models
"""Tortoise ORM models for the Pokemon system."""

from __future__ import annotations

from funbot.db.models.pokemon.dungeon_data import (
    DungeonData,
    DungeonLoot,
    DungeonPokemon,
    PlayerDungeonProgress,
)
from funbot.db.models.pokemon.gym_data import GymData, GymPokemon, PlayerBadge
from funbot.db.models.pokemon.key_item import KeyItemType, PlayerKeyItem
from funbot.db.models.pokemon.player_pokeball_settings import PlayerPokeballSettings
from funbot.db.models.pokemon.player_pokemon import PlayerPokemon
from funbot.db.models.pokemon.player_quest_progress import PlayerQuestProgress, QuestLineState
from funbot.db.models.pokemon.player_route_progress import PlayerRouteProgress
from funbot.db.models.pokemon.player_wallet import PlayerWallet
from funbot.db.models.pokemon.pokemon_data import PokemonData
from funbot.db.models.pokemon.quest_line_data import QuestData, QuestLineData
from funbot.db.models.pokemon.roaming_pokemon import RoamingPokemon
from funbot.db.models.pokemon.route_data import RouteData
from funbot.db.models.pokemon.route_requirement import (
    RequirementType,
    RouteRequirement,
    SpecialRoutePokemon,
)
from funbot.db.models.pokemon.temporary_battle_data import (
    PlayerBattleProgress,
    TemporaryBattleData,
    TemporaryBattlePokemon,
)

__all__ = [
    # Gym system
    "GymData",
    "GymPokemon",
    "PlayerBadge",
    # Dungeon system
    "DungeonData",
    "DungeonPokemon",
    "DungeonLoot",
    "PlayerDungeonProgress",
    # TemporaryBattle system
    "TemporaryBattleData",
    "TemporaryBattlePokemon",
    "PlayerBattleProgress",
    # QuestLine system
    "QuestLineData",
    "QuestData",
    "PlayerQuestProgress",
    "QuestLineState",
    # Route system
    "RouteData",
    "RouteRequirement",
    "SpecialRoutePokemon",
    "RoamingPokemon",
    "PlayerRouteProgress",
    # Core
    "KeyItemType",
    "PlayerKeyItem",
    "PlayerPokeballSettings",
    "PlayerPokemon",
    "PlayerWallet",
    "PokemonData",
    "RequirementType",
]
