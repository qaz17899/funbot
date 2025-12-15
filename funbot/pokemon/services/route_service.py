"""Route status service for computing route unlock status and progress.

Implements PokéClicker's route status system:
- Locked: Requirements not met
- Incomplete: Kills < ROUTE_KILLS_NEEDED (10)
- Uncaught Pokemon: Has new Pokemon to catch
- Uncaught Shiny: Missing shiny variants
- Completed: All conditions met

Based on PokéClicker's MapHelper.calculateRouteCssClass().
"""

from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from loguru import logger

from funbot.db.models.pokemon import PlayerPokemon, PlayerRouteProgress, RouteData
from funbot.pokemon.constants.game_constants import ROUTE_KILLS_NEEDED
from funbot.pokemon.services.requirement_service import get_requirement_service

if TYPE_CHECKING:
    from funbot.db.models.pokemon.route_requirement import RouteRequirement


class RouteStatus(IntEnum):
    """Route status matching PokéClicker's areaStatus.

    Fixed priority order (highest to lowest):
    1. LOCKED - Can't access yet
    2. INCOMPLETE - Kills < 10
    3. QUEST_AT_LOCATION - Has active quest (not implemented yet)
    4. UNCAUGHT_POKEMON - Has new Pokemon
    5. UNCAUGHT_SHINY - Missing shiny variants
    6. COMPLETED - Everything done
    """

    LOCKED = 0
    INCOMPLETE = 1
    QUEST_AT_LOCATION = 2
    UNCAUGHT_POKEMON = 3
    UNCAUGHT_SHINY = 4
    COMPLETED = 5


