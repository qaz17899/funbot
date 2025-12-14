"""Hatchery service for breeding Pokemon.

Based on Pokeclicker Breeding.ts and Egg.ts.
Handles egg slots, steps progress, hatching, and Pokerus spreading.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from funbot.db.models.pokemon import PlayerEgg, PlayerPokemon, PokemonData
from funbot.pokemon.constants import PokerusState
from funbot.pokemon.constants.game_constants import (
    BREEDING_ATTACK_BONUS,
    BREEDING_SHINY_ATTACK_MULTIPLIER,
    DEFAULT_EGG_SLOTS,
    EGG_CYCLE_MULTIPLIER,
    MAX_EGG_SLOTS,
    SHINY_CHANCE_BREEDING,
)

if TYPE_CHECKING:
    from funbot.db.models.user import User


@dataclass
class HatchResult:
    """Result of hatching an egg."""

    pokemon_name: str
    shiny: bool
    attack_bonus_percent: int
    attack_bonus_amount: int
    pokerus_upgraded: bool  # INFECTED -> CONTAGIOUS


class HatcheryService:
    """Service for managing the hatchery and breeding.

    Key mechanics from Pokeclicker:
    - 4 egg slots max (start with 1)
    - Steps-based progress (from battles)
    - Pokerus spreading (same type matching)
    - Attack bonus on hatch
    """

    @staticmethod
    async def get_egg_slots(user: User) -> int:
        """Get number of egg slots for user.

        TODO: Track in user preferences/progress model.
        For now, return default.
        """
        return DEFAULT_EGG_SLOTS

    @staticmethod
    async def get_eggs(user: User) -> list[PlayerEgg]:
        """Get all eggs in user's hatchery."""
        return await PlayerEgg.filter(user=user).prefetch_related("pokemon_data").all()

    @staticmethod
    async def has_free_slot(user: User) -> bool:
        """Check if user has a free egg slot."""
        current_eggs = await PlayerEgg.filter(user=user).count()
        slots = await HatcheryService.get_egg_slots(user)
        return current_eggs < slots

    @staticmethod
    async def add_to_hatchery(
        user: User, pokemon: PlayerPokemon, pokemon_data: PokemonData
    ) -> PlayerEgg | None:
        """Add a Pokemon to the hatchery.

        Args:
            user: The user
            pokemon: The PlayerPokemon to breed
            pokemon_data: The PokemonData for egg cycles

        Returns:
            The created PlayerEgg or None if no slots
        """
        if pokemon.breeding:
            return None

        if not await HatcheryService.has_free_slot(user):
            return None

        # Find next available slot
        current_eggs = await PlayerEgg.filter(user=user).all()
        used_slots = {egg.slot for egg in current_eggs}

        slot = None
        for i in range(MAX_EGG_SLOTS):
            if i not in used_slots:
                slot = i
                break

        if slot is None:
            return None

        # Calculate steps required with Carbos reduction
        # From PartyPokemon.ts:419-423:
        # extraCycles = (calcium + protein) / 2
        # steps = eggCycles * 40
        # if steps > 300: steps = ((steps/300)^(1 - carbos/70)) * 300
        egg_cycles = pokemon_data.egg_cycles if hasattr(pokemon_data, "egg_cycles") else 20
        extra_cycles = (pokemon.vitamin_calcium + pokemon.vitamin_protein) / 2
        base_steps = int((egg_cycles + extra_cycles) * EGG_CYCLE_MULTIPLIER)

        # Apply Carbos reduction (only affects steps > 300)
        carbos = pokemon.vitamin_carbos
        div = 300
        if base_steps <= div or carbos == 0:
            steps_required = base_steps
        else:
            # Carbos reduces steps using exponential formula
            steps_required = int(((base_steps / div) ** (1 - carbos / 70)) * div)

        # Create egg
        egg = await PlayerEgg.create(
            user=user,
            pokemon_data=pokemon_data,
            slot=slot,
            steps=0,
            steps_required=steps_required,
            shiny_chance=SHINY_CHANCE_BREEDING,
        )

        # Mark Pokemon as breeding
        pokemon.breeding = True
        await pokemon.save()

        return egg

    @staticmethod
    async def progress_eggs(user: User, steps: int) -> list[PlayerEgg]:
        """Progress all eggs by given steps.

        Also handles Pokerus spreading.

        Args:
            user: The user
            steps: Number of steps to add

        Returns:
            List of eggs that are now ready to hatch
        """
        eggs = await HatcheryService.get_eggs(user)
        ready_eggs: list[PlayerEgg] = []

        # Spread Pokerus first (before adding steps)
        await HatcheryService._spread_pokerus(user, eggs)

        # Add steps to each egg
        for egg in eggs:
            if not egg.can_hatch:
                egg.add_steps(steps)
                await egg.save()

            if egg.can_hatch:
                ready_eggs.append(egg)

        return ready_eggs

    @staticmethod
    async def _spread_pokerus(user: User, eggs: list[PlayerEgg]) -> None:
        """Spread Pokerus between eggs of same type.

        From PartyPokemon.calculatePokerus() lines 181-192:
        - Find types of all CONTAGIOUS+ eggs
        - Infect UNINFECTED eggs that share a type
        """
        if not eggs:
            return

        # Get all contagious Pokemon types from eggs
        contagious_types: set[int] = set()
        for egg in eggs:
            # Get the party pokemon for this egg
            party_pokemon = await PlayerPokemon.filter(
                user=user, pokemon_data=egg.pokemon_data
            ).first()
            if party_pokemon and party_pokemon.pokerus >= PokerusState.CONTAGIOUS:
                data = egg.pokemon_data
                contagious_types.add(data.type1)
                if data.type2:
                    contagious_types.add(data.type2)

        if not contagious_types:
            return

        # Infect uninfected eggs that share a type
        for egg in eggs:
            party_pokemon = await PlayerPokemon.filter(
                user=user, pokemon_data=egg.pokemon_data
            ).first()
            if party_pokemon and party_pokemon.pokerus == PokerusState.UNINFECTED:
                data = egg.pokemon_data
                if data.type1 in contagious_types or (
                    data.type2 and data.type2 in contagious_types
                ):
                    party_pokemon.pokerus = PokerusState.INFECTED
                    await party_pokemon.save()

    @staticmethod
    async def hatch_egg(egg: PlayerEgg) -> HatchResult | None:
        """Hatch an egg and apply bonuses.

        From Egg.hatch() lines 120-200:
        - Calculate shiny
        - Add attack bonuses
        - Upgrade Pokerus INFECTED -> CONTAGIOUS
        - Update statistics
        """
        if not egg.can_hatch:
            return None

        # Get party Pokemon (use prefetched pokemon_data)
        party_pokemon = await PlayerPokemon.filter(
            user=egg.user, pokemon_data=egg.pokemon_data
        ).first()

        if not party_pokemon:
            return None

        # Use prefetched pokemon_data instead of querying by ID
        pokemon_data: PokemonData = egg.pokemon_data  # type: ignore

        # Roll for shiny
        shiny = random.randint(1, egg.shiny_chance) == 1

        # Calculate bonuses with vitamins (from PartyPokemon.ts:426-428)
        # attackBonusPercent += (BREEDING_ATTACK_BONUS + calcium)
        # attackBonusAmount += protein
        shiny_mult = BREEDING_SHINY_ATTACK_MULTIPLIER if shiny else 1
        calcium_bonus = party_pokemon.vitamin_calcium
        protein_bonus = party_pokemon.vitamin_protein
        bonus_percent = (BREEDING_ATTACK_BONUS + calcium_bonus) * shiny_mult
        bonus_amount = protein_bonus * shiny_mult

        # Apply bonuses
        party_pokemon.attack_bonus_percent += bonus_percent
        party_pokemon.attack_bonus_amount += bonus_amount

        # Reset breeding state
        party_pokemon.breeding = False
        party_pokemon.exp = 0
        party_pokemon.level = 1

        # Upgrade Pokerus
        pokerus_upgraded = False
        if party_pokemon.pokerus == PokerusState.INFECTED:
            party_pokemon.pokerus = PokerusState.CONTAGIOUS
            pokerus_upgraded = True

        # Update statistics
        if shiny:
            party_pokemon.stat_shiny_hatched += 1
        party_pokemon.stat_hatched += 1

        await party_pokemon.save()

        # Delete egg
        await egg.delete()

        return HatchResult(
            pokemon_name=pokemon_data.name,
            shiny=shiny,
            attack_bonus_percent=bonus_percent,
            attack_bonus_amount=bonus_amount,
            pokerus_upgraded=pokerus_upgraded,
        )

    @staticmethod
    async def hatch_all_ready(user: User) -> list[HatchResult]:
        """Hatch all ready eggs for a user."""
        eggs = await HatcheryService.get_eggs(user)
        results: list[HatchResult] = []

        for egg in eggs:
            if egg.can_hatch:
                result = await HatcheryService.hatch_egg(egg)
                if result:
                    results.append(result)

        return results

    @staticmethod
    def calculate_steps_from_route(normalized_route: float) -> int:
        """Calculate steps from route battle.

        From Breeding.progressEggsBattle() + Routes.normalizedNumber():
        - normalizedRoute = route's order index (1, 2, 3...) not route number
        - steps = sqrt(normalizedRoute)

        Args:
            normalized_route: RouteData.order_number (e.g., 1.0, 2.0, 3.5)

        Returns:
            Steps per battle on this route
        """
        return max(1, int(math.sqrt(normalized_route)))
