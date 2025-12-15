"""Shop service for purchasing items.

Handles Pokeball purchases and other shop transactions.
Matches Pokeclicker's Shop.ts and PokeballItem.ts mechanics.

Note: All methods use player_id: int for consistency with other services.
"""

from __future__ import annotations

from dataclasses import dataclass

from funbot.db.models.pokemon.player_ball_inventory import PlayerBallInventory
from funbot.db.models.pokemon.player_wallet import PlayerWallet
from funbot.pokemon.constants.enums import Currency
from funbot.pokemon.constants.game_constants import POKEBALL_PRICES


@dataclass
class PurchaseResult:
    """Result of a purchase attempt.

    Contains pure data - View layer handles formatting with emojis.
    """

    success: bool
    message: str
    quantity: int = 0
    total_cost: int = 0
    new_balance: int = 0
    ball_type: int = 0  # For View to format ball name
    currency_type: int = 0  # For View to format currency emoji


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
    async def can_afford(
        player_id: int, ball_type: int, amount: int
    ) -> tuple[bool, int, int]:
        """Check if user can afford a purchase.

        Args:
            player_id: The player's user ID
            ball_type: Pokeball enum value
            amount: Number to purchase

        Returns:
            (can_afford, total_cost, current_balance)
        """
        price, currency_type = ShopService.get_ball_price(ball_type)
        total_cost = price * amount

        wallet, _ = await PlayerWallet.get_or_create(user_id=player_id)

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
    async def buy_pokeballs(
        player_id: int, ball_type: int, amount: int
    ) -> PurchaseResult:
        """Purchase Pokeballs.

        Matches Pokeclicker mechanics:
        - PokeballItem.gain() -> Pokeballs.gainPokeballs()
        - Currency deduction from wallet
        - Purchase statistics tracking

        Args:
            player_id: The player's user ID
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
        can_afford, total_cost, balance = await ShopService.can_afford(
            player_id, ball_type, amount
        )

        if not can_afford:
            _, currency_type = ShopService.get_ball_price(ball_type)
            # Return pure data - View layer handles formatting with emojis
            return PurchaseResult(
                success=False,
                message="資金不足",
                quantity=0,
                total_cost=total_cost,
                new_balance=balance,
                currency_type=currency_type,
            )

        # Deduct currency
        _, currency_type = ShopService.get_ball_price(ball_type)
        wallet, _ = await PlayerWallet.get_or_create(user_id=player_id)

        if currency_type == Currency.POKEDOLLAR:
            new_balance = await wallet.add_pokedollar(-total_cost)
        elif currency_type == Currency.QUEST_POINT:
            new_balance = await wallet.add_quest_point(-total_cost)
        else:
            new_balance = 0

        # Add balls to inventory
        inventory, _ = await PlayerBallInventory.get_or_create(user_id=player_id)
        await inventory.gain_balls(ball_type, amount, purchased=True)

        # Return pure data - View layer handles formatting
        return PurchaseResult(
            success=True,
            message="購買成功",
            quantity=amount,
            total_cost=total_cost,
            new_balance=new_balance,
            ball_type=ball_type,
            currency_type=currency_type,
        )

    @staticmethod
    async def get_shop_inventory(player_id: int) -> dict:
        """Get shop inventory with prices and user's current quantities.

        Args:
            player_id: The player's user ID

        Returns:
            Dict with ball info for shop display
        """
        wallet, _ = await PlayerWallet.get_or_create(user_id=player_id)
        inventory, _ = await PlayerBallInventory.get_or_create(user_id=player_id)

        shop_items = []
        for ball_type, (price, currency_type) in POKEBALL_PRICES.items():
            shop_items.append(
                {
                    "ball_type": ball_type,
                    # name removed - View layer uses get_pokeball_name()
                    "price": price,
                    "currency_type": currency_type,
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