class RouteStatusService:
    """Service for computing route status and progress.

    Implements the same logic as PokéClicker's MapHelper.
    """

    def __init__(self) -> None:
        self._requirement_service = get_requirement_service()

    async def get_route_status(
        self, player_id: int, route: RouteData
    ) -> tuple[RouteStatus, int]:
        """Get the status and kill count for a route.

        Args:
            player_id: The player's user ID
            route: The route to check

        Returns:
            Tuple of (RouteStatus, kills_count)
        """
        logger.debug("Checking route status: player={} route={}", player_id, route.name)

        # Get or create player progress for this route
        progress, created = await PlayerRouteProgress.get_or_create(
            user_id=player_id, route=route
        )
        kills = progress.kills
        if created:
            logger.debug("Created new progress record for route {}", route.name)

        # 1. Check if locked (requirements not met)
        is_unlocked = await self.is_route_unlocked(player_id, route)
        if not is_unlocked:
            logger.debug("Route {} is LOCKED for player {}", route.name, player_id)
            return RouteStatus.LOCKED, kills

        # 2. Check if incomplete (kills < 10)
        if kills < ROUTE_KILLS_NEEDED:
            logger.debug(
                "Route {} is INCOMPLETE: {}/{} kills",
                route.name,
                kills,
                ROUTE_KILLS_NEEDED,
            )
            return RouteStatus.INCOMPLETE, kills

        # 3. Quest at location (skip for now - quest system not fully integrated)
        # TODO: Check if there's an active quest at this route
        # Issue URL: https://github.com/qaz17899/funbot/issues/22

        # 4 & 5. Check for uncaught Pokemon
        uncaught_status = await self._check_uncaught_pokemon(player_id, route)
        if uncaught_status is not None:
            logger.debug(
                "Route {} has uncaught pokemon: status={}",
                route.name,
                uncaught_status.name,
            )
            return uncaught_status, kills

        # 6. Completed
        logger.debug("Route {} is COMPLETED for player {}", route.name, player_id)
        return RouteStatus.COMPLETED, kills

    async def is_route_unlocked(self, player_id: int, route: RouteData) -> bool:
        """Check if a route is unlocked for a player.

        Args:
            player_id: The player's user ID
            route: The route to check

        Returns:
            True if the route is unlocked
        """
        # Get the root requirement for this route
        requirements = await route.requirements.filter(parent=None).prefetch_related(
            "children", "children__children"
        )

        if not requirements:
            # No requirements = unlocked from start
            logger.debug(
                "Route {} has no requirements, unlocked by default", route.name
            )
            return True

        # Check each root requirement (they're implicitly AND'd)
        for requirement in requirements:
            if not await self._requirement_service.check_requirement(
                player_id, requirement
            ):
                logger.debug(
                    "Route {} locked: requirement {} not met",
                    route.name,
                    requirement.requirement_type,
                )
                return False

        logger.debug(
            "Route {} unlocked: all {} requirements met", route.name, len(requirements)
        )
        return True

    async def get_requirement_hints(
        self, player_id: int, route: RouteData
    ) -> list[str]:
        """Get hints for unmet requirements.

        Args:
            player_id: The player's user ID
            route: The route to check

        Returns:
            List of requirement hint strings
        """
        hints = []
        requirements = await route.requirements.filter(parent=None).prefetch_related(
            "children", "children__children"
        )

        for requirement in requirements:
            if not await self._requirement_service.check_requirement(
                player_id, requirement
            ):
                hint = self._get_requirement_hint(requirement)
                if hint:
                    hints.append(hint)

        return hints

    def _get_requirement_hint(self, requirement: RouteRequirement) -> str | None:
        """Generate a human-readable hint for a requirement."""
        from funbot.db.models.pokemon.route_requirement import RequirementType

        req_type = RequirementType(requirement.requirement_type)
        params = requirement.parameters or {}

        match req_type:
            case RequirementType.ROUTE_KILL:
                route = params.get("route", "?")
                amount = params.get("amount", 10)
                return f"在路線 {route} 擊敗 {amount} 隻寶可夢"
            case RequirementType.GYM_BADGE:
                badge = params.get("badge", "?")
                return f"需要 {badge} 徽章"
            case RequirementType.DUNGEON_CLEAR:
                dungeon = params.get("dungeon", "?")
                return f"通關 {dungeon}"
            case RequirementType.TEMP_BATTLE:
                battle = params.get("battle", "?")
                return f"擊敗 {battle}"
            case RequirementType.QUEST_LINE_COMPLETED:
                quest = params.get("quest", "?")
                return f"完成任務線: {quest}"
            case _:
                return None

    async def _check_uncaught_pokemon(
        self, player_id: int, route: RouteData
    ) -> RouteStatus | None:
        """Check if there are uncaught Pokemon on this route.

        Returns RouteStatus.UNCAUGHT_POKEMON, UNCAUGHT_SHINY, or None if all caught.
        """
        # Get all Pokemon that appear on this route
        all_pokemon_names: set[str] = set()
        all_pokemon_names.update(route.land_pokemon or [])
        all_pokemon_names.update(route.water_pokemon or [])
        all_pokemon_names.update(route.headbutt_pokemon or [])

        if not all_pokemon_names:
            return None

        # Get player's caught Pokemon
        caught_pokemon = await PlayerPokemon.filter(user_id=player_id).values_list(
            "pokemon_data__name", "shiny"
        )

        caught_names = {name for name, _ in caught_pokemon}
        caught_shiny_names = {name for name, shiny in caught_pokemon if shiny}

        # Check for uncaught Pokemon
        uncaught = all_pokemon_names - caught_names
        if uncaught:
            return RouteStatus.UNCAUGHT_POKEMON

        # Check for uncaught shiny
        uncaught_shiny = all_pokemon_names - caught_shiny_names
        if uncaught_shiny:
            return RouteStatus.UNCAUGHT_SHINY

        return None

    async def get_available_routes_for_region(
        self, player_id: int, region: int
    ) -> list[tuple[RouteData, RouteStatus, int]]:
        """Get all routes in a region with their status.

        Args:
            player_id: The player's user ID
            region: Region index (0=Kanto, 1=Johto, etc.)

        Returns:
            List of (RouteData, RouteStatus, kills) tuples, ordered by order_number
        """
        routes = await RouteData.filter(region=region, is_implemented=True).order_by(
            "order_number"
        )

        results = []
        for route in routes:
            status, kills = await self.get_route_status(player_id, route)
            results.append((route, status, kills))

        return results


# Singleton instance
_route_status_service: RouteStatusService | None = None


def get_route_status_service() -> RouteStatusService:
    """Get the singleton RouteStatusService instance."""
    global _route_status_service
    if _route_status_service is None:
        _route_status_service = RouteStatusService()
    return _route_status_service
