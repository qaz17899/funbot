"""Catch service for calculating catch rates and executing catch sequences.

Based on Pokeclicker mechanics:
- Catch rate = (base_catch_rate^0.75) + pokeball_bonus
- Catch attempt is automatic after defeating enemy
- Ball used depends on player settings
- Duplicate catches award EVs and Dungeon Tokens
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import IntEnum

from loguru import logger

from funbot.pokemon.constants.enums import POKEBALL_BONUS, Pokeball, PokerusState
from funbot.pokemon.constants.game_constants import (
    BASE_CATCH_RATE,
    BASE_EP_YIELD,
    DUNGEON_EP_YIELD,
    SHINY_CHANCE,
    SHINY_EP_MODIFIER,
)


class CatchContext(IntEnum):
    """Context where catch occurs, affects EP yield."""

    ROUTE = 1  # Standard route encounter (BASE_EP_YIELD = 100)
    DUNGEON = 2  # Dungeon encounter (DUNGEON_EP_YIELD = 300)
    SAFARI = 3  # Safari zone (SAFARI_EP_YIELD = 1000)
    SHOP = 4  # Shop purchase (SHOPMON_EP_YIELD = 1000)


# EP yields per context (from GameConstants.ts:428-441)
CONTEXT_EP_YIELDS: dict[CatchContext, int] = {
    CatchContext.ROUTE: BASE_EP_YIELD,  # 100
    CatchContext.DUNGEON: DUNGEON_EP_YIELD,  # 300
    CatchContext.SAFARI: 1000,
    CatchContext.SHOP: 1000,
}


@dataclass
class CatchAttemptResult:
    """Result of a catch attempt."""

    success: bool
    pokeball_used: Pokeball
    catch_rate: float


@dataclass
class CatchSequenceResult:
    """Complete result of a catch sequence transaction."""

    # Core result
    success: bool
    pokeball_used: Pokeball = Pokeball.NONE
    catch_rate: float = 0.0

    # Pokemon info
    pokemon_name: str = ""
    pokemon_id: int = 0
    is_new: bool = False
    is_shiny: bool = False

    # Rewards (for duplicates)
    effort_points_earned: int = 0
    dungeon_tokens_earned: int = 0

    # Status changes
    pokerus_evolved: bool = False  # CONTAGIOUS -> RESISTANT

    # Statistics updated
    stats_updated: dict[str, int] = field(default_factory=dict)

    @property
    def skipped(self) -> bool:
        """Returns True if no ball was thrown (settings or no inventory)."""
        return self.pokeball_used == Pokeball.NONE


class CatchService:
    """Service for catch calculations and complete catch sequences."""

    # =========================================================================
    # Core Calculation Methods (Pure functions, no DB)
    # =========================================================================

    @staticmethod
    def calculate_catch_rate(base_catch_rate: int, pokeball: Pokeball) -> float:
        """Calculate actual catch rate.

        Formula: (base_catch_rate^0.75) + pokeball_bonus
        Result is clamped to 0-100.

        Args:
            base_catch_rate: Pokemon's base catch rate (0-255)
            pokeball: Pokeball being used

        Returns:
            Catch rate as percentage (0-100)
        """
        if pokeball == Pokeball.NONE:
            return 0.0

        if pokeball == Pokeball.MASTERBALL:
            return 100.0

        # Apply formula
        rate = pow(base_catch_rate, BASE_CATCH_RATE) + POKEBALL_BONUS[pokeball]

        # Clamp to 0-100
        return max(0.0, min(100.0, rate))

    @staticmethod
    def attempt_catch(base_catch_rate: int, pokeball: Pokeball) -> CatchAttemptResult:
        """Attempt to catch a Pokemon (pure calculation).

        Args:
            base_catch_rate: Pokemon's base catch rate
            pokeball: Pokeball to use

        Returns:
            CatchAttemptResult with success status
        """
        catch_rate = CatchService.calculate_catch_rate(base_catch_rate, pokeball)
        success = random.random() * 100 < catch_rate

        return CatchAttemptResult(
            success=success, pokeball_used=pokeball, catch_rate=catch_rate
        )

    @staticmethod
    def get_pokeball_for_pokemon(
        settings: dict, is_new: bool, is_shiny: bool
    ) -> Pokeball:
        """Get which pokeball to use based on player settings.

        Args:
            settings: Player's pokeball settings dict
            is_new: True if Pokemon not yet in party
            is_shiny: True if Pokemon is shiny

        Returns:
            Pokeball to use (NONE if should not attempt catch)
        """
        if is_new and is_shiny:
            return Pokeball(settings.get("new_shiny", Pokeball.ULTRABALL))
        if is_new:
            return Pokeball(settings.get("new_pokemon", Pokeball.POKEBALL))
        if is_shiny:
            return Pokeball(settings.get("caught_shiny", Pokeball.POKEBALL))
        return Pokeball(settings.get("caught_pokemon", Pokeball.NONE))

    @staticmethod
    def find_available_ball(
        preferred_ball: Pokeball,
        get_quantity_fn: callable,
    ) -> Pokeball | None:
        """Find available ball with fallback to lower tiers.

        Args:
            preferred_ball: The preferred ball type
            get_quantity_fn: Function that returns quantity for a ball type

        Returns:
            Available Pokeball or None if no balls available
        """
        # Fallback priority: Preferred -> Ultra -> Great -> Poke
        for ball_type in [Pokeball.ULTRABALL, Pokeball.GREATBALL, Pokeball.POKEBALL]:
            if ball_type <= preferred_ball and get_quantity_fn(ball_type) > 0:
                return ball_type
        return None

    @staticmethod
    def roll_shiny(shiny_chance: int = SHINY_CHANCE) -> bool:
        """Roll for shiny encounter.

        Args:
            shiny_chance: The 1 in N chance (default: SHINY_CHANCE_BATTLE=8192)

        Returns:
            True if shiny
        """
        return random.randint(1, shiny_chance) == 1

    @staticmethod
    def calculate_effort_points(
        context: CatchContext,
        is_shiny: bool = False,
    ) -> int:
        """Calculate effort points earned from a catch.

        Args:
            context: Where the catch occurred
            is_shiny: If the caught Pokemon was shiny (5x multiplier)

        Returns:
            Effort points to award
        """
        base_ep = CONTEXT_EP_YIELDS.get(context, BASE_EP_YIELD)

        if is_shiny:
            base_ep *= SHINY_EP_MODIFIER

        return base_ep

    # =========================================================================
    # Complete Catch Sequence (Full transaction with DB)
    # =========================================================================

    @staticmethod
    async def perform_catch_sequence(
        player_id: int,
        pokemon_name: str,
        *,
        shiny_chance: int = SHINY_CHANCE,
        context: CatchContext = CatchContext.ROUTE,
        pre_rolled_shiny: bool | None = None,
        route_number: int = 1,
        region: int = 0,
    ) -> CatchSequenceResult:
        """Execute a complete catch sequence transaction.

        This is the SINGLE SOURCE OF TRUTH for all catch operations.
        Handles the complete lifecycle:
        1. Check existing ownership (New/Duplicate)
        2. Roll for shiny (or use pre-rolled value)
        3. Determine ball type from settings
        4. Check and deduct ball inventory
        5. Calculate and execute catch attempt
        6. For NEW Pokemon: Create PlayerPokemon record
        7. For DUPLICATE Pokemon:
           - Award Effort Points (EVs)
           - Award Dungeon Tokens
           - Update Pokerus status
        8. Update all statistics

        Args:
            player_id: The player's user ID
            pokemon_name: Name of the Pokemon to catch
            shiny_chance: Context-specific shiny chance
            context: Where the catch is occurring (affects EP yield)
            pre_rolled_shiny: If provided, use this instead of rolling
            route_number: Route number for token calculation
            region: Region for token calculation

        Returns:
            CatchSequenceResult with complete status and rewards
        """
        from funbot.db.models.pokemon import PlayerPokeballSettings, PlayerPokemon
        from funbot.db.models.pokemon.player_ball_inventory import PlayerBallInventory
        from funbot.db.models.pokemon.player_wallet import PlayerWallet
        from funbot.db.models.pokemon.pokemon_data import PokemonData
        from funbot.pokemon.services.battle_service import BattleService

        result = CatchSequenceResult(success=False, pokemon_name=pokemon_name)

        # 1. Get Pokemon Data
        pokemon_data = await PokemonData.filter(name=pokemon_name).first()
        if not pokemon_data:
            logger.warning(f"Pokemon not found: {pokemon_name}")
            return result

        result.pokemon_id = pokemon_data.id

        # 2. Check Ownership
        existing = await PlayerPokemon.filter(
            user_id=player_id, pokemon_data_id=pokemon_data.id
        ).first()
        is_new = existing is None
        result.is_new = is_new

        # 3. Determine Shiny (use pre-rolled or roll now)
        if pre_rolled_shiny is not None:
            is_shiny = pre_rolled_shiny
        else:
            is_shiny = CatchService.roll_shiny(shiny_chance)
        result.is_shiny = is_shiny

        # 4. Get Ball Settings
        settings, _ = await PlayerPokeballSettings.get_or_create(user_id=player_id)
        preferred_ball = CatchService.get_pokeball_for_pokemon(
            settings.to_dict(), is_new, is_shiny
        )

        if preferred_ball == Pokeball.NONE:
            # Player doesn't want to catch this type
            return result

        # 5. Check Ball Inventory
        inventory, _ = await PlayerBallInventory.get_or_create(user_id=player_id)
        actual_ball = CatchService.find_available_ball(
            preferred_ball, inventory.get_quantity
        )

        if actual_ball is None:
            # No balls available
            return result

        # 6. Consume Ball
        await inventory.use_ball(actual_ball)
        result.pokeball_used = actual_ball

        # 7. Attempt Catch
        attempt = CatchService.attempt_catch(pokemon_data.catch_rate, actual_ball)
        result.catch_rate = attempt.catch_rate
        result.success = attempt.success

        if not attempt.success:
            # Catch failed - ball consumed but no rewards
            return result

        # === CATCH SUCCESSFUL ===

        # 8. Calculate Dungeon Tokens (awarded on ALL successful catches)
        tokens_earned = BattleService.calculate_dungeon_tokens(route_number, region)
        result.dungeon_tokens_earned = tokens_earned

        # 9. Handle NEW Pokemon
        if is_new:
            new_pokemon = await PlayerPokemon.create(
                user_id=player_id,
                pokemon_data_id=pokemon_data.id,
                shiny=is_shiny,
                stat_captured=1,
                stat_shiny_captured=1 if is_shiny else 0,
            )
            logger.info(
                f"Player {player_id} caught new {pokemon_name} (shiny={is_shiny})"
            )
            result.stats_updated = {"stat_captured": 1}
            if is_shiny:
                result.stats_updated["stat_shiny_captured"] = 1

        # 10. Handle DUPLICATE Pokemon
        else:
            # Calculate EP
            ep_earned = CatchService.calculate_effort_points(context, is_shiny)
            result.effort_points_earned = ep_earned

            # Update existing Pokemon
            existing.stat_captured += 1
            if is_shiny:
                existing.stat_shiny_captured += 1
                # Upgrade to shiny if caught shiny version
                if not existing.shiny:
                    existing.shiny = True

            # Award EVs (only if Pokerus >= CONTAGIOUS)
            if existing.can_gain_evs:
                existing.effort_points += ep_earned

                # Check Pokerus Evolution (CONTAGIOUS -> RESISTANT at 50 EVs)
                if existing.pokerus == PokerusState.CONTAGIOUS and existing.evs >= 50:
                    existing.pokerus = PokerusState.RESISTANT
                    result.pokerus_evolved = True

            await existing.save()

            result.stats_updated = {"stat_captured": existing.stat_captured}
            if is_shiny:
                result.stats_updated["stat_shiny_captured"] = (
                    existing.stat_shiny_captured
                )

            logger.debug(
                f"Player {player_id} re-caught {pokemon_name} "
                f"(EP={ep_earned}, tokens={tokens_earned})"
            )

        # 11. Award Dungeon Tokens to Wallet
        if tokens_earned > 0:
            wallet, _ = await PlayerWallet.get_or_create(user_id=player_id)
            await wallet.add_dungeon_token(tokens_earned)

        return result
