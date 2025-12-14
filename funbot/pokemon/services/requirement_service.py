"""RequirementService - Evaluates route unlock requirements.

This service implements the same logic as Pokeclicker's Requirement system:
- Multi(Requirement) = AND - all children must pass
- OneFromMany(Requirement) = OR - any child must pass
- Base pattern: getProgress() >= requiredValue
"""

from __future__ import annotations

from datetime import UTC, datetime

from loguru import logger

from funbot.db.models.pokemon.route_requirement import RequirementType, RouteRequirement


class RequirementService:
    """Evaluates requirements for route unlocks.

    Implements Pokeclicker's requirement checking with 100% parity:
    - MultiRequirement: ALL children must be completed (AND)
    - OneFromManyRequirement: ANY child must be completed (OR)
    - Other requirements: getProgress() >= requiredValue
    """

    async def check_requirement(self, player_id: int, requirement: RouteRequirement) -> bool:
        """Recursively check if a requirement is met.

        Args:
            player_id: The player to check requirements for
            requirement: The root requirement node to evaluate

        Returns:
            True if requirement is satisfied, False otherwise
        """
        req_type = requirement.requirement_type
        params = requirement.parameters or {}

        # Compound requirements (tree logic)
        if req_type == RequirementType.MULTI:
            return await self._check_multi(player_id, requirement)
        if req_type == RequirementType.ONE_FROM_MANY:
            return await self._check_one_from_many(player_id, requirement)

        # Leaf requirements (data checks)
        match req_type:
            case RequirementType.ROUTE_KILL:
                return await self._check_route_kill(player_id, params)
            case RequirementType.GYM_BADGE:
                return await self._check_gym_badge(player_id, params)
            case RequirementType.DUNGEON_CLEAR:
                return await self._check_dungeon_clear(player_id, params)
            case RequirementType.TEMP_BATTLE:
                return await self._check_temp_battle(player_id, params)
            case RequirementType.QUEST_LINE_COMPLETED:
                return await self._check_quest_completed(player_id, params)
            case RequirementType.QUEST_LINE_STEP:
                return await self._check_quest_step(player_id, params)
            case RequirementType.OBTAINED_POKEMON:
                return await self._check_obtained_pokemon(player_id, params)
            case RequirementType.WEATHER:
                return self._check_weather(params)
            case RequirementType.DAY_OF_WEEK:
                return self._check_day_of_week(params)
            case RequirementType.SPECIAL_EVENT:
                return self._check_special_event(params)
            case _:
                # Unknown requirement type - log and return True (permissive)
                logger.warning(
                    "Unknown requirement type %s for player %s, defaulting to True",
                    req_type,
                    player_id,
                )
                return True

    # =========================================================================
    # COMPOUND REQUIREMENTS (Tree Logic)
    # =========================================================================

    async def _check_multi(self, player_id: int, requirement: RouteRequirement) -> bool:
        """MultiRequirement: ALL children must be completed (AND logic).

        Matches Pokeclicker: requirements.every(r => r.isCompleted())
        """
        children = await requirement.children.all()
        if not children:
            logger.debug("MULTI requirement {}: no children, satisfied", requirement.id)
            return True  # No children = satisfied

        for child in children:
            if not await self.check_requirement(player_id, child):
                logger.debug("MULTI requirement {}: child {} failed", requirement.id, child.id)
                return False
        logger.debug("MULTI requirement {}: all {} children passed", requirement.id, len(children))
        return True

    async def _check_one_from_many(self, player_id: int, requirement: RouteRequirement) -> bool:
        """OneFromManyRequirement: ANY child must be completed (OR logic).

        Matches Pokeclicker: requirements.some(r => r.isCompleted())
        """
        children = await requirement.children.all()
        if not children:
            logger.debug("ONE_FROM_MANY requirement {}: no children, satisfied", requirement.id)
            return True  # No children = satisfied

        for child in children:
            if await self.check_requirement(player_id, child):
                logger.debug(
                    "ONE_FROM_MANY requirement {}: child {} passed", requirement.id, child.id
                )
                return True
        logger.debug("ONE_FROM_MANY requirement {}: no children passed", requirement.id)
        return False

    # =========================================================================
    # ROUTE-RELATED REQUIREMENTS
    # =========================================================================

    async def _check_route_kill(self, player_id: int, params: dict) -> bool:
        """Check if player has killed enough Pokemon on a route.

        Pokeclicker: App.game.statistics.routeKills[region][route]() >= value
        """
        from funbot.db.models.pokemon.player_route_progress import PlayerRouteProgress

        region = params.get("region")
        route = params.get("route")
        amount = params.get("amount", 10)  # Default: 10 kills

        progress = await PlayerRouteProgress.filter(
            user_id=player_id, route__region=region, route__number=route
        ).first()

        kills = progress.kills if progress else 0
        return kills >= amount

    async def _check_gym_badge(self, player_id: int, params: dict) -> bool:
        """Check if player has a specific gym badge.

        Pokeclicker: App.game.badgeCase.hasBadge(badge)
        """
        from funbot.db.models.pokemon.gym_data import PlayerBadge

        badge_name = params.get("badge")
        if not badge_name:
            return True

        # Check if player has this badge
        return await PlayerBadge.filter(player_id=player_id, badge=badge_name).exists()

    async def _check_dungeon_clear(self, player_id: int, params: dict) -> bool:
        """Check if player has cleared a dungeon enough times.

        Pokeclicker: App.game.statistics.dungeonsCleared[index]() >= value
        """
        from funbot.db.models.pokemon.dungeon_data import DungeonData, PlayerDungeonProgress

        dungeon_name = params.get("dungeon")
        clears_required = params.get("clears", 1)

        if not dungeon_name:
            return True

        # Find dungeon
        dungeon = await DungeonData.filter(name=dungeon_name).first()
        if not dungeon:
            logger.warning("Dungeon '%s' not found in database", dungeon_name)
            return True  # Permissive if dungeon not found

        # Get player progress
        progress = await PlayerDungeonProgress.filter(
            player_id=player_id, dungeon_id=dungeon.id
        ).first()

        player_clears = progress.clears if progress else 0
        return player_clears >= clears_required

    async def _check_temp_battle(self, player_id: int, params: dict) -> bool:
        """Check if player has defeated a temporary battle.

        Pokeclicker: temporaryBattleDefeated[index]() >= value
        """
        from funbot.db.models.pokemon.temporary_battle_data import (
            PlayerBattleProgress,
            TemporaryBattleData,
        )

        battle_name = params.get("battle")
        defeats_required = params.get("defeats", 1)

        if not battle_name:
            return True

        # Find battle
        battle = await TemporaryBattleData.filter(name=battle_name).first()
        if not battle:
            logger.warning("TemporaryBattle '%s' not found in database", battle_name)
            return True  # Permissive if battle not found

        # Get player progress
        progress = await PlayerBattleProgress.filter(
            player_id=player_id, battle_id=battle.id
        ).first()

        player_defeats = progress.defeats if progress else 0
        return player_defeats >= defeats_required

    # =========================================================================
    # QUEST REQUIREMENTS
    # =========================================================================

    async def _check_quest_completed(self, player_id: int, params: dict) -> bool:
        """Check if player has completed a quest line.

        Pokeclicker: quest.state() === QuestLineState.ended
        """
        from funbot.db.models.pokemon.player_quest_progress import (
            PlayerQuestProgress,
            QuestLineState,
        )

        quest_name = params.get("quest")
        if not quest_name:
            return True

        progress = await PlayerQuestProgress.filter(
            player__id=player_id, quest_line__name=quest_name
        ).first()

        if not progress:
            return False

        return progress.state == QuestLineState.ENDED

    async def _check_quest_step(self, player_id: int, params: dict) -> bool:
        """Check if player has completed a specific quest step.

        Pokeclicker: quest.curQuestInitial() > step (with option support)

        Options:
        - "more" (default): current_step >= step
        - "less": current_step < step
        - "equal": current_step == step
        """
        from funbot.db.models.pokemon.player_quest_progress import PlayerQuestProgress

        quest_name = params.get("quest")
        step_required = params.get("step", 0)
        option = params.get("option", "more")

        if not quest_name:
            return True

        progress = await PlayerQuestProgress.filter(
            player__id=player_id, quest_line__name=quest_name
        ).first()

        # If no progress, treat as step -1 (not started)
        current_step = progress.current_quest_index if progress else -1

        match option:
            case "less":
                return current_step < step_required
            case "equal":
                return current_step == step_required
            case _:  # "more" or default
                return current_step >= step_required

    # =========================================================================
    # COLLECTION REQUIREMENTS
    # =========================================================================

    async def _check_obtained_pokemon(self, player_id: int, params: dict) -> bool:
        """Check if player has obtained a specific Pokemon.

        Pokeclicker: App.game.party.caughtPokemon.some(p => p.name == name)
        """
        from funbot.db.models.pokemon.player_pokemon import PlayerPokemon

        pokemon_name = params.get("pokemon")
        if not pokemon_name:
            return True

        return await PlayerPokemon.filter(player_id=player_id, pokemon__name=pokemon_name).exists()

    # =========================================================================
    # CONDITIONAL REQUIREMENTS (Real-time checks)
    # =========================================================================

    def _check_weather(self, params: dict) -> bool:
        """Check if current weather matches requirement.

        Pokeclicker: weather.includes(Weather.currentWeather())

        Note: Weather system not implemented. Returns True for now.
        """
        # TODO: Implement weather system
        # Issue URL: https://github.com/qaz17899/funbot/issues/21
        return True

    def _check_day_of_week(self, params: dict) -> bool:
        """Check if current day matches requirement.

        Pokeclicker: days.includes(today)
        """
        days = params.get("days", [])
        if not days:
            return True

        # Get current day name
        today = datetime.now(tz=UTC).strftime("%A")  # e.g., "Monday"
        return today in days

    def _check_special_event(self, params: dict) -> bool:
        """Check if a special event is currently active.

        Pokeclicker: SpecialEvent.isActive(eventName)

        Note: Event system not implemented. Returns False (events disabled).
        """
        # TODO: Implement event system
        # Issue URL: https://github.com/qaz17899/funbot/issues/20
        # Events are seasonal, return False for now
        return False


# Singleton instance
_requirement_service: RequirementService | None = None


def get_requirement_service() -> RequirementService:
    """Get the singleton RequirementService instance."""
    global _requirement_service
    if _requirement_service is None:
        _requirement_service = RequirementService()
    return _requirement_service
