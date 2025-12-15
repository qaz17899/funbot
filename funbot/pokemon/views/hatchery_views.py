"""Hatchery views.

UI components for the /pokemon hatchery commands.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from funbot.pokemon.ui_utils import Emoji, build_progress_bar, get_type_emoji
from funbot.ui.components_v2 import Container, LayoutView, Separator, TextDisplay

if TYPE_CHECKING:
    from funbot.db.models.pokemon import PlayerEgg, PokemonData


class HatcheryListView(LayoutView):
    """V2 LayoutView for hatchery display."""

    def __init__(self, eggs: list[PlayerEgg], slots: int, username: str) -> None:
        super().__init__(timeout=0)

        container = Container(accent_color=discord.Color.green())
        container.add_item(TextDisplay(f"# {Emoji.EGG} {username} 的孵化場"))
        container.add_item(TextDisplay(f"槽位: {len(eggs)}/{slots}"))
        container.add_item(Separator(spacing=discord.SeparatorSpacing.small))

        if not eggs:
            container.add_item(TextDisplay("*孵化場是空的*"))
            container.add_item(
                TextDisplay("-# 使用 `/pokemon hatchery add <寶可夢>` 加入蛋")
            )
        else:
            for egg in eggs:
                data: PokemonData = egg.pokemon_data  # type: ignore
                type_emoji = get_type_emoji(data.type1)
                progress_bar = build_progress_bar(
                    egg.steps, egg.steps_required, width=10
                )
                ready_mark = f" {Emoji.CHECK} 準備孵化！" if egg.can_hatch else ""

                container.add_item(
                    TextDisplay(
                        f"**Slot {egg.slot + 1}**: {type_emoji} {data.name}{ready_mark}"
                    )
                )
                container.add_item(
                    TextDisplay(f"-# {progress_bar} ({egg.progress:.1f}%)")
                )

        self.add_item(container)
