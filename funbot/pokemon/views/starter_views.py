"""Starter Pokemon selection views.

UI components for the /pokemon start command.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import ui

from funbot.db.models.pokemon import PlayerPokemon, PlayerWallet, PokemonData
from funbot.db.models.pokemon.player_ball_inventory import PlayerBallInventory
from funbot.pokemon.constants import PokerusState
from funbot.pokemon.ui_utils import Emoji, get_type_emoji

if TYPE_CHECKING:
    from funbot.db.models.user import User
    from funbot.types import Interaction


class StarterSelect(ui.Select["StarterSelectLayout"]):
    """Select menu for choosing starter Pokemon."""

    def __init__(self, starters: list[PokemonData], user: User, discord_user_id: int) -> None:
        self.user = user
        self.discord_user_id = discord_user_id
        self.starters = starters

        # Build options
        options = [
            discord.SelectOption(
                label=s.name,
                value=str(s.id),
                emoji=get_type_emoji(s.type1),
                description=f"HP: {s.base_hp} | ATK: {s.base_attack}",
            )
            for s in sorted(starters, key=lambda p: p.id)
        ]

        super().__init__(placeholder="選擇一隻寶可夢...", options=options)

    async def callback(self, interaction: Interaction) -> None:
        """Handle starter selection."""
        # Verify it's the same user
        if interaction.user.id != self.discord_user_id:
            await interaction.response.send_message(
                f"{Emoji.CROSS} 這不是你的選擇！", ephemeral=True
            )
            return

        pokemon_id = int(self.values[0])
        pokemon_data = await PokemonData.get(id=pokemon_id)

        # TODO: Correct Pokerus trigger per Pokeclicker (KeyItems.ts:57-79)
        # - Original trigger: After clearing "Distortion World" dungeon (Sinnoh "A New World" quest)
        # - Original target: Kanto starter OR lowest ID Pokemon (fallback)
        # - Should also unlock "Contagious" Pokeball filter option
        # Current simplification: Starter gets CONTAGIOUS immediately since we lack dungeon system
        # Migrate when dungeon/quest system is implemented
        await PlayerPokemon.create(
            user=self.user,
            pokemon_data=pokemon_data,
            level=5,
            shiny=False,
            pokerus=PokerusState.CONTAGIOUS,  # TEMPORARY: Should be UNINFECTED until quest
        )

        # Create wallet and ball inventory for user
        await PlayerWallet.get_or_create(user=self.user)
        await PlayerBallInventory.get_or_create(user=self.user)

        # Create success view and edit message
        success_view = StarterSuccessLayout(pokemon_data)
        await interaction.response.edit_message(view=success_view)


class StarterSelectActionRow(ui.ActionRow["StarterSelectLayout"]):
    """ActionRow containing the starter select menu."""

    def __init__(self, starters: list[PokemonData], user: User, discord_user_id: int) -> None:
        super().__init__()
        self.add_item(StarterSelect(starters, user, discord_user_id))


class StarterSelectLayout(ui.LayoutView):
    """V2 LayoutView for starter Pokemon selection."""

    def __init__(self, starters: list[PokemonData], user: User, discord_user_id: int) -> None:
        super().__init__(timeout=120)

        sorted_starters = sorted(starters, key=lambda p: p.id)

        # Build container with header and starter info
        container = ui.Container(accent_color=discord.Color.blue())

        # Header
        container.add_item(ui.TextDisplay("# 🎮 選擇你的初始寶可夢！"))
        container.add_item(ui.TextDisplay("歡迎來到寶可夢世界！請選擇以下其中一隻作為你的夥伴："))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Starter sections with thumbnails
        for starter in sorted_starters:
            type_emoji = get_type_emoji(starter.type1)
            if starter.sprite_url:
                section = ui.Section(
                    ui.TextDisplay(f"### {type_emoji} {starter.name}"),
                    ui.TextDisplay(f"HP: {starter.base_hp} | ATK: {starter.base_attack}"),
                    accessory=ui.Thumbnail(starter.sprite_url),
                )
                container.add_item(section)
            else:
                container.add_item(ui.TextDisplay(f"### {type_emoji} {starter.name}"))
                container.add_item(
                    ui.TextDisplay(f"HP: {starter.base_hp} | ATK: {starter.base_attack}")
                )

        # Add action row with select menu
        container.add_item(StarterSelectActionRow(starters, user, discord_user_id))

        self.add_item(container)


class StarterSuccessLayout(ui.LayoutView):
    """V2 LayoutView for successful starter selection."""

    def __init__(self, pokemon: PokemonData) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_color=discord.Color.green())

        # Header with thumbnail
        if pokemon.sprite_url:
            header = ui.Section(
                ui.TextDisplay("# 🎉 恭喜！"),
                ui.TextDisplay(f"你選擇了 **{pokemon.name}** 作為你的夥伴！"),
                accessory=ui.Thumbnail(pokemon.sprite_url),
            )
            container.add_item(header)
        else:
            container.add_item(ui.TextDisplay("# 🎉 恭喜！"))
            container.add_item(ui.TextDisplay(f"你選擇了 **{pokemon.name}** 作為你的夥伴！"))

        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        container.add_item(
            ui.TextDisplay(
                "使用 `/pokemon party` 查看你的隊伍\n"
                "使用 `/pokemon explore` 探索路線捕捉更多寶可夢！"
            )
        )

        self.add_item(container)
