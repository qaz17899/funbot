"""Admin cog for bot administration commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from funbot.types import Interaction

if TYPE_CHECKING:
    from funbot.bot.bot import FunBot

__all__ = ("Admin", "setup")


class Admin(commands.Cog):
    """Administration commands for bot owners."""

    def __init__(self, bot: FunBot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: Interaction) -> None:
        """Check the bot's latency to Discord."""
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!", description=f"Latency: **{latency}ms**", color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sync", description="Sync application commands")
    @app_commands.default_permissions(administrator=True)
    async def sync_commands(self, interaction: Interaction) -> None:
        """Sync application commands to Discord."""
        await interaction.response.defer(ephemeral=True)

        synced = await self.bot.tree.sync()

        embed = discord.Embed(
            title="✅ Commands Synced",
            description=f"Synced **{len(synced)}** commands globally.",
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=embed)
        logger.info(f"Synced {len(synced)} commands globally")

    @app_commands.command(name="reload", description="Reload a cog")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(cog="The cog to reload")
    async def reload_cog(self, interaction: Interaction, cog: str) -> None:
        """Hot reload a cog without restarting the bot."""
        await interaction.response.defer(ephemeral=True)

        try:
            await self.bot.reload_extension(f"funbot.cogs.{cog}")
            embed = discord.Embed(
                title="✅ Cog Reloaded",
                description=f"Successfully reloaded `{cog}`",
                color=discord.Color.green(),
            )
            logger.info(f"Reloaded cog: {cog}")
        except commands.ExtensionError as e:
            embed = discord.Embed(
                title="❌ Reload Failed",
                description=f"Failed to reload `{cog}`: {e}",
                color=discord.Color.red(),
            )
            logger.error(f"Failed to reload cog {cog}: {e}")

        await interaction.followup.send(embed=embed)


async def setup(bot: FunBot) -> None:
    """Load the Admin cog."""
    await bot.add_cog(Admin(bot))
