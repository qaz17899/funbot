"""Type aliases and protocols for the bot."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import discord
    from discord import app_commands

    from funbot.bot.bot import FunBot

# Type aliases
type Interaction = discord.Interaction[FunBot]
type CommandTree = app_commands.CommandTree[FunBot]
type User = discord.User | discord.Member
