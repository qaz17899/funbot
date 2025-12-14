"""Pokemon Shop commands.

Provides shop interface for purchasing Pokeballs and other items.
Matches Pokeclicker's Poké Mart system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands, ui
from discord.ext import commands

from funbot.cogs.pokemon.pokeballs import get_ball_emoji
from funbot.db.models.pokemon.player_ball_inventory import PlayerBallInventory
from funbot.db.models.user import User
from funbot.pokemon.constants.enums import Currency, Pokeball
from funbot.pokemon.constants.game_constants import POKEBALL_PRICES
from funbot.pokemon.services.shop_service import ShopService
from funbot.pokemon.ui_utils import Emoji, get_currency_emoji
from funbot.types import Interaction
from funbot.ui.components_v2 import Container, Separator, TextDisplay

if TYPE_CHECKING:
    from funbot.bot import FunBot


class BuyBallModal(ui.Modal, title="購買寶貝球"):
    """Modal for inputting purchase quantity."""

    amount = ui.TextInput(
        label="購買數量", placeholder="輸入數量 (1-999)", min_length=1, max_length=3, default="10"
    )

    def __init__(self, user: User, ball_type: int) -> None:
        super().__init__()
        self.user = user
        self.ball_type = ball_type

    async def on_submit(self, interaction: Interaction) -> None:
        """Handle modal submission."""
        try:
            amount = int(self.amount.value)
        except ValueError:
            await interaction.response.send_message(
                f"{Emoji.CROSS} 請輸入有效的數字！", ephemeral=True
            )
            return

        if amount <= 0 or amount > 999:
            await interaction.response.send_message(
                f"{Emoji.CROSS} 購買數量必須在 1-999 之間！", ephemeral=True
            )
            return

        result = await ShopService.buy_pokeballs(self.user, self.ball_type, amount)

        if result.success:
            currency_emoji = get_currency_emoji("money")
            await interaction.response.send_message(
                f"{Emoji.CHECK} {result.message}\n"
                f"-# 花費: {currency_emoji} {result.total_cost:,} | 餘額: {currency_emoji} {result.new_balance:,}",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"{Emoji.CROSS} {result.message}", ephemeral=True
            )


class BuyBallButton(ui.Button["ShopView"]):
    """Button to buy a specific ball type."""

    def __init__(self, ball_type: int, user: User, row: int) -> None:
        ball_name = ShopService.get_ball_name(ball_type)
        price, currency_type = POKEBALL_PRICES.get(ball_type, (0, 0))
        currency_name = "¥" if currency_type == Currency.POKEDOLLAR else "QP"

        super().__init__(
            label=f"{ball_name} ({price:,} {currency_name})",
            style=discord.ButtonStyle.primary,
            emoji=get_ball_emoji(ball_type),
            row=row,
        )
        self.ball_type = ball_type
        self.user = user

    async def callback(self, interaction: Interaction) -> None:
        """Show purchase modal."""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                f"{Emoji.CROSS} 這不是你的商店！", ephemeral=True
            )
            return

        modal = BuyBallModal(self.user, self.ball_type)
        await interaction.response.send_modal(modal)


class ShopView(ui.View):
    """View with ball purchase buttons."""

    def __init__(self, user: User) -> None:
        super().__init__(timeout=300)
        self.user = user

        # Add buttons for each ball type
        for i, ball_type in enumerate(
            [Pokeball.POKEBALL, Pokeball.GREATBALL, Pokeball.ULTRABALL, Pokeball.MASTERBALL]
        ):
            self.add_item(BuyBallButton(ball_type, user, row=i))


class ShopCog(commands.Cog, name="Shop"):
    """Shop commands for purchasing items."""

    def __init__(self, bot: FunBot) -> None:
        self.bot = bot

    @app_commands.command(name="pokemon-shop", description="寶貝球商店 - 購買寶貝球")
    async def shop(self, interaction: Interaction) -> None:
        """Open the Poké Mart shop."""
        await interaction.response.defer()

        # Get user
        user = await User.get_or_none(id=interaction.user.id)
        if not user:
            await interaction.followup.send(
                f"{Emoji.CROSS} 你還沒有開始寶可夢之旅！使用 `/pokemon-start` 選擇初始寶可夢。",
                ephemeral=True,
            )
            return

        # Get shop data
        shop_data = await ShopService.get_shop_inventory(user)
        inventory, _ = await PlayerBallInventory.get_or_create(user=user)

        # Build V2 container
        container = Container(accent_color=discord.Color.blue())

        # Header
        container.add_item(TextDisplay("# 🏪 寶貝球商店"))
        container.add_item(Separator(spacing=discord.SeparatorSpacing.small))

        # Wallet section
        money_emoji = get_currency_emoji("money")
        wallet = shop_data["wallet"]
        container.add_item(
            TextDisplay(
                f"### 💰 錢包\n"
                f"{money_emoji} **{wallet['pokedollar']:,}** PokéDollar\n"
                f"🎯 **{wallet['quest_point']:,}** Quest Point"
            )
        )
        container.add_item(Separator(spacing=discord.SeparatorSpacing.small))

        # Inventory section
        container.add_item(TextDisplay("### 🎒 背包"))

        ball_lines = []
        for ball_type in [
            Pokeball.POKEBALL,
            Pokeball.GREATBALL,
            Pokeball.ULTRABALL,
            Pokeball.MASTERBALL,
        ]:
            ball_emoji = get_ball_emoji(ball_type)
            name = ShopService.get_ball_name(ball_type)
            qty = inventory.get_quantity(ball_type)
            ball_lines.append(f"{ball_emoji} {name}: **{qty}**")

        container.add_item(TextDisplay("\n".join(ball_lines)))
        container.add_item(Separator(spacing=discord.SeparatorSpacing.small))

        # Price list
        container.add_item(TextDisplay("### 📋 價目表"))

        price_lines = []
        for ball_type, (price, currency_type) in POKEBALL_PRICES.items():
            ball_emoji = get_ball_emoji(ball_type)
            name = ShopService.get_ball_name(ball_type)
            if currency_type == Currency.POKEDOLLAR:
                price_lines.append(f"{ball_emoji} {name}: {money_emoji} **{price:,}**")
            else:
                price_lines.append(f"{ball_emoji} {name}: 🎯 **{price:,}** QP")

        container.add_item(TextDisplay("\n".join(price_lines)))
        container.add_item(TextDisplay("-# 點擊下方按鈕購買"))

        # Create view with buttons
        view = ShopView(user)

        await interaction.followup.send(view=view)


async def setup(bot: FunBot) -> None:
    """Add the cog to the bot."""
    await bot.add_cog(ShopCog(bot))
