"""Discord autocomplete functions for Pokemon commands.

Provides autocomplete for:
- Region selection (Kanto, Johto, etc.)
- Route selection with status indicators
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from discord import app_commands

from funbot.pokemon.constants.enums import Region
from funbot.pokemon.services.route_service import RouteStatus, get_route_status_service
from funbot.pokemon.ui_utils import (
    REGION_DISPLAY_NAMES,
    format_dungeon_choice,
    format_gym_choice,
    format_route_choice,
)

if TYPE_CHECKING:
    from funbot.types import Interaction


async def region_autocomplete(
    _interaction: Interaction, current: str
) -> list[app_commands.Choice[int]]:
    """Autocomplete for region selection.

    Shows available regions with localized names.
    Uses REGION_DISPLAY_NAMES from ui_utils as SSOT.
    """
    # Yield control to event loop (required for async autocomplete)
    await asyncio.sleep(0)

    current_lower = current.lower()
    choices = []

    for region_enum in Region:
        display_name = REGION_DISPLAY_NAMES.get(region_enum, region_enum.name)
        if current_lower in display_name.lower():
            choices.append(
                app_commands.Choice(name=display_name, value=region_enum.value)
            )

    return choices[:25]  # Discord limits to 25 choices


async def route_autocomplete(
    interaction: Interaction, current: str
) -> list[app_commands.Choice[int]]:
    """Autocomplete for route selection with status indicators.

    Shows routes in the selected region with:
    - Status emoji (🔒/⚔️/🆕/✨/🌈)
    - Kill count (X/10)
    - Extra info (新/閃/✓)

    Requires 'region' parameter to be filled first.
    """
    # Get the region from namespace (filled by user)
    namespace = interaction.namespace
    region = getattr(namespace, "region", 0)  # Default to Kanto

    player_id = interaction.user.id
    service = get_route_status_service()

    # Get all routes for this region with status
    routes_with_status = await service.get_available_routes_for_region(
        player_id, region
    )

    current_lower = current.lower()
    choices = []

    for route, status, kills in routes_with_status:
        # Use centralized format_route_choice from ui_utils
        display_name, route_id = format_route_choice(route, status, kills)

        # Filter by current input
        if current_lower in display_name.lower() or current_lower in route.name.lower():
            choices.append(app_commands.Choice(name=display_name, value=route_id))

    return choices[:25]  # Discord limits to 25 choices


async def unlocked_route_autocomplete(
    interaction: Interaction, current: str
) -> list[app_commands.Choice[int]]:
    """Autocomplete showing only unlocked routes.

    Same as route_autocomplete but filters out locked routes.
    Useful for commands that require an accessible route.
    """
    namespace = interaction.namespace
    region = getattr(namespace, "region", 0)

    player_id = interaction.user.id
    service = get_route_status_service()

    routes_with_status = await service.get_available_routes_for_region(
        player_id, region
    )

    current_lower = current.lower()
    choices = []

    for route, status, kills in routes_with_status:
        # Skip locked routes
        if status == RouteStatus.LOCKED:
            continue

        # Use centralized format_route_choice from ui_utils
        display_name, route_id = format_route_choice(route, status, kills)

        if current_lower in display_name.lower() or current_lower in route.name.lower():
            choices.append(app_commands.Choice(name=display_name, value=route_id))

    return choices[:25]


async def gym_autocomplete(
    interaction: Interaction, current: str
) -> list[app_commands.Choice[str]]:
    """Autocomplete for gym selection.

    Shows available gyms in the current region with badge status.
    Uses GymService for data and format_gym_choice for display.
    """
    from funbot.pokemon.services.gym_service import GymService

    # Yield control for async
    await asyncio.sleep(0)

    # Get region from namespace (default to Kanto)
    namespace = interaction.namespace
    region = getattr(namespace, "region", 0)
    user_id = interaction.user.id

    # Use Service to get data (proper layering)
    gyms_with_status = await GymService.search_gyms_for_autocomplete(
        user_id, region, current
    )

    choices = []
    for gym, has_badge in gyms_with_status:
        # Use centralized format function from ui_utils
        display_name = format_gym_choice(gym.name, gym.leader, gym.is_elite, has_badge)
        choices.append(app_commands.Choice(name=display_name, value=gym.name))

    return choices[:25]


async def dungeon_autocomplete(
    interaction: Interaction, current: str
) -> list[app_commands.Choice[str]]:
    """Autocomplete for dungeon selection.

    Shows available dungeons in the current region with status indicators:
    - ⚔️ Available (not cleared)
    - ✅ Cleared

    Uses DungeonService for data and format_dungeon_choice for display.
    Requires 'region' parameter to be filled first (defaults to Kanto).
    """
    from funbot.pokemon.services.dungeon_service import DungeonService

    # Yield control for async
    await asyncio.sleep(0)

    # Get region from namespace (default to Kanto)
    namespace = interaction.namespace
    region = getattr(namespace, "region", 0)
    user_id = interaction.user.id

    # Use Service to get data (proper layering)
    service = DungeonService()
    dungeons_with_status = await service.search_dungeons_for_autocomplete(
        user_id, region, current
    )

    choices = []
    for dungeon, clears in dungeons_with_status:
        # Use centralized format function from ui_utils
        display_name = format_dungeon_choice(dungeon.name, clears)
        choices.append(app_commands.Choice(name=display_name, value=dungeon.name))

    return choices[:25]
