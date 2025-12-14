"""Pokeball settings command.

/pokemon pokeballs - View and edit auto-catch settings.
Uses Discord Components V2 with subclassing pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands, ui
from discord.ext import commands

from funbot.db.models.pokemon import PlayerPokeballSettings
from funbot.db.models.user import User
from funbot.pokemon.constants.enums import Pokeball
from funbot.pokemon.ui_utils import get_ball_emoji
from funbot.types import Interaction

if TYPE_CHECKING:
    from funbot.bot import FunBot


class PokeballsCog(commands.Cog):
    """Commands for managing Pokeball settings."""

    def __init__(self, bot: FunBot) -> None:
        self.bot = bot

    @app_commands.command(name="pokemon-pokeballs", description="設定自動捕捉的寶貝球")
    async def pokemon_pokeballs(self, interaction: Interaction) -> None:
        """View and edit Pokeball settings."""
        await interaction.response.defer()

        # Get user
        user = await User.get_or_none(id=interaction.user.id)
        if not user:
            await interaction.followup.send(
                "❌ 你還沒有開始寶可夢之旅！使用 `/pokemon-start` 選擇初始寶可夢。", ephemeral=True
            )
            return

        # Get or create settings
        settings, _ = await PlayerPokeballSettings.get_or_create(user=user)

        # Create V2 layout
        view = PokeballSettingsLayout(settings, interaction.user.id)

        await interaction.followup.send(view=view)


class PokeballSelect(ui.Select["PokeballSettingsLayout"]):
    """Select menu for choosing pokeball for a category."""

    def __init__(
        self, category: str, label: str, settings: PlayerPokeballSettings, discord_user_id: int
    ) -> None:
        self.category = category
        self.settings = settings
        self.discord_user_id = discord_user_id

        current_value = getattr(settings, category)

        options = [
            discord.SelectOption(
                label="不捕捉",
                value=str(Pokeball.NONE),
                emoji="❌",
                default=current_value == Pokeball.NONE,
            ),
            discord.SelectOption(
                label="Poké Ball",
                value=str(Pokeball.POKEBALL),
                emoji="🔴",
                default=current_value == Pokeball.POKEBALL,
            ),
            discord.SelectOption(
                label="Great Ball",
                value=str(Pokeball.GREATBALL),
                emoji="🔵",
                default=current_value == Pokeball.GREATBALL,
            ),
            discord.SelectOption(
                label="Ultra Ball",
                value=str(Pokeball.ULTRABALL),
                emoji="🟡",
                default=current_value == Pokeball.ULTRABALL,
            ),
            discord.SelectOption(
                label="Master Ball",
                value=str(Pokeball.MASTERBALL),
                emoji="🟣",
                default=current_value == Pokeball.MASTERBALL,
            ),
        ]

        super().__init__(placeholder=f"{label}...", options=options)

    async def callback(self, interaction: Interaction) -> None:
        """Handle pokeball selection."""
        if interaction.user.id != self.discord_user_id:
            await interaction.response.send_message("❌ 這不是你的設定！", ephemeral=True)
            return

        # Update the setting
        new_value = int(self.values[0])
        setattr(self.settings, self.category, new_value)
        await self.settings.save(update_fields=[self.category, "updated_at"])

        # Update the select menu defaults
        for option in self.options:
            option.default = int(option.value) == new_value

        # Rebuild the layout with updated settings
        layout = PokeballSettingsLayout(self.settings, self.discord_user_id)
        await interaction.response.edit_message(view=layout)


class PokeballSelectActionRow(ui.ActionRow["PokeballSettingsLayout"]):
    """ActionRow containing a pokeball select menu."""

    def __init__(
        self, category: str, label: str, settings: PlayerPokeballSettings, discord_user_id: int
    ) -> None:
        super().__init__()
        self.add_item(PokeballSelect(category, label, settings, discord_user_id))


class PokeballSettingsLayout(ui.LayoutView):
    """V2 LayoutView for editing Pokeball settings."""

    def __init__(self, settings: PlayerPokeballSettings, discord_user_id: int) -> None:
        super().__init__(timeout=120)
        self.settings = settings
        self.discord_user_id = discord_user_id

        # Build container
        container = ui.Container(accent_color=discord.Color.blue())

        # Header
        container.add_item(ui.TextDisplay("# ⚙️ 寶貝球設定"))
        container.add_item(ui.TextDisplay("設定各類寶可夢要使用的寶貝球："))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Category definitions
        categories = [
            ("new_shiny", "🆕✨ 新異色"),
            ("new_pokemon", "🆕 新寶可夢"),
            ("caught_shiny", "📦✨ 已有異色"),
            ("caught_pokemon", "📦 已有寶可夢"),
        ]

        # Setting sections with current values and select menus
        for key, name in categories:
            current_value = getattr(settings, key)
            ball_emoji = get_ball_emoji(current_value)
            ball_name = Pokeball(current_value).name.replace("_", " ").title()

            container.add_item(ui.TextDisplay(f"### {name}"))
            container.add_item(ui.TextDisplay(f"目前: {ball_emoji} {ball_name}"))
            container.add_item(PokeballSelectActionRow(key, name, settings, discord_user_id))

        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
        container.add_item(ui.TextDisplay("-# 選擇後會自動儲存"))

        self.add_item(container)


async def setup(bot: FunBot) -> None:
    """Add cog to bot."""
    await bot.add_cog(PokeballsCog(bot))
