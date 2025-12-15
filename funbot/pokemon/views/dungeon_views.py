"""Dungeon UI views using V2 components.

Provides dungeon list, exploration, battle, and result views.
Uses auto-exploration with animated display similar to GymBattleView.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, ClassVar

import discord

from funbot.pokemon.ui_utils import get_currency_emoji
from funbot.ui.components_v2 import Container, LayoutView, TextDisplay

if TYPE_CHECKING:
    from funbot.pokemon.services.dungeon_map import DungeonMap
    from funbot.pokemon.services.dungeon_service import DungeonInfo
    from funbot.types import Interaction, User


# Region names for display
REGION_NAMES = {
    0: "Kanto",
    1: "Johto",
    2: "Hoenn",
    3: "Sinnoh",
    4: "Unova",
    5: "Kalos",
    6: "Alola",
    7: "Galar",
    8: "Paldea",
}


class DungeonListView(LayoutView):
    """View for displaying available dungeons in a region.

    Shows all dungeons with their unlock status, entry cost, and clear count.

    Requirements:
        - 5.1: Display all dungeons with unlock status
        - 5.2: Show entry cost, region, clear count
        - 5.3: Show available Pokemon and loot for unlocked dungeons
    """

    def __init__(
        self,
        dungeons: list[DungeonInfo],
        region: int,
        author: User | None = None,
    ) -> None:
        """Initialize the dungeon list view.

        Args:
            dungeons: List of dungeon info for the region
            region: Region number (0=Kanto, etc.)
            author: User who can interact with this view
        """
        super().__init__(author=author, timeout=120)

        region_name = REGION_NAMES.get(region, f"Region {region}")
        token_emoji = get_currency_emoji("dungeon_token")

        container = Container(accent_color=discord.Color.dark_purple())

        # Header
        container.add_item(TextDisplay(f"# 🏰 {region_name} 地下城"))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        if not dungeons:
            container.add_item(TextDisplay("此區域沒有可用的地下城。"))
        else:
            # Build dungeon list
            dungeon_lines = []
            for dungeon in dungeons:
                # Status indicator
                if dungeon.is_unlocked:
                    status = "✅" if dungeon.player_clears > 0 else "⚔️"
                else:
                    status = "🔒"  # Locked

                # Build line
                line = f"{status} **{dungeon.name}**"

                # Add cost and clears for unlocked dungeons
                if dungeon.is_unlocked:
                    line += f" - {dungeon.token_cost:,} {token_emoji}"
                    if dungeon.player_clears > 0:
                        line += f" ({dungeon.player_clears}次通關)"
                # Show unlock hints for locked dungeons
                elif dungeon.unlock_hints:
                    hint = dungeon.unlock_hints[0]
                    line += f"\n  -# 解鎖條件: {hint}"

                dungeon_lines.append(line)

            container.add_item(TextDisplay("\n".join(dungeon_lines)))

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(
            TextDisplay("-# 使用 `/pokemon dungeon enter <地下城名>` 來進入地下城")
        )

        self.add_item(container)


class DungeonExploreView(LayoutView):
    """Auto-exploration dungeon view with animated display.

    Automatically explores the dungeon with visual updates every second.
    Similar to GymBattleView's animation loop.

    Requirements:
        - 6.1: Display visual map representation
        - 6.2: Show current position, revealed tiles, remaining actions
    """

    # Tile type to emoji mapping
    TILE_EMOJIS: ClassVar[dict[str, str]] = {
        "entrance": "🚪",
        "enemy": "👾",
        "chest": "📦",
        "boss": "👹",
        "empty": "⬜",
        "ladder": "🪜",
        "fog": "⬛",  # Unrevealed tile
        "player": "🧑",  # Player position
    }

    def __init__(
        self,
        run_id: int,
        dungeon_name: str,
        user_id: int,
        author: User | None = None,
    ) -> None:
        """Initialize the exploration view.

        Args:
            run_id: Active dungeon run ID
            dungeon_name: Name of the dungeon
            user_id: Player's user ID
            author: User who can interact with this view
        """
        super().__init__(author=author, timeout=300)  # 5 minute timeout

        self.run_id = run_id
        self.dungeon_name = dungeon_name
        self.user_id = user_id

        # State tracking
        self.running = True
        self.abandoned = False
        self.map_data: dict = {}
        self.chests_opened = 0
        self.enemies_defeated = 0
        self.loot_collected: list[dict] = []
        self.pokemon_caught: list[str] = []
        self.status_message = "開始探索..."
        self.completed = False
        self.is_first_clear = False
        self.rewards: dict = {}

        # Build initial loading view
        self._build_initial_view()

    def _build_initial_view(self) -> None:
        """Build the initial loading view."""
        container = Container(accent_color=discord.Color.dark_teal())
        container.add_item(TextDisplay(f"# 🏰 {self.dungeon_name}"))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(TextDisplay("⏳ 載入地下城中..."))
        self.add_item(container)

    def _render_map(self) -> str:
        """Render the map as a text grid."""
        tiles = self.map_data.get("tiles", [])
        player_pos = tuple(self.map_data.get("player_position", [0, 0]))
        size = self.map_data.get("size", 5)

        lines = []
        for y in range(size):
            row = []
            for x in range(size):
                if (x, y) == player_pos:
                    row.append(self.TILE_EMOJIS["player"])
                elif y < len(tiles) and x < len(tiles[y]):
                    tile = tiles[y][x]
                    if tile.get("is_visible", False):
                        tile_type = tile.get("tile_type", "empty")
                        row.append(self.TILE_EMOJIS.get(tile_type, "❓"))
                    else:
                        row.append(self.TILE_EMOJIS["fog"])
                else:
                    row.append(self.TILE_EMOJIS["fog"])
            lines.append("".join(row))

        return "\n".join(lines)

    def _build_explore_container(self) -> Container:
        """Build the exploration UI container."""
        container = Container(accent_color=discord.Color.dark_teal())

        # Header
        container.add_item(TextDisplay(f"# 🏰 {self.dungeon_name}"))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Map display
        if self.map_data:
            map_text = self._render_map()
            container.add_item(TextDisplay(f"```\n{map_text}\n```"))
        else:
            container.add_item(TextDisplay("載入地圖中..."))

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Stats
        stats_text = (
            f"📦 **寶箱**: {self.chests_opened} | "
            f"👾 **敵人**: {self.enemies_defeated}"
        )
        container.add_item(TextDisplay(stats_text))

        # Status message
        container.add_item(TextDisplay(f"\n**{self.status_message}**"))

        # Legend
        legend = "-# 🧑=你 🚪=入口 👾=敵人 📦=寶箱 👹=Boss ⬛=未探索"
        container.add_item(TextDisplay(legend))

        return container

    def _build_result_container(self) -> Container:
        """Build the completion result container."""
        color = discord.Color.gold() if self.completed else discord.Color.dark_grey()
        container = Container(accent_color=color)

        # Header
        if self.completed:
            header = f"# 🎉 {self.dungeon_name} 通關！"
            if self.is_first_clear:
                header += "\n### ⭐ 首次通關！"
        elif self.abandoned:
            header = f"# 🚪 放棄 {self.dungeon_name}"
        else:
            header = f"# 🚪 離開 {self.dungeon_name}"

        container.add_item(TextDisplay(header))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Stats summary
        stats = [
            f"👾 **擊敗敵人**: {self.enemies_defeated}",
            f"📦 **開啟寶箱**: {self.chests_opened}",
        ]
        container.add_item(TextDisplay("\n".join(stats)))

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Rewards
        money_emoji = get_currency_emoji("money")
        token_emoji = get_currency_emoji("dungeon_token")

        money = self.rewards.get("money", 0)
        exp = self.rewards.get("exp", 0)
        tokens = self.rewards.get("dungeon_tokens", 0)

        rewards_lines = [
            f"💰 **金錢**: {money:,} {money_emoji}",
            f"✨ **經驗**: {exp:,}",
            f"🎫 **地下城代幣**: {tokens:,} {token_emoji}",
        ]

        # First clear bonus
        first_clear_bonus = self.rewards.get("first_clear_bonus")
        if self.is_first_clear and first_clear_bonus:
            bonus_tokens = first_clear_bonus.get("bonus_tokens", 0)
            bonus_money = first_clear_bonus.get("bonus_money", 0)
            if bonus_tokens > 0:
                rewards_lines.append(
                    f"⭐ **首通獎勵代幣**: +{bonus_tokens:,} {token_emoji}"
                )
            if bonus_money > 0:
                rewards_lines.append(
                    f"⭐ **首通獎勵金錢**: +{bonus_money:,} {money_emoji}"
                )

        container.add_item(TextDisplay("\n".join(rewards_lines)))

        # Loot collected
        if self.loot_collected:
            container.add_item(
                discord.ui.Separator(spacing=discord.SeparatorSpacing.small)
            )
            loot_lines = ["### 📦 收集的戰利品"]
            for item in self.loot_collected[:10]:
                tier_emoji = DungeonResultView._get_tier_emoji(
                    item.get("tier", "common")
                )
                loot_lines.append(f"{tier_emoji} {item.get('item_name', 'Unknown')}")
            if len(self.loot_collected) > 10:
                loot_lines.append(f"-# ...還有 {len(self.loot_collected) - 10} 個物品")
            container.add_item(TextDisplay("\n".join(loot_lines)))

        # Pokemon caught
        if self.pokemon_caught:
            container.add_item(
                discord.ui.Separator(spacing=discord.SeparatorSpacing.small)
            )
            caught_text = "### 🎉 捕獲的寶可夢\n" + ", ".join(self.pokemon_caught)
            container.add_item(TextDisplay(caught_text))

        return container

    async def run_exploration(self, interaction: Interaction) -> None:
        """Run the auto-exploration loop.

        Args:
            interaction: Discord interaction to respond to
        """
        from funbot.pokemon.services.dungeon_exploration_service import (
            DungeonExplorationService,
            ExplorationStatus,
            TileEventType,
        )
        from funbot.pokemon.services.dungeon_map import DungeonMap
        from funbot.pokemon.services.dungeon_service import DungeonService

        service = DungeonService()

        # Get initial run state
        run = await service.get_run_by_id(self.run_id)
        if not run:
            self.status_message = "❌ 找不到地下城探索資料"
            self.clear_items()
            self.add_item(self._build_explore_container())
            await interaction.edit_original_response(view=self)
            return

        self.map_data = run.map_data
        self.chests_opened = run.chests_opened
        self.enemies_defeated = run.enemies_defeated
        self.loot_collected = run.loot_collected or []

        # Send initial view
        self.clear_items()
        self.add_item(self._build_explore_container())
        await interaction.edit_original_response(view=self)

        dungeon_map = DungeonMap.from_dict(run.map_data)

        # Auto-exploration loop
        while self.running and not self.abandoned:
            await asyncio.sleep(1.0)

            # Get valid moves
            valid_moves = DungeonExplorationService.get_valid_moves(
                dungeon_map, ExplorationStatus.EXPLORING
            )

            if not valid_moves:
                self.status_message = "❌ 無法移動"
                break

            # Pick next move (prioritize unvisited tiles)
            next_move = self._pick_next_move(dungeon_map, valid_moves)
            if not next_move:
                self.status_message = "✅ 探索完成"
                break

            target_x, target_y = next_move

            # Execute exploration step
            result = await service.explore_step(self.run_id, target_x, target_y)

            # Refresh run state
            run = await service.get_run_by_id(self.run_id)
            if not run:
                break

            self.map_data = run.map_data
            self.chests_opened = run.chests_opened
            self.enemies_defeated = run.enemies_defeated
            self.loot_collected = run.loot_collected or []
            dungeon_map = DungeonMap.from_dict(run.map_data)

            # Handle events
            if result.tile_event:
                event_type = result.tile_event.event_type

                if event_type == TileEventType.BATTLE:
                    self.status_message = "⚔️ 遇到敵人！戰鬥中..."
                    self.clear_items()
                    self.add_item(self._build_explore_container())
                    try:
                        await interaction.edit_original_response(view=self)
                    except discord.HTTPException:
                        self.running = False
                        break

                    await asyncio.sleep(1.0)

                    if result.battle_result:
                        pokemon_name = result.battle_result.pokemon_name
                        if result.battle_result.catch_success:
                            self.pokemon_caught.append(pokemon_name)
                            self.status_message = f"🎉 捕獲了 {pokemon_name}！"
                        elif result.battle_result.catch_attempted:
                            self.status_message = f"💨 {pokemon_name} 逃跑了..."
                        else:
                            self.status_message = f"✅ 擊敗了 {pokemon_name}！"

                elif event_type == TileEventType.CHEST:
                    if result.chest_result:
                        tier = result.chest_result.tier
                        item_name = result.chest_result.item_name
                        tier_emoji = DungeonResultView._get_tier_emoji(tier)
                        self.status_message = f"📦 獲得 {tier_emoji} {item_name}！"
                    else:
                        self.status_message = "📦 開啟寶箱！"

                elif event_type == TileEventType.BOSS:
                    self.status_message = "👹 發現 Boss！準備戰鬥..."
                    self.clear_items()
                    self.add_item(self._build_explore_container())
                    try:
                        await interaction.edit_original_response(view=self)
                    except discord.HTTPException:
                        self.running = False
                        break

                    await asyncio.sleep(1.0)

                    # Fight boss
                    boss_result = await service.fight_boss(self.run_id)

                    if boss_result.won:
                        self.completed = True
                        self.rewards = {
                            "money": boss_result.rewards.money,
                            "exp": boss_result.rewards.exp,
                            "dungeon_tokens": boss_result.rewards.dungeon_tokens,
                            "first_clear_bonus": boss_result.rewards.first_clear_bonus,
                        }
                        self.is_first_clear = (
                            boss_result.rewards.first_clear_bonus is not None
                        )
                        self.status_message = f"🎉 擊敗了 {boss_result.boss_name}！"
                        self.running = False
                    else:
                        self.status_message = f"⚔️ 與 {boss_result.boss_name} 戰鬥中..."

                elif event_type == TileEventType.ENTRANCE:
                    self.status_message = "🚪 回到入口"

                elif event_type == TileEventType.LADDER:
                    self.status_message = "🪜 發現樓梯！"

                else:
                    self.status_message = "🧑 移動中..."
            else:
                self.status_message = "🧑 移動中..."

            # Update display
            self.clear_items()
            self.add_item(self._build_explore_container())

            try:
                await interaction.edit_original_response(view=self)
            except discord.HTTPException:
                self.running = False
                break

        # Show final result
        self.clear_items()
        self.add_item(self._build_result_container())

        with contextlib.suppress(discord.HTTPException):
            await interaction.edit_original_response(view=self)

    def _pick_next_move(
        self, dungeon_map: DungeonMap, valid_moves: list[tuple[int, int]]
    ) -> tuple[int, int] | None:
        """Pick the next move, prioritizing unvisited tiles.

        Args:
            dungeon_map: Current map state
            valid_moves: List of valid move positions

        Returns:
            Next position to move to, or None if no good moves
        """
        import random

        # Prioritize unvisited tiles
        unvisited = []
        visited = []

        for x, y in valid_moves:
            tile = dungeon_map.get_tile(x, y)
            if tile and not tile.is_visited:
                unvisited.append((x, y))
            else:
                visited.append((x, y))

        if unvisited:
            return random.choice(unvisited)

        # If all adjacent tiles visited, pick randomly
        if visited:
            return random.choice(visited)

        return None


class DungeonBattleView(LayoutView):
    """Dungeon battle progress view.

    Displays enemy Pokemon with health bar and battle progress.
    Reuses patterns from GymBattleView.

    Requirements:
        - 6.3: Display battle progress with health bars
    """

    def __init__(
        self,
        enemy_name: str,
        enemy_health: int,
        enemy_max_health: int,
        damage_per_tick: int,
        is_boss: bool = False,
        author: User | None = None,
    ) -> None:
        """Initialize the battle view.

        Args:
            enemy_name: Name of the enemy Pokemon
            enemy_health: Current enemy health
            enemy_max_health: Maximum enemy health
            damage_per_tick: Damage dealt per tick
            is_boss: Whether this is a boss battle
            author: User who can interact with this view
        """
        super().__init__(author=author, timeout=60)

        self.enemy_name = enemy_name
        self.enemy_health = enemy_health
        self.enemy_max_health = enemy_max_health
        self.damage_per_tick = damage_per_tick
        self.is_boss = is_boss

        self._build_view()

    def _build_health_bar(self, current: int, maximum: int, width: int = 16) -> str:
        """Build a visual health bar.

        Args:
            current: Current HP
            maximum: Maximum HP
            width: Number of characters in bar

        Returns:
            Health bar string
        """
        if maximum <= 0:
            return "░" * width + " 0/0"

        percent = max(0, min(1, current / maximum))
        filled = int(percent * width)
        empty = width - filled

        return f"{'█' * filled}{'░' * empty} {current:,}/{maximum:,}"

    def _build_view(self) -> None:
        """Build the battle view components."""
        # Choose color based on boss status
        color = discord.Color.red() if self.is_boss else discord.Color.orange()

        container = Container(accent_color=color)

        # Header
        battle_type = "👹 Boss 戰鬥" if self.is_boss else "⚔️ 戰鬥"
        container.add_item(TextDisplay(f"# {battle_type}"))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Enemy info
        hp_bar = self._build_health_bar(self.enemy_health, self.enemy_max_health)
        enemy_text = f"### 🎯 {self.enemy_name}\nHP: `{hp_bar}`"
        container.add_item(TextDisplay(enemy_text))

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Battle stats
        ticks_needed = max(
            1, (self.enemy_health + self.damage_per_tick - 1) // self.damage_per_tick
        )
        stats_text = (
            f"⚔️ **每秒傷害**: {self.damage_per_tick:,}\n"
            f"⏱️ **預計時間**: {ticks_needed} 秒"
        )
        container.add_item(TextDisplay(stats_text))

        self.add_item(container)


class DungeonBattleResultView(LayoutView):
    """View for displaying battle result.

    Shows victory/defeat status and rewards.
    """

    def __init__(
        self,
        enemy_name: str,
        defeated: bool,
        exp_earned: int,
        catch_attempted: bool = False,
        catch_success: bool = False,
        is_boss: bool = False,
        author: User | None = None,
    ) -> None:
        """Initialize the battle result view.

        Args:
            enemy_name: Name of the enemy Pokemon
            defeated: Whether the enemy was defeated
            exp_earned: Experience points earned
            catch_attempted: Whether catch was attempted
            catch_success: Whether catch was successful
            is_boss: Whether this was a boss battle
            author: User who can interact with this view
        """
        super().__init__(author=author, timeout=60)

        container = Container(
            accent_color=discord.Color.gold() if defeated else discord.Color.red()
        )

        if defeated:
            # Victory
            container.add_item(TextDisplay(f"# ✅ 擊敗了 {enemy_name}！"))
            container.add_item(
                discord.ui.Separator(spacing=discord.SeparatorSpacing.small)
            )

            rewards = [f"✨ **經驗值**: +{exp_earned:,}"]

            if catch_attempted:
                if catch_success:
                    rewards.append(f"🎉 **成功捕獲** {enemy_name}！")
                else:
                    rewards.append(f"💨 {enemy_name} 逃跑了...")

            container.add_item(TextDisplay("\n".join(rewards)))
        else:
            # Defeat (shouldn't happen in current implementation)
            container.add_item(TextDisplay(f"# ❌ 被 {enemy_name} 擊敗..."))

        self.add_item(container)


class DungeonResultView(LayoutView):
    """Dungeon completion result view.

    Displays summary of encounters, loot, and rewards.

    Requirements:
        - 6.4: Display summary of encounters, loot, rewards
    """

    def __init__(
        self,
        dungeon_name: str,
        completed: bool,
        enemies_defeated: int,
        chests_opened: int,
        loot_collected: list[dict],
        money_earned: int,
        exp_earned: int,
        tokens_earned: int,
        is_first_clear: bool = False,
        first_clear_bonus: dict | None = None,
        pokemon_caught: list[str] | None = None,
        author: User | None = None,
    ) -> None:
        """Initialize the result view.

        Args:
            dungeon_name: Name of the dungeon
            completed: Whether dungeon was completed (boss defeated)
            enemies_defeated: Number of enemies defeated
            chests_opened: Number of chests opened
            loot_collected: List of loot items collected
            money_earned: Money earned
            exp_earned: Experience earned
            tokens_earned: Dungeon tokens earned
            is_first_clear: Whether this was first clear
            first_clear_bonus: First clear bonus rewards
            pokemon_caught: List of Pokemon caught
            author: User who can interact with this view
        """
        super().__init__(author=author, timeout=120)

        # Choose color based on completion
        color = discord.Color.gold() if completed else discord.Color.dark_grey()

        container = Container(accent_color=color)

        # Header
        if completed:
            header = f"# 🎉 {dungeon_name} 通關！"
            if is_first_clear:
                header += "\n### ⭐ 首次通關！"
        else:
            header = f"# 🚪 離開 {dungeon_name}"

        container.add_item(TextDisplay(header))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Stats summary
        stats = [
            f"👾 **擊敗敵人**: {enemies_defeated}",
            f"📦 **開啟寶箱**: {chests_opened}",
        ]
        container.add_item(TextDisplay("\n".join(stats)))

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Rewards
        money_emoji = get_currency_emoji("money")
        token_emoji = get_currency_emoji("dungeon_token")

        rewards = [
            f"💰 **金錢**: {money_earned:,} {money_emoji}",
            f"✨ **經驗**: {exp_earned:,}",
            f"🎫 **地下城代幣**: {tokens_earned:,} {token_emoji}",
        ]

        # First clear bonus
        if is_first_clear and first_clear_bonus:
            bonus_tokens = first_clear_bonus.get("bonus_tokens", 0)
            bonus_money = first_clear_bonus.get("bonus_money", 0)
            if bonus_tokens > 0:
                rewards.append(f"⭐ **首通獎勵代幣**: +{bonus_tokens:,} {token_emoji}")
            if bonus_money > 0:
                rewards.append(f"⭐ **首通獎勵金錢**: +{bonus_money:,} {money_emoji}")

        container.add_item(TextDisplay("\n".join(rewards)))

        # Loot collected
        if loot_collected:
            container.add_item(
                discord.ui.Separator(spacing=discord.SeparatorSpacing.small)
            )
            loot_lines = ["### 📦 收集的戰利品"]
            for item in loot_collected[:10]:  # Limit to 10 items
                tier_emoji = self._get_tier_emoji(item.get("tier", "common"))
                loot_lines.append(f"{tier_emoji} {item.get('item_name', 'Unknown')}")
            if len(loot_collected) > 10:
                loot_lines.append(f"-# ...還有 {len(loot_collected) - 10} 個物品")
            container.add_item(TextDisplay("\n".join(loot_lines)))

        # Pokemon caught
        if pokemon_caught:
            container.add_item(
                discord.ui.Separator(spacing=discord.SeparatorSpacing.small)
            )
            caught_text = "### 🎉 捕獲的寶可夢\n" + ", ".join(pokemon_caught)
            container.add_item(TextDisplay(caught_text))

        self.add_item(container)

    @staticmethod
    def _get_tier_emoji(tier: str) -> str:
        """Get emoji for loot tier.

        Args:
            tier: Loot tier name

        Returns:
            Emoji string
        """
        tier_emojis = {
            "common": "⚪",
            "rare": "🔵",
            "epic": "🟣",
            "legendary": "🟡",
            "mythic": "🔴",
        }
        return tier_emojis.get(tier.lower(), "⚪")
