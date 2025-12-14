"""Hatchery commands for breeding Pokemon.

/pokemon-hatchery add <pokemon> - Add Pokemon to hatchery
/pokemon-hatchery list - View eggs and progress
/pokemon-hatchery hatch - Hatch all ready eggs
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from funbot.db.models.pokemon import PlayerEgg, PlayerPokemon, PokemonData
from funbot.db.models.user import User
from funbot.pokemon.services.hatchery_service import HatcheryService
from funbot.pokemon.ui_utils import Emoji, get_type_emoji
from funbot.ui.components_v2 import Container, LayoutView, Separator, TextDisplay

if TYPE_CHECKING:
    from funbot.bot import FunBot
    from funbot.types import Interaction


class HatcheryCog(commands.Cog):
    """Commands for managing the Pokemon hatchery."""

    def __init__(self, bot: FunBot) -> None:
        self.bot = bot

    hatchery_group = app_commands.Group(name="pokemon-hatchery", description="孵化場指令")

    @hatchery_group.command(name="list", description="查看孵化場中的蛋")
    async def hatchery_list(self, interaction: Interaction) -> None:
        """View all eggs in hatchery."""
        await interaction.response.defer()

        user, _ = await User.get_or_create(id=interaction.user.id)
        eggs = await HatcheryService.get_eggs(user)
        slots = await HatcheryService.get_egg_slots(user)

        view = HatcheryListView(eggs, slots, interaction.user.display_name)
        await interaction.followup.send(view=view)

    @hatchery_group.command(name="add", description="將寶可夢加入孵化場")
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
            f"-# 需要 {egg.steps_required:,} 步驟孵化。使用 `/pokemon-explore` 累積步數。"
        )

    @hatchery_group.command(name="hatch", description="孵化所有已完成的蛋")
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


class HatcheryListView(LayoutView):
    """V2 LayoutView for hatchery display."""

    def __init__(self, eggs: list[PlayerEgg], slots: int, username: str) -> None:
        super().__init__(timeout=0)

        container = Container(accent_color=discord.Color.green())
        container.add_item(TextDisplay(f"# {Emoji.EGG} {username} 的孵化場"))
        container.add_item(TextDisplay(f"槽位: {len(eggs)}/{slots}"))
        container.add_item(Separator(spacing=discord.SeparatorSpacing.small))

        if not eggs:
            container.add_item(TextDisplay("*孵化場是空的*"))
            container.add_item(TextDisplay("-# 使用 `/pokemon-hatchery add <寶可夢>` 加入蛋"))
        else:
            for egg in eggs:
                data: PokemonData = egg.pokemon_data  # type: ignore
                type_emoji = get_type_emoji(data.type1)
                progress_bar = self._create_progress_bar(egg.progress)
                ready_mark = f" {Emoji.CHECK} 準備孵化！" if egg.can_hatch else ""

                container.add_item(
                    TextDisplay(f"**Slot {egg.slot + 1}**: {type_emoji} {data.name}{ready_mark}")
                )
                container.add_item(
                    TextDisplay(
                        f"-# {progress_bar} {egg.steps:,}/{egg.steps_required:,} ({egg.progress:.1f}%)"
                    )
                )

        self.add_item(container)

    @staticmethod
    def _create_progress_bar(progress: float, length: int = 10) -> str:
        """Create a text progress bar."""
        filled = int(progress / 100 * length)
        empty = length - filled
        return Emoji.PROGRESS * filled + Emoji.PROGRESS_EMPTY * empty


async def setup(bot: FunBot) -> None:
    """Add cog to bot."""
    await bot.add_cog(HatcheryCog(bot))
