"""Shared UI utilities for Pokemon module.

Contains emoji mappings and other UI helpers used across multiple cogs.
"""

from __future__ import annotations

__all__ = ("BALL_EMOJIS", "TYPE_EMOJIS", "get_ball_emoji", "get_type_emoji")


# Pokemon type to emoji mapping (all 18 types)
TYPE_EMOJIS: dict[int, str] = {
    1: "⚪",  # Normal
    2: "🔥",  # Fire
    3: "💧",  # Water
    4: "⚡",  # Electric
    5: "🌿",  # Grass
    6: "❄️",  # Ice
    7: "👊",  # Fighting
    8: "☠️",  # Poison
    9: "🏔️",  # Ground
    10: "🪽",  # Flying
    11: "🔮",  # Psychic
    12: "🐛",  # Bug
    13: "🪨",  # Rock
    14: "👻",  # Ghost
    15: "🐉",  # Dragon
    16: "🌑",  # Dark
    17: "⚙️",  # Steel
    18: "🧚",  # Fairy
}


def get_type_emoji(type_id: int) -> str:
    """Get emoji for Pokemon type ID.

    Args:
        type_id: Pokemon type ID (1-18)

    Returns:
        Emoji string for the type
    """
    return TYPE_EMOJIS.get(type_id, "⚪")


# Pokeball type to emoji mapping
BALL_EMOJIS: dict[int, str] = {
    0: "❌",  # NONE
    1: "🔴",  # POKEBALL
    2: "🔵",  # GREATBALL
    3: "🟡",  # ULTRABALL
    4: "🟣",  # MASTERBALL
}


def get_ball_emoji(ball_id: int) -> str:
    """Get emoji for Pokeball type.

    Args:
        ball_id: Pokeball enum value (0-4)

    Returns:
        Emoji string for the ball type
    """
    return BALL_EMOJIS.get(ball_id, "⚪")
