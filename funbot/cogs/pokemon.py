"""Pokemon Cog - All Pokemon commands consolidated.

Commands are organized under the /pokemon group:
- /pokemon start - Select your starter Pokemon
- /pokemon explore - Explore routes and catch wild Pokemon
- /pokemon party - View your Pokemon party
- /pokemon shop - Purchase Pokeballs
- /pokemon pokeballs - Configure catch settings
- /pokemon hatchery list/add/hatch - Manage breeding
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands

from funbot.db.models.pokemon import (
    PlayerPokeballSettings,
    PlayerPokemon,
    PlayerWallet,
    PokemonData,
)
from funbot.db.models.pokemon.player_ball_inventory import PlayerBallInventory
from funbot.db.models.pokemon.route_data import RouteData
from funbot.db.models.user import User
from funbot.pokemon.autocomplete import gym_autocomplete, region_autocomplete, route_autocomplete
from funbot.pokemon.constants.enums import Pokeball, Region
from funbot.pokemon.constants.game_constants import DEFAULT_STARTER_REGION, STARTERS
from funbot.pokemon.services.battle_service import BattleService
from funbot.pokemon.services.catch_service import CatchService
from funbot.pokemon.services.exp_service import ExpService
from funbot.pokemon.services.gym_service import GymService
from funbot.pokemon.services.hatchery_service import HatcheryService
from funbot.pokemon.services.route_service import get_route_status_service
from funbot.pokemon.services.shop_service import ShopService
from funbot.pokemon.ui_utils import Emoji, get_type_emoji
from funbot.pokemon.views.explore_views import ExploreResult, ExploreResultView
from funbot.pokemon.views.gym_views import GymBattleView, GymListView
from funbot.pokemon.views.hatchery_views import HatcheryListView
from funbot.pokemon.views.party_views import PartyPaginatorView
from funbot.pokemon.views.pokeball_views import PokeballSettingsLayout
from funbot.pokemon.views.shop_views import ShopView
from funbot.pokemon.views.starter_views import StarterSelectLayout

if TYPE_CHECKING:
    from funbot.bot import FunBot
    from funbot.types import Interaction


@dataclass
class EncounterData:
    """Data for a single encounter during explore."""

    pokemon: PokemonData
    is_shiny: bool = False
    is_new: bool = False
    caught: bool = False
    ball_used: int = 0


class PokemonCog(commands.Cog, name="Pokemon"):
    """All Pokemon commands consolidated into single cog."""

    def __init__(self, bot: FunBot) -> None:
        self.bot = bot
        self._route_service = get_route_status_service()

    # ═══════════════════════════════════════════════════════════════════════
    # COMMAND GROUP
    # ═══════════════════════════════════════════════════════════════════════

    pokemon = app_commands.Group(name="pokemon", description="寶可夢指令")
    hatchery = app_commands.Group(name="hatchery", parent=pokemon, description="孵化場指令")

    # ═══════════════════════════════════════════════════════════════════════
    # /pokemon start
    # ═══════════════════════════════════════════════════════════════════════

    @pokemon.command(name="start", description="選擇你的初始寶可夢")
    async def start(self, interaction: Interaction) -> None:
        """Select your starter Pokemon."""
        await interaction.response.defer()

        # Get or create user
        user, _ = await User.get_or_create(id=interaction.user.id)

        # Check if user already has Pokemon
        existing_count = await PlayerPokemon.filter(user=user).count()
        if existing_count > 0:
            await interaction.followup.send(
                f"{Emoji.CROSS} 你已經有寶可夢了！使用 `/pokemon party` 查看你的隊伍。",
                ephemeral=True,
            )
            return

        # Get starter Pokemon data
        starter_ids = STARTERS[DEFAULT_STARTER_REGION]
        starters = await PokemonData.filter(id__in=starter_ids)

        if not starters:
            await interaction.followup.send(
                f"{Emoji.CROSS} 寶可夢資料尚未匯入，請先執行資料匯入腳本。", ephemeral=True
            )
            return

        # Create V2 layout with starter selection
        view = StarterSelectLayout(
            starters=list(starters), user=user, discord_user_id=interaction.user.id
        )

        await interaction.followup.send(view=view)

    # ═══════════════════════════════════════════════════════════════════════
    # /pokemon party
    # ═══════════════════════════════════════════════════════════════════════

    @pokemon.command(name="party", description="查看你的寶可夢隊伍")
    async def party(self, interaction: Interaction) -> None:
        """Display all owned Pokemon."""
        await interaction.response.defer()

        # Get user
        user = await User.get_or_none(id=interaction.user.id)
        if not user:
            await interaction.followup.send(
                f"{Emoji.CROSS} 你還沒有開始寶可夢之旅！使用 `/pokemon start` 選擇初始寶可夢。",
                ephemeral=True,
            )
            return

        # Get all Pokemon
        pokemon_list = await PlayerPokemon.filter(user=user).prefetch_related("pokemon_data")

        if not pokemon_list:
            await interaction.followup.send(
                f"{Emoji.CROSS} 你還沒有任何寶可夢！使用 `/pokemon start` 選擇初始寶可夢。",
                ephemeral=True,
            )
            return

        # Sort by Pokemon ID
        sorted_pokemon = sorted(pokemon_list, key=lambda p: p.pokemon_data.id)

        # Calculate total attack
        total_attack = sum(
            ExpService.calculate_attack_from_level(p.pokemon_data.base_attack, p.level)
            for p in sorted_pokemon
        )

        # Build the paginator view
        view = PartyPaginatorView(
            pokemon_list=sorted_pokemon,
            username=interaction.user.display_name,
            total_attack=total_attack,
            author=interaction.user,
        )

        await view.start(interaction)

    # ═══════════════════════════════════════════════════════════════════════
    # /pokemon shop
    # ═══════════════════════════════════════════════════════════════════════

    @pokemon.command(name="shop", description="寶貝球商店 - 購買寶貝球")
    async def shop(self, interaction: Interaction) -> None:
        """Open the Poké Mart shop."""
        await interaction.response.defer()

        # Get user
        user = await User.get_or_none(id=interaction.user.id)
        if not user:
            await interaction.followup.send(
                f"{Emoji.CROSS} 你還沒有開始寶可夢之旅！使用 `/pokemon start` 選擇初始寶可夢。",
                ephemeral=True,
            )
            return

        # Get shop data
        shop_data = await ShopService.get_shop_inventory(user)
        inventory, _ = await PlayerBallInventory.get_or_create(user=user)

        # Create beautiful V2 shop view
        view = ShopView(user, shop_data["wallet"], inventory)

        await interaction.followup.send(view=view)

    # ═══════════════════════════════════════════════════════════════════════
    # /pokemon pokeballs
    # ═══════════════════════════════════════════════════════════════════════

    @pokemon.command(name="pokeballs", description="設定自動捕捉的寶貝球")
    async def pokeballs(self, interaction: Interaction) -> None:
        """View and edit Pokeball settings."""
        await interaction.response.defer()

        # Get user
        user = await User.get_or_none(id=interaction.user.id)
        if not user:
            await interaction.followup.send(
                f"{Emoji.CROSS} 你還沒有開始寶可夢之旅！使用 `/pokemon start` 選擇初始寶可夢。",
                ephemeral=True,
            )
            return

        # Get or create settings
        settings, _ = await PlayerPokeballSettings.get_or_create(user=user)

        # Create V2 layout
        view = PokeballSettingsLayout(settings, interaction.user.id)

        await interaction.followup.send(view=view)

    # ═══════════════════════════════════════════════════════════════════════
    # /pokemon explore
    # ═══════════════════════════════════════════════════════════════════════

    @pokemon.command(name="explore", description="探索路線並捕捉野生寶可夢")
    @app_commands.describe(region="地區編號 (0=關都)", route="路線編號", count="探索次數 (1-100)")
    @app_commands.autocomplete(region=region_autocomplete, route=route_autocomplete)
    async def explore(
        self, interaction: Interaction, region: int = 0, route: int = 0, count: int = 1
    ) -> None:
        """Explore a route and encounter wild Pokemon."""
        await interaction.response.defer()

        # Validate count
        count = max(1, min(100, count))

        # Get user and validate
        user = await User.get_or_none(id=interaction.user.id)
        if not user:
            await interaction.followup.send(
                f"{Emoji.CROSS} 你還沒有開始寶可夢之旅！使用 `/pokemon start` 選擇初始寶可夢。",
                ephemeral=True,
            )
            return

        # Get route data
        route_data = await RouteData.filter(region=region, number=route).first()
        if not route_data:
            await interaction.followup.send(
                f"{Emoji.CROSS} 找不到路線。請確認地區和路線編號。", ephemeral=True
            )
            return

        # Check route unlock status
        status, _kills = await self._route_service.get_route_status(user.id, route_data)
        if status.name == "LOCKED":
            hints = await self._route_service.get_requirement_hints(user.id, route_data)
            await interaction.followup.send(
                f"{Emoji.CROSS} 此路線尚未解鎖。\n需求: {', '.join(hints) if hints else '未知'}",
                ephemeral=True,
            )
            return

        # Get player's party
        party = await PlayerPokemon.filter(user=user).prefetch_related("pokemon_data")
        if not party:
            await interaction.followup.send(f"{Emoji.CROSS} 你沒有任何寶可夢！", ephemeral=True)
            return

        # Get route Pokemon
        wild_pokemon = await self._get_route_pokemon(route_data)
        if not wild_pokemon:
            await interaction.followup.send(f"{Emoji.CROSS} 此路線沒有野生寶可夢。", ephemeral=True)
            return

        # Get settings and resources
        settings, _ = await PlayerPokeballSettings.get_or_create(user=user)
        wallet, _ = await PlayerWallet.get_or_create(user=user)
        ball_inventory, _ = await PlayerBallInventory.get_or_create(user=user)

        # Run simulation
        results = await self._simulate_encounters(
            user=user,
            party=list(party),
            settings=settings,
            wallet=wallet,
            ball_inventory=ball_inventory,
            route_data=route_data,
            wild_pokemon=wild_pokemon,
            count=count,
        )

        # Progress eggs
        steps = HatcheryService.calculate_steps_from_route(route_data.order_number)
        await HatcheryService.progress_eggs(user, int(steps * count))

        # Create result view
        view = ExploreResultView(interaction.user.display_name, route_data, results)
        await interaction.followup.send(view=view)

    async def _get_route_pokemon(self, route_data: RouteData) -> list[PokemonData]:
        """Get Pokemon available on a route."""
        pokemon_ids = set()

        if route_data.land_pokemon:
            pokemon_ids.update(route_data.land_pokemon)
        if route_data.water_pokemon:
            pokemon_ids.update(route_data.water_pokemon)
        if route_data.headbutt_pokemon:
            pokemon_ids.update(route_data.headbutt_pokemon)

        if not pokemon_ids:
            return []

        return list(await PokemonData.filter(id__in=pokemon_ids))

    async def _simulate_encounters(
        self,
        user: User,
        party: list[PlayerPokemon],
        settings: PlayerPokeballSettings,
        wallet: PlayerWallet,
        ball_inventory: PlayerBallInventory,
        route_data: RouteData,
        wild_pokemon: list[PokemonData],
        count: int,
    ) -> ExploreResult:
        """Simulate multiple encounters."""
        total_exp = 0
        total_money = 0
        pokedex_new: list[str] = []
        shiny_caught: list[str] = []
        already_caught = 0
        failed_catches = 0
        balls_used: dict[int, int] = {}

        # Get owned Pokemon IDs for "new" detection
        owned_ids = {p.pokemon_data.id for p in party}

        for _ in range(count):
            # Pick random wild Pokemon
            wild = random.choice(wild_pokemon)

            # Calculate battle rewards (simplified - use route-based money)
            party_attack = sum(p.calculate_attack(p.pokemon_data.base_attack) for p in party)
            _ticks = BattleService.calculate_ticks_to_defeat(wild.base_hp, party_attack)
            money_earned = BattleService.calculate_route_money(route_data.number, route_data.region)
            exp_earned = wild.base_hp // 10  # Simplified EXP

            # Add rewards
            total_exp += exp_earned
            total_money += money_earned

            # Determine shiny
            is_shiny = random.random() < 1 / 8192
            is_new = wild.id not in owned_ids

            # Determine which ball to use
            if is_new and is_shiny:
                preferred_ball = settings.new_shiny
            elif is_new:
                preferred_ball = settings.new_pokemon
            elif is_shiny:
                preferred_ball = settings.caught_shiny
            else:
                preferred_ball = settings.caught_pokemon

            if preferred_ball == Pokeball.NONE:
                continue

            # Find available ball (fallback to lower tier)
            actual_ball = None
            for ball_type in [
                preferred_ball,
                Pokeball.ULTRABALL,
                Pokeball.GREATBALL,
                Pokeball.POKEBALL,
            ]:
                if ball_type <= preferred_ball and ball_inventory.get_quantity(ball_type) > 0:
                    actual_ball = ball_type
                    break

            if actual_ball is None:
                failed_catches += 1
                continue

            # Attempt catch
            catch_result = CatchService.attempt_catch(255, actual_ball)  # Use max catch rate
            catch_success = catch_result.success

            if catch_success:
                # Track ball usage
                balls_used[actual_ball] = balls_used.get(actual_ball, 0) + 1
                await ball_inventory.use_ball(actual_ball)

                if is_new:
                    pokedex_new.append(wild.name)
                    owned_ids.add(wild.id)
                    # Create new Pokemon record
                    await PlayerPokemon.create(user=user, pokemon_data=wild, shiny=is_shiny)
                else:
                    already_caught += 1

                if is_shiny:
                    shiny_caught.append(wild.name)
            else:
                failed_catches += 1
                # Still consume ball on failure
                balls_used[actual_ball] = balls_used.get(actual_ball, 0) + 1
                await ball_inventory.use_ball(actual_ball)

        # Update wallet
        wallet.pokedollar += total_money
        await wallet.save(update_fields=["pokedollar"])

        # Update party EXP (simplified - just add some levels based on EXP)
        exp_per_pokemon = total_exp // len(party) if party else 0
        for poke in party:
            # Add EXP and level up
            level_result = ExpService.add_exp_and_level_up(poke.level, 0, exp_per_pokemon)
            if level_result.leveled_up:
                poke.level = level_result.new_level
                await poke.save(update_fields=["level"])

        return ExploreResult(
            total_exp=total_exp,
            total_money=total_money,
            pokedex_new=pokedex_new,
            shiny_caught=shiny_caught,
            already_caught=already_caught,
            failed_catches=failed_catches,
            total_encounters=count,
            total_battles=count,
            balls_used=balls_used,
        )

    # ═══════════════════════════════════════════════════════════════════════
    # /pokemon gym
    # ═══════════════════════════════════════════════════════════════════════

    @pokemon.command(name="gym", description="挑戰道館")
    @app_commands.describe(
        region="地區", gym_name="道館名稱 (留空顯示列表)", animated="是否顯示即時戰鬥動畫"
    )
    @app_commands.autocomplete(region=region_autocomplete, gym_name=gym_autocomplete)  # pyright: ignore[reportArgumentType]
    async def gym(
        self,
        interaction: Interaction,
        region: int = 0,
        gym_name: str | None = None,
        animated: bool = True,
    ) -> None:
        """Challenge a gym leader."""
        await interaction.response.defer()

        user_id = interaction.user.id

        # If no gym specified, show list
        if not gym_name:
            gyms = await GymService.get_available_gyms(region)
            badges = await GymService.get_player_badges(user_id)
            # Get region display name from enum
            try:
                region_enum = Region(region)
                region_name = f"{region_enum.name.title()}"
            except ValueError:
                region_name = "Unknown"
            view = GymListView(gyms, badges, region_name)
            await interaction.followup.send(view=view)
            return

        # Find the gym
        gym = await GymService.get_gym_by_name(gym_name)
        if not gym:
            await interaction.followup.send(f"{Emoji.CROSS} 找不到道館: {gym_name}", ephemeral=True)
            return

        # Start battle
        state = await GymService.start_battle(user_id, gym)
        view = GymBattleView(user_id, gym, state)

        if animated:
            # Run with animation (updates every second)
            await view.run_battle(interaction)
        else:
            # Instant result
            await view.run_instant(interaction)

    # ═══════════════════════════════════════════════════════════════════════
    # /pokemon hatchery list
    # ═══════════════════════════════════════════════════════════════════════

    @hatchery.command(name="list", description="查看孵化場中的蛋")
    async def hatchery_list(self, interaction: Interaction) -> None:
        """View all eggs in hatchery."""
        await interaction.response.defer()

        user, _ = await User.get_or_create(id=interaction.user.id)
        eggs = await HatcheryService.get_eggs(user)
        slots = await HatcheryService.get_egg_slots(user)

        view = HatcheryListView(eggs, slots, interaction.user.display_name)
        await interaction.followup.send(view=view)

    # ═══════════════════════════════════════════════════════════════════════
    # /pokemon hatchery add
    # ═══════════════════════════════════════════════════════════════════════

    @hatchery.command(name="add", description="將寶可夢加入孵化場")
    @app_commands.describe(pokemon_name="要繁殖的寶可夢名稱")
    async def hatchery_add(self, interaction: Interaction, pokemon_name: str) -> None:
        """Add a Pokemon to the hatchery."""
        await interaction.response.defer()

        user, _ = await User.get_or_create(id=interaction.user.id)

        # Find Pokemon by name
        pokemon_data = await PokemonData.filter(name__icontains=pokemon_name).first()
        if not pokemon_data:
            await interaction.followup.send(
                f"{Emoji.CROSS} 找不到名為 `{pokemon_name}` 的寶可夢", ephemeral=True
            )
            return

        # Check if user owns this Pokemon
        player_pokemon = await PlayerPokemon.filter(user=user, pokemon_data=pokemon_data).first()
        if not player_pokemon:
            await interaction.followup.send(
                f"{Emoji.CROSS} 你沒有 **{pokemon_data.name}**！", ephemeral=True
            )
            return

        # Check if already breeding
        if player_pokemon.breeding:
            await interaction.followup.send(
                f"{Emoji.CROSS} **{pokemon_data.name}** 已經在孵化場中！", ephemeral=True
            )
            return

        # Try to add to hatchery
        egg = await HatcheryService.add_to_hatchery(user, player_pokemon, pokemon_data)
        if not egg:
            await interaction.followup.send(
                f"{Emoji.CROSS} 孵化場已滿！請先孵化現有的蛋。", ephemeral=True
            )
            return

        type_emoji = get_type_emoji(pokemon_data.type1)
        await interaction.followup.send(
            f"{Emoji.CHECK} {type_emoji} **{pokemon_data.name}** 已加入孵化場！\n"
            f"-# 需要 {egg.steps_required:,} 步驟孵化。使用 `/pokemon explore` 累積步數。"
        )

    # ═══════════════════════════════════════════════════════════════════════
    # /pokemon hatchery hatch
    # ═══════════════════════════════════════════════════════════════════════

    @hatchery.command(name="hatch", description="孵化所有已完成的蛋")
    async def hatchery_hatch(self, interaction: Interaction) -> None:
        """Hatch all ready eggs."""
        await interaction.response.defer()

        user, _ = await User.get_or_create(id=interaction.user.id)
        results = await HatcheryService.hatch_all_ready(user)

        if not results:
            await interaction.followup.send(f"{Emoji.CROSS} 沒有已準備好孵化的蛋！", ephemeral=True)
            return

        # Build result message
        lines = [f"# {Emoji.EGG} 孵化結果"]
        for result in results:
            shiny_mark = Emoji.SHINY if result.shiny else ""
            pokerus_mark = f" {Emoji.POKERUS} **Pokerus 升級！**" if result.pokerus_upgraded else ""
            lines.append(
                f"- {shiny_mark}**{result.pokemon_name}** +{result.attack_bonus_percent}% ATK{pokerus_mark}"
            )
        lines.append("\n-# 等級已重置為 Lv.1")

        await interaction.followup.send("\n".join(lines))


async def setup(bot: FunBot) -> None:
    """Add cog to bot."""
    await bot.add_cog(PokemonCog(bot))
