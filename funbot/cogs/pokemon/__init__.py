# Pokemon Cogs
"""Discord commands for Pokemon system."""

from __future__ import annotations

from typing import TYPE_CHECKING

from funbot.cogs.pokemon.explore import ExploreCog
from funbot.cogs.pokemon.hatchery import HatcheryCog
from funbot.cogs.pokemon.party import PartyCog
from funbot.cogs.pokemon.pokeballs import PokeballsCog
from funbot.cogs.pokemon.starter import StarterCog

if TYPE_CHECKING:
    from funbot.bot import FunBot


async def setup(bot: FunBot) -> None:
    """Load all Pokemon cogs."""
    await bot.add_cog(StarterCog(bot))
    await bot.add_cog(PartyCog(bot))
    await bot.add_cog(ExploreCog(bot))
    await bot.add_cog(PokeballsCog(bot))
    await bot.add_cog(HatcheryCog(bot))


__all__ = ["ExploreCog", "HatcheryCog", "PartyCog", "PokeballsCog", "StarterCog", "setup"]
