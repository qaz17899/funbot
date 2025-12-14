"""Player's Pokemon wallet for currencies.

Stores Pokemon-specific currencies separate from main bot currencies.
"""

from __future__ import annotations

from tortoise import fields
from tortoise.expressions import F
from tortoise.models import Model


class PlayerWallet(Model):
    """Pokemon currency wallet for a player.

    One wallet per user, created on first Pokemon interaction.
    """

    class Meta:
        table = "player_pokemon_wallet"

    id = fields.IntField(pk=True)

    # Owner reference (one-to-one)
    user = fields.OneToOneField(
        "models.User", related_name="pokemon_wallet", on_delete=fields.CASCADE
    )

    # Currencies
    pokedollar = fields.BigIntField(default=0, description="Main Pokemon currency")
    dungeon_token = fields.BigIntField(default=0, description="Dungeon exploration currency")
    battle_point = fields.BigIntField(default=0, description="Battle frontier currency")
    quest_point = fields.BigIntField(default=0, description="Quest reward currency")

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Wallet(id={self.id}, ¥{self.pokedollar:,})"

    async def add_pokedollar(self, amount: int) -> int:
        """Add pokedollar to wallet atomically.

        Uses F expression for atomic update to prevent race conditions.

        Args:
            amount: Amount to add (can be negative)

        Returns:
            New balance
        """
        # Atomic update using F expression
        await PlayerWallet.filter(id=self.id).update(pokedollar=F("pokedollar") + amount)
        # Refresh to get new value
        await self.refresh_from_db(fields=["pokedollar"])
        # Ensure non-negative
        if self.pokedollar < 0:
            await PlayerWallet.filter(id=self.id).update(pokedollar=0)
            self.pokedollar = 0
        return self.pokedollar

    async def add_dungeon_token(self, amount: int) -> int:
        """Add dungeon tokens to wallet atomically."""
        await PlayerWallet.filter(id=self.id).update(dungeon_token=F("dungeon_token") + amount)
        await self.refresh_from_db(fields=["dungeon_token"])
        if self.dungeon_token < 0:
            await PlayerWallet.filter(id=self.id).update(dungeon_token=0)
            self.dungeon_token = 0
        return self.dungeon_token
