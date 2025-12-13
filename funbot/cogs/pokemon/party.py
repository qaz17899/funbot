"""Party display command.

/pokemon party - Display all owned Pokemon with stats.
Uses Discord Components V2 for modern UI.
"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from funbot.db.models.pokemon import PlayerPokemon, PokemonData
from funbot.db.models.user import User
from funbot.pokemon.services.exp_service import ExpService
from funbot.pokemon.ui_utils import get_type_emoji
from funbot.ui.components_v2 import (
    Container,
    LayoutView,
    Section,
    Separator,
    TextDisplay,
    Thumbnail,
)


class PartyCog(commands.Cog):
    """Commands for viewing party Pokemon."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="pokemon-party", description="查看你的寶可夢隊伍")
    async def pokemon_party(self, interaction: discord.Interaction) -> None:
        """Display all owned Pokemon."""
        await interaction.response.defer()

        # Get user
        user = await User.get_or_none(id=interaction.user.id)
        if not user:
            await interaction.followup.send(
                "❌ 你還沒有開始寶可夢之旅！使用 `/pokemon-start` 選擇初始寶可夢。", ephemeral=True
            )
            return

        # Get all Pokemon
        pokemon_list = await PlayerPokemon.filter(user=user).prefetch_related("pokemon_data")

        if not pokemon_list:
            await interaction.followup.send(
                "❌ 你還沒有任何寶可夢！使用 `/pokemon-start` 選擇初始寶可夢。", ephemeral=True
            )
            return

        # Build the V2 layout
        view = PartyLayoutView(
            pokemon_list=list(pokemon_list), username=interaction.user.display_name
        )

        await interaction.followup.send(view=view)


class PartyLayoutView(LayoutView):
    """V2 Layout for displaying party Pokemon."""

    def __init__(self, pokemon_list: list[PlayerPokemon], username: str) -> None:
        super().__init__(timeout=120)

        # Calculate stats and build content
        total_attack = 0
        pokemon_lines: list[str] = []

        for poke in sorted(pokemon_list, key=lambda p: p.pokemon_data.id):
            data: PokemonData = poke.pokemon_data  # type: ignore

            # Calculate attack
            attack = ExpService.calculate_attack_from_level(data.base_attack, poke.level)
            total_attack += attack

            # Format line
            shiny_mark = "✨" if poke.shiny else ""
            name = poke.nickname or data.name
            type_emoji = get_type_emoji(data.type1)

            pokemon_lines.append(
                f"{type_emoji} {shiny_mark}**{name}** Lv.{poke.level} | ATK: {attack}"
            )

        # Main container with accent color
        container = Container(accent_color=discord.Color.blue())

        # Header section with thumbnail
        first_pokemon = min(pokemon_list, key=lambda p: p.pokemon_data.id)
        sprite_url = first_pokemon.pokemon_data.sprite_url  # type: ignore

        if sprite_url:
            header = Section(
                TextDisplay(f"# 🎒 {username} 的寶可夢隊伍"), accessory=Thumbnail(sprite_url)
            )
        else:
            header = Section(TextDisplay(f"# 🎒 {username} 的寶可夢隊伍"))
        container.add_item(header)

        container.add_item(Separator(spacing=discord.SeparatorSpacing.small))

        # Pokemon list (limit to 15 for V2 character limit)
        display_lines = pokemon_lines[:15]
        container.add_item(TextDisplay("\n".join(display_lines)))

        if len(pokemon_lines) > 15:
            container.add_item(TextDisplay(f"-# ...還有 {len(pokemon_lines) - 15} 隻寶可夢"))

        container.add_item(Separator(spacing=discord.SeparatorSpacing.large, divider=True))

        # Stats section
        stats_text = (
            f"## 📊 隊伍統計\n寶可夢數量: **{len(pokemon_list)}**\n總攻擊力: **{total_attack:,}**"
        )
        container.add_item(TextDisplay(stats_text))

        self.add_item(container)


async def setup(bot: commands.Bot) -> None:
    """Add cog to bot."""
    await bot.add_cog(PartyCog(bot))
