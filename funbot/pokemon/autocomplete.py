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

if TYPE_CHECKING:
    from funbot.types import Interaction


async def region_autocomplete(
    _interaction: Interaction, current: str
) -> list[app_commands.Choice[int]]:
    """Autocomplete for region selection.

    Shows available regions with localized names.
    """
    # Yield control to event loop (required for async autocomplete)
    await asyncio.sleep(0)

    regions = [
        (Region.KANTO, "關都 Kanto"),
        (Region.JOHTO, "城都 Johto"),
        (Region.HOENN, "豐緣 Hoenn"),
        (Region.SINNOH, "神奧 Sinnoh"),
        (Region.UNOVA, "合眾 Unova"),
        (Region.KALOS, "卡洛斯 Kalos"),
        (Region.ALOLA, "阿羅拉 Alola"),
        (Region.GALAR, "伽勒爾 Galar"),
        (Region.PALDEA, "帕底亞 Paldea"),
    ]

    current_lower = current.lower()
    choices = []

    for region_enum, display_name in regions:
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
        display_name, route_id = service.format_route_choice(route, status, kills)

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

        display_name, route_id = service.format_route_choice(route, status, kills)

        if current_lower in display_name.lower() or current_lower in route.name.lower():
            choices.append(app_commands.Choice(name=display_name, value=route_id))

    return choices[:25]


async def gym_autocomplete(
    interaction: Interaction, current: str
) -> list[app_commands.Choice[str]]:
    """Autocomplete for gym selection.

    Shows available gyms in the current region with badge status.
    """
    from funbot.db.models.pokemon.gym_data import GymData, PlayerBadge

    # Yield control for async
    await asyncio.sleep(0)

    # Get region from namespace (default to Kanto)
    namespace = interaction.namespace
    region = getattr(namespace, "region", 0)
    user_id = interaction.user.id

    # Get gyms for region
    gyms = await GymData.filter(region=region).order_by("id").limit(25).all()

    # Get player badges
    player_badges = await PlayerBadge.filter(user_id=user_id).values_list(
        "badge", flat=True
    )
    player_badge_set = {str(b) for b in player_badges}

    current_lower = current.lower()
    choices = []

    for gym in gyms:
        has_badge = gym.badge in player_badge_set
        status = "🏅" if has_badge else "⚔️"
        is_elite = "👑 " if gym.is_elite else ""
        display_name = f"{status} {is_elite}{gym.name} - {gym.leader}"

        if current_lower in display_name.lower() or current_lower in gym.name.lower():
            choices.append(app_commands.Choice(name=display_name[:100], value=gym.name))

    return choices[:25]


async def dungeon_autocomplete(
    interaction: Interaction, current: str
) -> list[app_commands.Choice[str]]:
    """Autocomplete for dungeon selection.

    Shows available dungeons in the current region with status indicators:
    - 🔒 Locked
    - ⚔️ Available (not cleared)
    - ✅ Cleared

    Requires 'region' parameter to be filled first (defaults to Kanto).
    """
    from funbot.db.models.pokemon.dungeon_data import DungeonData, PlayerDungeonProgress

    # Yield control for async
    await asyncio.sleep(0)

    # Get region from namespace (default to Kanto)
    namespace = interaction.namespace
    region = getattr(namespace, "region", 0)
    user_id = interaction.user.id

    # Get dungeons for region
    dungeons = await DungeonData.filter(region=region).order_by("id").limit(25).all()

    # Get player progress
    progress_list = (
        await PlayerDungeonProgress.filter(
            player_id=user_id,
            dungeon__region=region,
        )
        .prefetch_related("dungeon")
        .all()
    )

    progress_map = {p.dungeon.id: p.clears for p in progress_list}

    current_lower = current.lower()
    choices = []

    for dungeon in dungeons:
        clears = progress_map.get(dungeon.id, 0)

        # Determine status
        if clears > 0:
            status = "✅"
            suffix = f" ({clears}次)"
        else:
            status = "⚔️"
            suffix = ""

        display_name = f"{status} {dungeon.name}{suffix}"

        if (
            current_lower in display_name.lower()
            or current_lower in dungeon.name.lower()
        ):
            choices.append(
                app_commands.Choice(name=display_name[:100], value=dungeon.name)
            )

    return choices[:25]
