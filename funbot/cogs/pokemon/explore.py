"""Explore command for encountering wild Pokemon.

/pokemon explore <route> [count] - Encounter and battle wild Pokemon.
Results are calculated instantly, no interactive UI needed.
Uses Discord Components V2 for modern UI.
"""

from __future__ import annotations

import random

import discord
from discord import app_commands
from discord.ext import commands

from funbot.db.models.pokemon import (
    PlayerPokeballSettings,
    PlayerPokemon,
    PlayerWallet,
    PokemonData,
)
from funbot.db.models.user import User
from funbot.pokemon.constants.enums import PokemonType
from funbot.pokemon.services.battle_service import BattleService, ExploreResult
from funbot.pokemon.services.catch_service import CatchService
from funbot.pokemon.services.exp_service import ExpService
from funbot.ui.components_v2 import Container, LayoutView, TextDisplay


class ExploreCog(commands.Cog):
    """Commands for exploring routes and battling wild Pokemon."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="pokemon-explore", description="探索路線遇見野生寶可夢")
    @app_commands.describe(route="路線編號 (1-25 關都)", count="遭遇次數 (1-20)")
    async def pokemon_explore(
        self, interaction: discord.Interaction, route: int = 1, count: int = 1
    ) -> None:
        """Explore a route and encounter wild Pokemon."""
        await interaction.response.defer()

        # Validate inputs
        count = max(1, min(20, count))
        route = max(1, min(25, route))

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

        # Get pokeball settings
        settings, _ = await PlayerPokeballSettings.get_or_create(user=user)

        # Get wallet
        wallet, _ = await PlayerWallet.get_or_create(user=user)

        # Get available wild Pokemon for this route
        wild_pokemon = await self._get_route_pokemon(route)
        if not wild_pokemon:
            await interaction.followup.send("❌ 此路線暫無可遇見的寶可夢。", ephemeral=True)
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
            route=route,
            wild_pokemon=wild_pokemon,
            count=count,
        )

        # Create result view (V2)
        view = self._create_result_view(interaction.user.display_name, route, results)

        await interaction.followup.send(view=view)

    async def _get_route_pokemon(self, route: int) -> list[PokemonData]:
        """Get Pokemon available on a route.

        For now, uses a simple formula based on route number.
        Route 1 = low dex Pokemon, higher routes = higher dex.
        """
        # Simple mapping: route 1-5 gets dex 1-50, etc.
        min_dex = max(1, (route - 1) * 10 + 1)
        max_dex = min(151, route * 10 + 20)  # Cap at Gen 1 for now

        pokemon = await PokemonData.filter(
            id__gte=min_dex,
            id__lte=max_dex,
            evolves_from__isnull=True,  # Only base forms for wild
        ).limit(10)

        # If no Pokemon found, get any available
        if not pokemon:
            pokemon = await PokemonData.filter(id__lte=151).limit(10)

        return list(pokemon)

    async def _simulate_encounters(
        self,
        user: User,
        party: list[PlayerPokemon],
        party_data: list[dict],
        settings: PlayerPokeballSettings,
        wallet: PlayerWallet,
        route: int,
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

        owned_ids = {p.pokemon_data_id for p in party}

        # Collect new Pokemon to create in bulk after the loop
        new_pokemon_to_create: list[dict] = []

        for _ in range(count):
            # Pick random wild Pokemon
            wild = random.choice(wild_pokemon)
            is_shiny = CatchService.roll_shiny()

            # Calculate enemy HP and damage
            enemy_hp = BattleService.calculate_route_health(route, 0)
            enemy_type1 = PokemonType(wild.type1)
            enemy_type2 = PokemonType(wild.type2) if wild.type2 else PokemonType.NONE

            party_attack = BattleService.calculate_party_attack(
                party_data, enemy_type1, enemy_type2
            )

            # Check if can defeat
            can_defeat = BattleService.can_defeat_enemy(enemy_hp, party_attack)

            if can_defeat:
                pokemon_defeated += 1

                # Money and exp
                money = BattleService.calculate_route_money(route, 0)
                exp = ExpService.calculate_battle_exp(wild.base_exp, route * 2, len(party))
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
                    if is_shiny:
                        shiny_count += 1

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

        return ExploreResult(
            route=route,
            region=0,  # Kanto
            encounter_count=count,
            pokemon_defeated=pokemon_defeated,
            pokemon_caught=len(caught_pokemon),
            shiny_count=shiny_count,
            total_money=total_money,
            total_exp=total_exp,
            caught_pokemon=caught_pokemon,
        )

    def _create_result_view(self, username: str, route: int, results: ExploreResult) -> LayoutView:
        """Create V2 LayoutView for explore results."""
        # Determine color based on catch success
        color = discord.Color.green() if results.caught_pokemon else discord.Color.blue()

        # Build content lines
        lines = [
            f"## 🗺️ Route {route} 探索結果",
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
        view = LayoutView(timeout=None)
        container = Container(TextDisplay("\n".join(lines)), accent_color=color)
        view.add_item(container)

        return view


async def setup(bot: commands.Bot) -> None:
    """Add cog to bot."""
    await bot.add_cog(ExploreCog(bot))
