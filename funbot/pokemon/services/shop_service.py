"""Shop service for purchasing items.

Handles Pokeball purchases and other shop transactions.
Matches Pokeclicker's Shop.ts and PokeballItem.ts mechanics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from funbot.db.models.pokemon.player_ball_inventory import PlayerBallInventory
from funbot.db.models.pokemon.player_wallet import PlayerWallet
from funbot.pokemon.constants.enums import Currency, Pokeball
from funbot.pokemon.constants.game_constants import POKEBALL_PRICES

if TYPE_CHECKING:
    from funbot.db.models.user import User


@dataclass
class PurchaseResult:
    """Result of a purchase attempt."""

    success: bool
    message: str
    quantity: int = 0
    total_cost: int = 0
    new_balance: int = 0


class ShopService:
    """Service for shop transactions.

    Matches Pokeclicker's shop mechanics:
    - Pokeball purchases (PokeballItem.ts)
    - Currency deduction (Wallet.ts)
    - Inventory updates (Pokeballs.ts:214-220)
    """

    @staticmethod
    def get_ball_price(ball_type: int) -> tuple[int, int]:
        """Get price and currency for a ball type.

        Args:
            ball_type: Pokeball enum value

        Returns:
            (price, currency_type) tuple
        """
        return POKEBALL_PRICES.get(ball_type, (0, 0))

    @staticmethod
    def get_ball_name(ball_type: int) -> str:
        """Get display name for a ball type."""
        names: dict[int, str] = {
            Pokeball.POKEBALL: "Poké Ball",
            Pokeball.GREATBALL: "Great Ball",
            Pokeball.ULTRABALL: "Ultra Ball",
            Pokeball.MASTERBALL: "Master Ball",
        }
        return names.get(ball_type, "Unknown Ball")

    @staticmethod
    async def can_afford(user: User, ball_type: int, amount: int) -> tuple[bool, int, int]:
        """Check if user can afford a purchase.

        Args:
            user: The user
            ball_type: Pokeball enum value
            amount: Number to purchase

        Returns:
            (can_afford, total_cost, current_balance)
        """
        price, currency_type = ShopService.get_ball_price(ball_type)
        total_cost = price * amount

        wallet, _ = await PlayerWallet.get_or_create(user=user)

        # Get current balance based on currency type
        if currency_type == Currency.POKEDOLLAR:
            balance = wallet.pokedollar
        elif currency_type == Currency.QUEST_POINT:
            balance = wallet.quest_point
        elif currency_type == Currency.DUNGEON_TOKEN:
            balance = wallet.dungeon_token
        elif currency_type == Currency.BATTLE_POINT:
            balance = wallet.battle_point
        else:
            balance = 0

        return balance >= total_cost, total_cost, balance

    @staticmethod
    async def buy_pokeballs(user: User, ball_type: int, amount: int) -> PurchaseResult:
        """Purchase Pokeballs.

        Matches Pokeclicker mechanics:
        - PokeballItem.gain() -> Pokeballs.gainPokeballs()
        - Currency deduction from wallet
        - Purchase statistics tracking

        Args:
            user: The user making the purchase
            ball_type: Pokeball enum value (1-4)
            amount: Number of balls to buy

        Returns:
            PurchaseResult with success/failure info
        """
        if ball_type not in POKEBALL_PRICES:
            return PurchaseResult(success=False, message="無效的寶貝球類型")

        if amount <= 0:
            return PurchaseResult(success=False, message="購買數量必須大於 0")

        # Check affordability
        can_afford, total_cost, balance = await ShopService.can_afford(user, ball_type, amount)

        if not can_afford:
            _price, currency_type = ShopService.get_ball_price(ball_type)
            currency_name = Currency(currency_type).name.replace("_", " ").title()
            return PurchaseResult(
                success=False,
                message=f"資金不足！需要 {total_cost:,} {currency_name}，你只有 {balance:,}",
            )

        # Deduct currency
        _, currency_type = ShopService.get_ball_price(ball_type)
        wallet, _ = await PlayerWallet.get_or_create(user=user)

        if currency_type == Currency.POKEDOLLAR:
            new_balance = await wallet.add_pokedollar(-total_cost)
        elif currency_type == Currency.QUEST_POINT:
            # Need to add quest_point method to wallet
            from tortoise.expressions import F

            await PlayerWallet.filter(id=wallet.id).update(
                quest_point=F("quest_point") - total_cost
            )
            await wallet.refresh_from_db(fields=["quest_point"])
            new_balance = wallet.quest_point
        else:
            new_balance = 0

        # Add balls to inventory
        inventory, _ = await PlayerBallInventory.get_or_create(user=user)
        await inventory.gain_balls(ball_type, amount, purchased=True)

        ball_name = ShopService.get_ball_name(ball_type)

        return PurchaseResult(
            success=True,
            message=f"成功購買 {amount} 個 {ball_name}！",
            quantity=amount,
            total_cost=total_cost,
            new_balance=new_balance,
        )

    @staticmethod
    async def get_shop_inventory(user: User) -> dict:
        """Get shop inventory with prices and user's current quantities.

        Returns:
            Dict with ball info for shop display
        """
        wallet, _ = await PlayerWallet.get_or_create(user=user)
        inventory, _ = await PlayerBallInventory.get_or_create(user=user)

        shop_items = []
        for ball_type, (price, currency_type) in POKEBALL_PRICES.items():
            shop_items.append(
                {
                    "ball_type": ball_type,
                    "name": ShopService.get_ball_name(ball_type),
                    "price": price,
                    "currency": Currency(currency_type).name,
                    "owned": inventory.get_quantity(ball_type),
                }
            )

        return {
            "items": shop_items,
            "wallet": {
                "pokedollar": wallet.pokedollar,
                "quest_point": wallet.quest_point,
                "dungeon_token": wallet.dungeon_token,
                "battle_point": wallet.battle_point,
            },
        }
