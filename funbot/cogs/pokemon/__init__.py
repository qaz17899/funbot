# Pokemon Cogs
"""Discord commands for Pokemon system."""

from __future__ import annotations

from discord.ext import commands

from funbot.cogs.pokemon.explore import ExploreCog
from funbot.cogs.pokemon.party import PartyCog
from funbot.cogs.pokemon.pokeballs import PokeballsCog
from funbot.cogs.pokemon.starter import StarterCog


async def setup(bot: commands.Bot) -> None:
    """Load all Pokemon cogs."""
    await bot.add_cog(StarterCog(bot))
    await bot.add_cog(PartyCog(bot))
    await bot.add_cog(ExploreCog(bot))
    await bot.add_cog(PokeballsCog(bot))


__all__ = ["ExploreCog", "PartyCog", "PokeballsCog", "StarterCog", "setup"]
