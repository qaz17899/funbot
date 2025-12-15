"""Gym battle UI views using V2 components.

Provides real-time animated gym battles with health bars and leader images.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING

import discord

from funbot.pokemon.services.battle_service import BattleService
from funbot.pokemon.services.gym_service import (
    GYM_TIME_LIMIT,
    GymBattleResult,
    GymBattleState,
    GymBattleStatus,
    GymService,
)
from funbot.pokemon.ui_utils import Emoji, get_currency_emoji
from funbot.ui.components_v2 import (
    Container,
    LayoutView,
    Section,
    TextDisplay,
    Thumbnail,
)

if TYPE_CHECKING:
    from funbot.db.models.pokemon.gym_data import GymData
    from funbot.types import Interaction


class GymBattleView(LayoutView):
    """Real-time animated gym battle view using V2 components.

    Updates every second to show battle progress with health bars.
    """

    def __init__(self, user_id: int, gym: GymData, state: GymBattleState) -> None:
        super().__init__(timeout=60)  # 60 second timeout for safety
        self.user_id = user_id
        self.gym = gym
        self.state = state
        self.running = True
        self.result: GymBattleResult | None = None

    def _build_health_bar(self, current: int, maximum: int, width: int = 16) -> str:
        """Build a visual health bar.

        Args:
            current: Current HP
            maximum: Maximum HP
            width: Number of characters in bar

        Returns:
            Health bar string like "████████░░░░░░░░ 432/693"
        """
        if maximum <= 0:
            return "░" * width + " 0/0"

        percent = max(0, min(1, current / maximum))
        filled = int(percent * width)
        empty = width - filled

        return f"{'█' * filled}{'░' * empty} {current:,}/{maximum:,}"

    def _build_time_bar(self, time_remaining: float, width: int = 20) -> str:
        """Build a visual time bar.

        Args:
            time_remaining: Seconds remaining
            width: Number of characters

        Returns:
            Time bar string
        """
        percent = max(0, min(1, time_remaining / GYM_TIME_LIMIT))
        filled = int(percent * width)
        empty = width - filled

        return f"{'▓' * filled}{'░' * empty}"

    def _build_battle_container(self) -> Container:
        """Build the battle UI container.

        Returns:
            V2 Container with battle status
        """
        # Choose color based on status
        if self.state.status == GymBattleStatus.WON:
            color = discord.Color.gold()
        elif self.state.status == GymBattleStatus.LOST:
            color = discord.Color.red()
        else:
            # In progress - color based on time remaining
            time_percent = self.state.time_remaining / GYM_TIME_LIMIT
            if time_percent > 0.5:
                color = discord.Color.green()
            elif time_percent > 0.25:
                color = discord.Color.orange()
            else:
                color = discord.Color.red()

        container = Container(accent_color=color)

        # Header with gym info and leader image
        leader_image_url = GymService.get_leader_image_url(self.gym.leader)
        container.add_item(
            Section(
                TextDisplay(f"# ⚡ {self.gym.name}"),
                TextDisplay(f"**館主**: {self.gym.leader}"),
                accessory=Thumbnail(leader_image_url),
            )
        )

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Time bar
        time_bar = self._build_time_bar(self.state.time_remaining)
        container.add_item(
            TextDisplay(
                f"🕐 **剩餘時間**: {self.state.time_remaining:.1f}s\n`{time_bar}`"
            )
        )

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Current opponent with sprite
        current = self.state.current_pokemon
        if current:
            hp_bar = self._build_health_bar(current.current_hp, current.max_hp)
            opponent_text = (
                f"### 🎯 對手: {current.name} Lv.{current.level}\nHP: `{hp_bar}`"
            )

            # Use Section with Thumbnail if sprite available
            if current.sprite_url:
                container.add_item(
                    Section(
                        TextDisplay(opponent_text),
                        accessory=Thumbnail(current.sprite_url),
                    )
                )
            else:
                container.add_item(TextDisplay(opponent_text))
        else:
            container.add_item(TextDisplay("### ✅ 所有寶可夢已擊敗！"))

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Battle stats - show actual damage per tick (using centralized BattleService)
        actual_damage_per_tick = BattleService.calculate_damage_per_tick(
            self.state.player_attack
        )
        progress = f"{self.state.defeated_count}/{self.state.total_pokemon}"
        container.add_item(
            TextDisplay(
                f"⚔️ **每秒傷害**: {actual_damage_per_tick:,}\n"
                f"📊 **進度**: {progress} 寶可夢"
            )
        )

        return container

    def _build_victory_container(self) -> Container:
        """Build the victory screen container.

        Returns:
            V2 Container with victory info
        """
        container = Container(accent_color=discord.Color.gold())

        # Victory header
        leader_image_url = GymService.get_leader_image_url(self.gym.leader)
        container.add_item(
            Section(
                TextDisplay("# 🎉 勝利！"),
                TextDisplay(f"你擊敗了 **{self.gym.leader}**！"),
                accessory=Thumbnail(leader_image_url),
            )
        )

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Defeat message
        if self.gym.defeat_message:
            container.add_item(TextDisplay(f'-# *"{self.gym.defeat_message}"*'))
            container.add_item(
                discord.ui.Separator(spacing=discord.SeparatorSpacing.small)
            )

        # Rewards
        if self.result:
            money_emoji = get_currency_emoji("money")
            rewards = []

            if self.result.is_first_win:
                rewards.append(f"🏅 **獲得徽章**: {self.result.badge_name} Badge")

            rewards.extend(
                (
                    f"**獎金**: {self.result.money_earned:,} {money_emoji}",
                    f"⏱️ **用時**: {self.result.time_used:.1f}秒",
                )
            )

            container.add_item(TextDisplay("\n".join(rewards)))

        return container

    def _build_defeat_container(self) -> Container:
        """Build the defeat screen container.

        Returns:
            V2 Container with defeat info
        """
        container = Container(accent_color=discord.Color.red())

        # Defeat header
        leader_image_url = GymService.get_leader_image_url(self.gym.leader)
        container.add_item(
            Section(
                TextDisplay(f"# {Emoji.CROSS} 失敗..."),
                TextDisplay(f"你無法在時限內擊敗 **{self.gym.leader}**"),
                accessory=Thumbnail(leader_image_url),
            )
        )

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Stats
        current = self.state.current_pokemon
        if current:
            hp_bar = self._build_health_bar(current.current_hp, current.max_hp)
            stats = [
                f"📊 **進度**: {self.state.defeated_count}/{self.state.total_pokemon} 寶可夢",
                f"🎯 **剩餘對手 HP**: `{hp_bar}`",
                "-# 提示: 升級你的寶可夢來增加攻擊力！",
            ]
            container.add_item(TextDisplay("\n".join(stats)))

        return container

    async def run_battle(self, interaction: Interaction) -> None:
        """Run the animated battle loop.

        Args:
            interaction: Discord interaction to respond to
        """
        # Send initial message (interaction already deferred)
        self.clear_items()
        self.add_item(self._build_battle_container())

        await interaction.edit_original_response(view=self)

        # Battle loop - update every second
        while self.running and self.state.status == GymBattleStatus.IN_PROGRESS:
            await asyncio.sleep(1.0)

            # Tick the battle
            self.state = GymService.tick_battle(self.state, delta=1.0)

            # Update display
            self.clear_items()
            self.add_item(self._build_battle_container())

            try:
                await interaction.edit_original_response(view=self)
            except discord.HTTPException:
                # Message might be deleted
                self.running = False
                break

        # Battle finished - show result
        self.result = await GymService.complete_battle(self.user_id, self.state)

        self.clear_items()
        if self.state.status == GymBattleStatus.WON:
            self.add_item(self._build_victory_container())
        else:
            self.add_item(self._build_defeat_container())

        with contextlib.suppress(discord.HTTPException):
            await interaction.edit_original_response(view=self)

    async def run_instant(self, interaction: Interaction) -> None:
        """Run the battle instantly without animation.

        Args:
            interaction: Discord interaction to respond to
        """
        # Simulate full battle
        self.state = GymService.simulate_full_battle(self.state)
        self.result = await GymService.complete_battle(self.user_id, self.state)

        # Show result
        self.clear_items()
        if self.state.status == GymBattleStatus.WON:
            self.add_item(self._build_victory_container())
        else:
            self.add_item(self._build_defeat_container())

        await interaction.edit_original_response(view=self)


class GymListView(LayoutView):
    """View for displaying available gyms."""

    def __init__(
        self, gyms: list[GymData], player_badges: list[str], region_name: str
    ) -> None:
        super().__init__(timeout=60)

        container = Container(accent_color=discord.Color.blue())

        container.add_item(TextDisplay(f"# 🏟️ {region_name} 道館"))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        gym_lines = []
        for gym in gyms:
            has_badge = gym.badge in player_badges
            status = "🏅" if has_badge else "⚔️"
            badge_text = f" ({gym.badge} Badge)" if has_badge else ""
            gym_lines.append(f"{status} **{gym.name}** - {gym.leader}{badge_text}")

        container.add_item(TextDisplay("\n".join(gym_lines)))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(TextDisplay("-# 使用 `/pokemon gym <道館名>` 來挑戰道館"))

        self.add_item(container)
