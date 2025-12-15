"""Shop views.

UI components for the /pokemon shop command.

Note: Views store player_id (int) instead of User objects to:
1. Avoid detached instance issues in async context
2. Match Service layer interface (player_id: int)
3. Ensure fresh data is fetched when needed
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import ui

from funbot.pokemon.constants.enums import Currency, Pokeball
from funbot.pokemon.services.shop_service import ShopService
from funbot.pokemon.ui_utils import Emoji, get_ball_emoji, get_currency_emoji, get_pokeball_name
from funbot.ui.components_v2 import Button, Container, LayoutView, Section, Separator, TextDisplay

if TYPE_CHECKING:
    from collections.abc import Callable

    from funbot.db.models.pokemon.player_ball_inventory import PlayerBallInventory
    from funbot.types import Interaction


class BuyBallModal(ui.Modal, title="購買寶貝球"):
    """Modal for inputting purchase quantity."""

    amount = ui.TextInput(
        label="購買數量",
        placeholder="輸入數量 (1-999)",
        min_length=1,
        max_length=3,
        default="10",
    )

    def __init__(
        self, player_id: int, ball_type: int, refresh_callback: Callable
    ) -> None:
        super().__init__()
        self.player_id = player_id
        self.ball_type = ball_type
        self.refresh_callback = refresh_callback

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

        result = await ShopService.buy_pokeballs(self.player_id, self.ball_type, amount)

        if result.success:
            # Format success message in View layer (Service returns pure data)
            ball_name = get_pokeball_name(result.ball_type)
            message = f"成功購買 {result.quantity} 個 {ball_name}！"
            await self.refresh_callback(interaction, message)
        else:
            # Format error message in View layer
            currency_emoji = get_currency_emoji(Currency(result.currency_type))
            error_msg = (
                f"資金不足！需要 {result.total_cost:,} {currency_emoji}，"
                f"你只有 {result.new_balance:,} {currency_emoji}"
            )
            await interaction.response.send_message(
                f"{Emoji.CROSS} {error_msg}", ephemeral=True
            )


class BuyBallButton(Button["ShopView"]):
    """Button to buy a specific ball type."""

    def __init__(self, ball_type: int, player_id: int) -> None:
        # Style based on ball tier
        styles = {
            Pokeball.POKEBALL: discord.ButtonStyle.secondary,
            Pokeball.GREATBALL: discord.ButtonStyle.primary,
            Pokeball.ULTRABALL: discord.ButtonStyle.success,
            Pokeball.MASTERBALL: discord.ButtonStyle.danger,
        }

        super().__init__(
            label="購買",
            style=styles.get(Pokeball(ball_type), discord.ButtonStyle.secondary),
        )
        self.ball_type = ball_type
        self.player_id = player_id

    async def callback(self, interaction: Interaction) -> None:
        """Show purchase modal."""
        if interaction.user.id != self.player_id:
            await interaction.response.send_message(
                f"{Emoji.CROSS} 這不是你的商店！", ephemeral=True
            )
            return

        modal = BuyBallModal(self.player_id, self.ball_type, self.view.refresh_shop)
        await interaction.response.send_modal(modal)


class ShopView(LayoutView):
    """Shop view with V2 components."""

    def __init__(
        self, player_id: int, wallet: dict, inventory: PlayerBallInventory
    ) -> None:
        super().__init__(timeout=300)
        self.player_id = player_id
        self.wallet = wallet
        self.inventory = inventory

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the shop UI."""
        # Clear existing items
        self.clear_items()

        # Get emojis
        money_emoji = get_currency_emoji(Currency.POKEDOLLAR)
        quest_emoji = get_currency_emoji(Currency.QUEST_POINT)

        # Main container with gradient blue
        container = Container(accent_color=discord.Color.from_rgb(66, 133, 244))

        # Header
        container.add_item(
            TextDisplay("# 🏪 寶貝球商店\n-# Poké Mart - 購買捕捉寶可夢的必需品")
        )
        container.add_item(Separator(spacing=discord.SeparatorSpacing.small))

        # Wallet Section
        wallet_text = (
            f"### 💰 錢包餘額\n"
            f"**{self.wallet['pokedollar']:,}** {money_emoji}\n"
            f"**{self.wallet['quest_point']:,}** {quest_emoji}"
        )
        container.add_item(TextDisplay(wallet_text))
        container.add_item(Separator(spacing=discord.SeparatorSpacing.small))

        # Inventory Section with detailed ball info - using Section for inline buttons
        container.add_item(TextDisplay("### 🎒 商品列表"))

        for ball_type in [
            Pokeball.POKEBALL,
            Pokeball.GREATBALL,
            Pokeball.ULTRABALL,
            Pokeball.MASTERBALL,
        ]:
            ball_emoji = get_ball_emoji(ball_type)
            name = get_pokeball_name(ball_type)
            qty = self.inventory.get_quantity(ball_type)
            price, currency_type = ShopService.get_ball_price(ball_type)
            catch_bonus = ShopService.get_ball_catch_bonus(ball_type)

            # Currency display
            if currency_type == Currency.POKEDOLLAR:
                price_str = f"{price:,} {money_emoji}"
            else:
                price_str = f"{price:,} {quest_emoji}"

            # Catch bonus display
            if ball_type == Pokeball.MASTERBALL:
                bonus_str = "**100%** 必定捕獲"
            elif catch_bonus > 0:
                bonus_str = f"+{catch_bonus}% 捕獲率"
            else:
                bonus_str = "基礎捕獲率"

            # Use Section to put ball info and buy button side by side
            ball_title = f"{ball_emoji} **{name}**"
            ball_details = f"-# 庫存: {qty} ┃ {price_str} ┃ {bonus_str}"

            section = Section(
                ball_title,
                ball_details,
                accessory=BuyBallButton(ball_type, self.player_id),
            )
            container.add_item(section)

        container.add_item(Separator(spacing=discord.SeparatorSpacing.small))

        # Footer hint
        container.add_item(TextDisplay("-# 💡 點擊右側按鈕購買寶貝球"))

        self.add_item(container)

    async def refresh_shop(
        self, interaction: Interaction, success_message: str = ""
    ) -> None:
        """Refresh the shop UI after a purchase."""
        # Re-fetch data using player_id
        self.wallet = (await ShopService.get_shop_inventory(self.player_id))["wallet"]
        await self.inventory.refresh_from_db()

        # Rebuild UI
        self._build_ui()

        # Send success message and update view
        if success_message:
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(
                f"{Emoji.CHECK} {success_message}", ephemeral=True
            )
        else:
            await interaction.response.edit_message(view=self)
