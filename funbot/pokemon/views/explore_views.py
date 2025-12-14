"""Explore results views.

UI components for the /pokemon explore command results.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import discord

from funbot.pokemon.ui_utils import Emoji, get_currency_emoji
from funbot.ui.components_v2 import Container, LayoutView, TextDisplay

if TYPE_CHECKING:
    from funbot.db.models.pokemon.route_data import RouteData


@dataclass
class ExploreResult:
    """Result data from explore encounters."""

    total_exp: int
    total_money: int
    pokedex_new: list[str]
    shiny_caught: list[str]
    already_caught: int
    failed_catches: int
    total_encounters: int
    total_battles: int
    balls_used: dict[int, int]


class ExploreResultView(LayoutView):
    """V2 LayoutView for explore results."""

    def __init__(self, username: str, route_data: RouteData, results: ExploreResult) -> None:
        super().__init__(timeout=0)  # No timeout for static result view

        container = Container(accent_color=discord.Color.green())

        # Header with route info
        container.add_item(
            TextDisplay(f"# {Emoji.MAP} {route_data.name}\n-# {username} 的探索結果")
        )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Battle stats
        money_emoji = get_currency_emoji("money")
        battle_summary = (
            f"{Emoji.BATTLE} 戰鬥: {results.total_battles} 場\n"
            f"{Emoji.EXP} 經驗: +{results.total_exp:,}\n"
            f"{money_emoji} 金錢: +{results.total_money:,}"
        )
        container.add_item(TextDisplay(battle_summary))

        # Catch results
        catch_lines = []

        if results.pokedex_new:
            # Limit display
            catch_lines.extend(f"🆕 **{name}** (圖鑑登錄！)" for name in results.pokedex_new[:5])
            if len(results.pokedex_new) > 5:
                catch_lines.append(f"-# ...還有 {len(results.pokedex_new) - 5} 隻")

        if results.shiny_caught:
            catch_lines.extend(
                f"{Emoji.SHINY} **{name}** (異色！)" for name in results.shiny_caught[:3]
            )

        if results.already_caught > 0:
            catch_lines.append(f"📦 已有寶可夢: +{results.already_caught}")

        if results.failed_catches > 0:
            catch_lines.append(f"{Emoji.CROSS} 捕捉失敗: {results.failed_catches}")

        if catch_lines:
            container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(TextDisplay("### 🎯 捕捉結果"))
            container.add_item(TextDisplay("\n".join(catch_lines)))

        # Balls used
        if results.balls_used:
            from funbot.pokemon.ui_utils import get_ball_emoji

            ball_lines = []
            for ball_type, count in sorted(results.balls_used.items()):
                ball_emoji = get_ball_emoji(ball_type)
                ball_lines.append(f"{ball_emoji} ×{count}")

            container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(TextDisplay(f"-# 使用寶貝球: {' '.join(ball_lines)}"))

        self.add_item(container)
