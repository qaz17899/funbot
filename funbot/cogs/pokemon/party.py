"""Party display command.

/pokemon party - Display all owned Pokemon with stats.
Uses Discord Components V2 with PaginatorView for modern UI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from funbot.db.models.pokemon import PlayerPokemon, PokemonData
from funbot.db.models.user import User
from funbot.pokemon.services.exp_service import ExpService
from funbot.pokemon.ui_utils import Emoji, get_type_emoji
from funbot.types import Interaction
from funbot.ui.components_v2 import Container, Section, Separator, TextDisplay, Thumbnail
from funbot.ui.components_v2.paginator import PaginatorView

if TYPE_CHECKING:
    from funbot.bot import FunBot

# Pokemon per page
POKEMON_PER_PAGE = 8


class PartyCog(commands.Cog):
    """Commands for viewing party Pokemon."""

    def __init__(self, bot: FunBot) -> None:
        self.bot = bot

    @app_commands.command(name="pokemon-party", description="查看你的寶可夢隊伍")
    async def pokemon_party(self, interaction: Interaction) -> None:
        """Display all owned Pokemon."""
        await interaction.response.defer()

        # Get user
        user = await User.get_or_none(id=interaction.user.id)
        if not user:
            await interaction.followup.send(
                f"{Emoji.CROSS} 你還沒有開始寶可夢之旅！使用 `/pokemon-start` 選擇初始寶可夢。",
                ephemeral=True,
            )
            return

        # Get all Pokemon
        pokemon_list = await PlayerPokemon.filter(user=user).prefetch_related("pokemon_data")

        if not pokemon_list:
            await interaction.followup.send(
                f"{Emoji.CROSS} 你還沒有任何寶可夢！使用 `/pokemon-start` 選擇初始寶可夢。",
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


class PartyPaginatorView(PaginatorView):
    """Paginated party view with 8 Pokemon Sections per page."""

    def __init__(
        self,
        pokemon_list: list[PlayerPokemon],
        username: str,
        total_attack: int,
        author: discord.User | discord.Member,
    ) -> None:
        # Set instance attributes BEFORE super().__init__() because it calls _build_layout()
        self.pokemon_list = pokemon_list
        self.username = username
        self.total_attack = total_attack
        self._all_pokemon = pokemon_list

        # Calculate pages
        total_pokemon = len(pokemon_list)
        total_pages = (total_pokemon + POKEMON_PER_PAGE - 1) // POKEMON_PER_PAGE
        if total_pages == 0:
            total_pages = 1
        self._total_pages = total_pages  # Must be set before super().__init__()

        # Initialize with placeholder pages (we override the layout building)
        from funbot.ui.components_v2.paginator import Page

        pages = [Page() for _ in range(total_pages)]
        super().__init__(pages, author=author, timeout=300.0)

    def _build_layout(self) -> None:
        """Override to build custom layout with Sections."""
        self._rebuild_content()

        # Separator before buttons
        self.add_item(Separator(divider=False, spacing=discord.SeparatorSpacing.small))

        # Navigation buttons
        from funbot.ui.components_v2.paginator import NavigationRow

        self.nav_row = NavigationRow(self)
        self.add_item(self.nav_row)

    def _rebuild_content(self) -> None:
        """Build content container for current page."""
        # Remove existing container if any
        self.content_container = Container(accent_color=discord.Color.blue())

        # Header
        page_info = f"(第{self._current_page + 1}頁/共{self._total_pages}頁)"
        self.content_container.add_item(
            TextDisplay(f"# 🎒 {self.username} 的寶可夢隊伍 {page_info}")
        )
        self.content_container.add_item(Separator(spacing=discord.SeparatorSpacing.small))

        # Get Pokemon for current page
        start_idx = self._current_page * POKEMON_PER_PAGE
        end_idx = start_idx + POKEMON_PER_PAGE
        page_pokemon = self._all_pokemon[start_idx:end_idx]

        # Build Sections for each Pokemon
        for poke in page_pokemon:
            data: PokemonData = poke.pokemon_data  # type: ignore

            # Calculate attack with exact Pokeclicker formula
            total_attack = poke.calculate_attack(data.base_attack)

            # Format text
            shiny_mark = Emoji.SHINY if poke.shiny else ""
            pokerus_mark = Emoji.POKERUS if poke.has_pokerus else ""
            gender_mark = poke.gender_symbol
            name = poke.nickname or data.name
            type_emoji = get_type_emoji(data.type1)
            type2_emoji = get_type_emoji(data.type2) if data.type2 else ""

            # Line 1: Name with marks, Level, Attack
            line1 = f"**{shiny_mark}{name}** {gender_mark}{pokerus_mark} Lv.{poke.level} | ATK: {total_attack:,}"

            # Line 2: Types and EV info
            ev_info = f" | EVs: {poke.evs:.1f}" if poke.evs > 0 else ""
            line2 = f"-# {type_emoji}{type2_emoji}{ev_info}"

            # Line 3: Statistics (if any captures)
            stats_parts = []
            if poke.stat_captured > 0:
                stats_parts.append(f"捕捉: {poke.stat_captured}")
            if poke.stat_defeated > 0:
                stats_parts.append(f"擊敗: {poke.stat_defeated}")
            if poke.caught_at:
                caught_str = poke.caught_at.strftime("%Y/%m/%d")
                stats_parts.append(f"首捕: {caught_str}")
            line3 = f"-# 📊 {' | '.join(stats_parts)}" if stats_parts else ""

            # Create section with thumbnail if sprite available
            sprite_url = (
                data.sprite_shiny_url
                if (poke.shiny and not poke.hide_shiny_sprite)
                else data.sprite_url
            )
            if sprite_url:
                items = [TextDisplay(line1), TextDisplay(line2)]
                if line3:
                    items.append(TextDisplay(line3))
                section = Section(*items, accessory=Thumbnail(sprite_url))
                self.content_container.add_item(section)
            else:
                # No sprite - just text
                self.content_container.add_item(TextDisplay(line1))
                self.content_container.add_item(TextDisplay(line2))
                if line3:
                    self.content_container.add_item(TextDisplay(line3))

        # Footer with stats (on last page or all pages)
        self.content_container.add_item(Separator(spacing=discord.SeparatorSpacing.large))
        stats = f"-# 📊 總計: {len(self._all_pokemon)} 隻 | 總攻擊力: {self.total_attack:,}"
        self.content_container.add_item(TextDisplay(stats))

        # Add to view (at position 0)
        self.clear_items()
        self.add_item(self.content_container)

    async def update_page(self, interaction: Interaction) -> None:
        """Override to rebuild content on page change."""
        self._rebuild_content()

        # Re-add navigation
        self.add_item(Separator(divider=False, spacing=discord.SeparatorSpacing.small))
        self.nav_row.update_states(self._current_page, self.max_page)
        self.add_item(self.nav_row)

        await self.absolute_edit(interaction, view=self)


async def setup(bot: FunBot) -> None:
    """Add cog to bot."""
    await bot.add_cog(PartyCog(bot))
