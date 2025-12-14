"""Explore command for encountering wild Pokemon.

/pokemon explore <region> <route> [count] - Encounter and battle wild Pokemon.
Results are calculated instantly, no interactive UI needed.
Uses Discord Components V2 for modern UI.

Features:
- Autocomplete with status indicators (🔒/⚔️/🆕/✨/🌈)
- Kill count tracking
- Unlock requirement checking
- Real route Pokemon data from database
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from funbot.db.models.pokemon import (
    PlayerPokeballSettings,
    PlayerPokemon,
    PlayerRouteProgress,
    PlayerWallet,
    PokemonData,
    RouteData,
)
from funbot.db.models.user import User
from funbot.pokemon.autocomplete import region_autocomplete, route_autocomplete
from funbot.pokemon.constants.enums import PokemonType
from funbot.pokemon.constants.game_constants import BASE_EP_YIELD
from funbot.pokemon.services.battle_service import BattleService, ExploreResult
from funbot.pokemon.services.catch_service import CatchService
from funbot.pokemon.services.exp_service import ExpService
from funbot.pokemon.services.hatchery_service import HatcheryService
from funbot.pokemon.services.route_service import get_route_status_service
from funbot.types import Interaction
from funbot.ui.components_v2 import Container, LayoutView, TextDisplay

if TYPE_CHECKING:
    from funbot.bot import FunBot


class ExploreCog(commands.Cog):
    """Commands for exploring routes and battling wild Pokemon."""

    def __init__(self, bot: FunBot) -> None:
        self.bot = bot
        self._route_service = get_route_status_service()

    @app_commands.command(name="pokemon-explore", description="探索路線遇見野生寶可夢")
    @app_commands.describe(
        region="選擇區域 (關都/城都/...)",
        route="選擇路線 (顯示狀態和擊敗次數)",
        count="遭遇次數 (1-20)",
    )
    @app_commands.autocomplete(region=region_autocomplete, route=route_autocomplete)
    async def pokemon_explore(
        self, interaction: Interaction, region: int = 0, route: int = 0, count: int = 1
    ) -> None:
        """Explore a route and encounter wild Pokemon."""
        await interaction.response.defer()

        # Validate count
        count = max(1, min(20, count))

        # Get user
        user = await User.get_or_none(id=interaction.user.id)
        if not user:
            await interaction.followup.send(
                "❌ 你還沒有開始寶可夢之旅！使用 `/pokemon-start` 選擇初始寶可夢。", ephemeral=True
            )
            return

        # Get user's party Pokemon
        party = await PlayerPokemon.filter(user=user).prefetch_related("pokemon_data")
        if not party:
            await interaction.followup.send(
                "❌ 你還沒有任何寶可夢！使用 `/pokemon-start` 選擇初始寶可夢。", ephemeral=True
            )
            return

        # Get route data from database
        route_data = await RouteData.get_or_none(id=route)
        if not route_data:
            # Try to find by region and number (fallback for manual input)
            route_data = await RouteData.filter(region=region).order_by("order_number").first()
            if not route_data:
                await interaction.followup.send(
                    "❌ 找不到該路線。請使用自動補全選擇路線。", ephemeral=True
                )
                return

        # Check if route is unlocked
        is_unlocked = await self._route_service.is_route_unlocked(user.id, route_data)
        if not is_unlocked:
            hints = await self._route_service.get_requirement_hints(user.id, route_data)
            hint_text = "\n".join(f"• {h}" for h in hints) if hints else "需求未達成"
            await interaction.followup.send(
                f"🔒 **{route_data.name}** 尚未解鎖！\n\n{hint_text}", ephemeral=True
            )
            return

        # Get pokeball settings
        settings, _ = await PlayerPokeballSettings.get_or_create(user=user)

        # Get wallet
        wallet, _ = await PlayerWallet.get_or_create(user=user)

        # Get available wild Pokemon for this route from real data
        wild_pokemon = await self._get_route_pokemon(route_data)
        if not wild_pokemon:
            await interaction.followup.send(
                f"❌ {route_data.name} 暫無可遇見的寶可夢。", ephemeral=True
            )
            return

        # Calculate party attack power
        party_pokemon_data = []
        for poke in party:
            data: PokemonData = poke.pokemon_data  # type: ignore
            attack = ExpService.calculate_attack_from_level(data.base_attack, poke.level)
            party_pokemon_data.append(
                {
                    "attack": attack,
                    "type1": PokemonType(data.type1),
                    "type2": PokemonType(data.type2) if data.type2 else PokemonType.NONE,
                }
            )

        # Simulate encounters
        results = await self._simulate_encounters(
            user=user,
            party=party,
            party_data=party_pokemon_data,
            settings=settings,
            wallet=wallet,
            route_data=route_data,
            wild_pokemon=wild_pokemon,
            count=count,
        )

        # Create result view (V2)
        view = self._create_result_view(interaction.user.display_name, route_data, results)

        await interaction.followup.send(view=view)

    async def _get_route_pokemon(self, route_data: RouteData) -> list[PokemonData]:
        """Get Pokemon available on a route from real database data.

        Uses the route's land_pokemon, water_pokemon, and headbutt_pokemon fields.
        """
        # Collect all Pokemon names from route data
        all_pokemon_names: list[str] = []
        all_pokemon_names.extend(route_data.land_pokemon or [])
        # TODO: Add water_pokemon when fishing is implemented
        # Issue URL: https://github.com/qaz17899/funbot/issues/19
        # TODO: Add headbutt_pokemon when headbutt is implemented
        # Issue URL: https://github.com/qaz17899/funbot/issues/18

        if not all_pokemon_names:
            return []

        # Query PokemonData by name
        pokemon = await PokemonData.filter(name__in=all_pokemon_names)

        return list(pokemon)

    async def _simulate_encounters(
        self,
        user: User,
        party: list[PlayerPokemon],
        party_data: list[dict],
        settings: PlayerPokeballSettings,
        wallet: PlayerWallet,
        route_data: RouteData,
        wild_pokemon: list[PokemonData],
        count: int,
    ) -> ExploreResult:
        """Simulate multiple encounters and return structured result."""
        # Track results
        pokemon_defeated = 0
        caught_pokemon: list[tuple[str, int, bool]] = []  # (name, id, is_shiny)
        shiny_count = 0
        total_money = 0
        total_exp = 0

        # Track per-species statistics for batch update
        # Key: pokemon_data_id, Value: {encountered, defeated, captured, shiny variants}
        species_stats: dict[int, dict[str, int]] = {}

        # Map owned Pokemon for EP gain
        owned_pokemon_map: dict[int, PlayerPokemon] = {p.pokemon_data.id: p for p in party}  # type: ignore
        owned_ids = set(owned_pokemon_map.keys())

        # Get route parameters
        route_number = route_data.number
        region = route_data.region

        # Calculate health (use custom_health if set, otherwise formula)
        if route_data.custom_health:
            base_health = route_data.custom_health
        else:
            base_health = BattleService.calculate_route_health(route_number, region)

        # Collect new Pokemon to create in bulk after the loop
        new_pokemon_to_create: list[dict] = []

        for _ in range(count):
            # Pick random wild Pokemon
            wild = random.choice(wild_pokemon)
            is_shiny = CatchService.roll_shiny()

            # Track encounter statistic
            if wild.id not in species_stats:
                species_stats[wild.id] = {
                    "encountered": 0,
                    "defeated": 0,
                    "captured": 0,
                    "shiny_encountered": 0,
                    "shiny_defeated": 0,
                    "shiny_captured": 0,
                }
            species_stats[wild.id]["encountered"] += 1
            if is_shiny:
                species_stats[wild.id]["shiny_encountered"] += 1

            # Calculate enemy HP and damage
            enemy_type1 = PokemonType(wild.type1)
            enemy_type2 = PokemonType(wild.type2) if wild.type2 else PokemonType.NONE

            party_attack = BattleService.calculate_party_attack(
                party_data, enemy_type1, enemy_type2
            )

            # Check if can defeat
            can_defeat = BattleService.can_defeat_enemy(base_health, party_attack)

            if can_defeat:
                pokemon_defeated += 1
                species_stats[wild.id]["defeated"] += 1
                if is_shiny:
                    species_stats[wild.id]["shiny_defeated"] += 1

                # Money and exp
                money = BattleService.calculate_route_money(route_number, region)
                exp = ExpService.calculate_battle_exp(wild.base_exp, route_number * 2, len(party))
                total_money += money
                total_exp += exp

                # Attempt catch
                is_new = wild.id not in owned_ids
                pokeball = CatchService.get_pokeball_for_pokemon(
                    settings.to_dict(), is_new, is_shiny
                )

                catch_result = CatchService.attempt_catch(wild.catch_rate, pokeball)

                if catch_result.success:
                    caught_pokemon.append((wild.name, wild.id, is_shiny))
                    species_stats[wild.id]["captured"] += 1
                    if is_shiny:
                        shiny_count += 1
                        species_stats[wild.id]["shiny_captured"] += 1

                    # Add EP if re-catching existing Pokemon
                    if not is_new and wild.id in owned_pokemon_map:
                        existing_pokemon = owned_pokemon_map[wild.id]
                        existing_pokemon.gain_effort_points(BASE_EP_YIELD, shiny=is_shiny)

                    # Collect new Pokemon for bulk create later (avoid DB call in loop)
                    if is_new:
                        new_pokemon_to_create.append(
                            {"user": user, "pokemon_data": wild, "shiny": is_shiny}
                        )
                        owned_ids.add(wild.id)  # Track to avoid duplicates in same batch

        # Bulk create new Pokemon outside the loop
        if new_pokemon_to_create:
            await PlayerPokemon.bulk_create(
                [PlayerPokemon(**data) for data in new_pokemon_to_create], ignore_conflicts=True
            )

        # Update per-species statistics for owned Pokemon
        pokemon_to_update_stats: list[PlayerPokemon] = []
        for pokemon_id, stats in species_stats.items():
            if pokemon_id in owned_pokemon_map:
                poke = owned_pokemon_map[pokemon_id]
                poke.stat_encountered += stats["encountered"]
                poke.stat_defeated += stats["defeated"]
                poke.stat_captured += stats["captured"]
                poke.stat_shiny_encountered += stats["shiny_encountered"]
                poke.stat_shiny_defeated += stats["shiny_defeated"]
                poke.stat_shiny_captured += stats["shiny_captured"]
                pokemon_to_update_stats.append(poke)

        if pokemon_to_update_stats:
            await PlayerPokemon.bulk_update(
                pokemon_to_update_stats,
                fields=[
                    "effort_points",
                    "pokerus",  # EP and Pokerus from gain_effort_points()
                    "stat_encountered",
                    "stat_defeated",
                    "stat_captured",
                    "stat_shiny_encountered",
                    "stat_shiny_defeated",
                    "stat_shiny_captured",
                ],
            )

        # Update wallet
        if total_money > 0:
            await wallet.add_pokedollar(total_money)

        # Distribute exp to all party Pokemon
        if total_exp > 0:
            exp_per_pokemon = total_exp // len(party)
            for poke in party:
                level_result = ExpService.add_exp_and_level_up(
                    poke.level, poke.exp, exp_per_pokemon
                )
                poke.level = level_result.new_level
                poke.exp = level_result.exp_remaining

            # Bulk update party Pokemon levels
            await PlayerPokemon.bulk_update(party, fields=["level", "exp"])

        # Update route progress (kills)
        if pokemon_defeated > 0:
            progress, _ = await PlayerRouteProgress.get_or_create(user_id=user.id, route=route_data)
            progress.kills += pokemon_defeated
            await progress.save()

            # Progress hatchery eggs (steps = sqrt(normalized_route) per defeat)
            # normalized_route = order_number, not route number (per Pokeclicker Routes.normalizedNumber)
            hatchery_steps = (
                HatcheryService.calculate_steps_from_route(route_data.order_number)
                * pokemon_defeated
            )
            await HatcheryService.progress_eggs(user, hatchery_steps)

        return ExploreResult(
            route=route_number,
            region=region,
            encounter_count=count,
            pokemon_defeated=pokemon_defeated,
            pokemon_caught=len(caught_pokemon),
            shiny_count=shiny_count,
            total_money=total_money,
            total_exp=total_exp,
            caught_pokemon=caught_pokemon,
        )

    def _create_result_view(
        self, username: str, route_data: RouteData, results: ExploreResult
    ) -> LayoutView:
        """Create V2 LayoutView for explore results."""
        # Determine color based on catch success
        color = discord.Color.green() if results.caught_pokemon else discord.Color.blue()

        # Build content lines
        lines = [
            f"## 🗺️ {route_data.name} 探索結果",
            "",
            f"⚔️ 擊敗: **{results.pokemon_defeated}** 隻寶可夢",
            f"💰 獲得: **{results.total_money:,}** PokeDollar",
            f"⭐ 經驗: **+{results.total_exp:,}** EXP (全隊)",
        ]

        # Catch results
        if results.caught_pokemon:
            caught_names = [f"{'✨' if s else ''}{name}" for name, _, s in results.caught_pokemon]
            lines.extend(
                [f"🎯 捕獲: **{results.pokemon_caught}** 隻", f"   {', '.join(caught_names[:5])}"]
            )
            if len(caught_names) > 5:
                lines.append(f"   ...還有 {len(caught_names) - 5} 隻")
        else:
            lines.append("🎯 捕獲: 0 隻")

        if results.shiny_count > 0:
            lines.append(f"✨ 異色: **{results.shiny_count}** 隻！")

        lines.append(f"\n-# 探索者: {username}")

        # Create view
        view = LayoutView()
        container = Container(TextDisplay("\n".join(lines)), accent_color=color)
        view.add_item(container)

        return view


async def setup(bot: FunBot) -> None:
    """Add cog to bot."""
    await bot.add_cog(ExploreCog(bot))
