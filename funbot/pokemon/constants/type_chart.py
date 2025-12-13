"""Pokemon type effectiveness chart.

Based on Gen 6+ type chart (includes Fairy type).
Values:
- 0.0 = Immune (no effect)
- 0.5 = Not very effective
- 1.0 = Normal effectiveness
- 2.0 = Super effective
"""

from __future__ import annotations

from funbot.pokemon.constants.enums import PokemonType

# Type effectiveness matrix [attacker][defender]
# Index matches PokemonType enum values (1-18, index 0 is NONE)
TYPE_EFFECTIVENESS: dict[PokemonType, dict[PokemonType, float]] = {
    PokemonType.NORMAL: {PokemonType.ROCK: 0.5, PokemonType.GHOST: 0.0, PokemonType.STEEL: 0.5},
    PokemonType.FIRE: {
        PokemonType.FIRE: 0.5,
        PokemonType.WATER: 0.5,
        PokemonType.GRASS: 2.0,
        PokemonType.ICE: 2.0,
        PokemonType.BUG: 2.0,
        PokemonType.ROCK: 0.5,
        PokemonType.DRAGON: 0.5,
        PokemonType.STEEL: 2.0,
    },
    PokemonType.WATER: {
        PokemonType.FIRE: 2.0,
        PokemonType.WATER: 0.5,
        PokemonType.GRASS: 0.5,
        PokemonType.GROUND: 2.0,
        PokemonType.ROCK: 2.0,
        PokemonType.DRAGON: 0.5,
    },
    PokemonType.ELECTRIC: {
        PokemonType.WATER: 2.0,
        PokemonType.ELECTRIC: 0.5,
        PokemonType.GRASS: 0.5,
        PokemonType.GROUND: 0.0,
        PokemonType.FLYING: 2.0,
        PokemonType.DRAGON: 0.5,
    },
    PokemonType.GRASS: {
        PokemonType.FIRE: 0.5,
        PokemonType.WATER: 2.0,
        PokemonType.GRASS: 0.5,
        PokemonType.POISON: 0.5,
        PokemonType.GROUND: 2.0,
        PokemonType.FLYING: 0.5,
        PokemonType.BUG: 0.5,
        PokemonType.ROCK: 2.0,
        PokemonType.DRAGON: 0.5,
        PokemonType.STEEL: 0.5,
    },
    PokemonType.ICE: {
        PokemonType.FIRE: 0.5,
        PokemonType.WATER: 0.5,
        PokemonType.GRASS: 2.0,
        PokemonType.ICE: 0.5,
        PokemonType.GROUND: 2.0,
        PokemonType.FLYING: 2.0,
        PokemonType.DRAGON: 2.0,
        PokemonType.STEEL: 0.5,
    },
    PokemonType.FIGHTING: {
        PokemonType.NORMAL: 2.0,
        PokemonType.ICE: 2.0,
        PokemonType.POISON: 0.5,
        PokemonType.FLYING: 0.5,
        PokemonType.PSYCHIC: 0.5,
        PokemonType.BUG: 0.5,
        PokemonType.ROCK: 2.0,
        PokemonType.GHOST: 0.0,
        PokemonType.DARK: 2.0,
        PokemonType.STEEL: 2.0,
        PokemonType.FAIRY: 0.5,
    },
    PokemonType.POISON: {
        PokemonType.GRASS: 2.0,
        PokemonType.POISON: 0.5,
        PokemonType.GROUND: 0.5,
        PokemonType.ROCK: 0.5,
        PokemonType.GHOST: 0.5,
        PokemonType.STEEL: 0.0,
        PokemonType.FAIRY: 2.0,
    },
    PokemonType.GROUND: {
        PokemonType.FIRE: 2.0,
        PokemonType.ELECTRIC: 2.0,
        PokemonType.GRASS: 0.5,
        PokemonType.POISON: 2.0,
        PokemonType.FLYING: 0.0,
        PokemonType.BUG: 0.5,
        PokemonType.ROCK: 2.0,
        PokemonType.STEEL: 2.0,
    },
    PokemonType.FLYING: {
        PokemonType.ELECTRIC: 0.5,
        PokemonType.GRASS: 2.0,
        PokemonType.FIGHTING: 2.0,
        PokemonType.BUG: 2.0,
        PokemonType.ROCK: 0.5,
        PokemonType.STEEL: 0.5,
    },
    PokemonType.PSYCHIC: {
        PokemonType.FIGHTING: 2.0,
        PokemonType.POISON: 2.0,
        PokemonType.PSYCHIC: 0.5,
        PokemonType.DARK: 0.0,
        PokemonType.STEEL: 0.5,
    },
    PokemonType.BUG: {
        PokemonType.FIRE: 0.5,
        PokemonType.GRASS: 2.0,
        PokemonType.FIGHTING: 0.5,
        PokemonType.POISON: 0.5,
        PokemonType.FLYING: 0.5,
        PokemonType.PSYCHIC: 2.0,
        PokemonType.GHOST: 0.5,
        PokemonType.DARK: 2.0,
        PokemonType.STEEL: 0.5,
        PokemonType.FAIRY: 0.5,
    },
    PokemonType.ROCK: {
        PokemonType.FIRE: 2.0,
        PokemonType.ICE: 2.0,
        PokemonType.FIGHTING: 0.5,
        PokemonType.GROUND: 0.5,
        PokemonType.FLYING: 2.0,
        PokemonType.BUG: 2.0,
        PokemonType.STEEL: 0.5,
    },
    PokemonType.GHOST: {
        PokemonType.NORMAL: 0.0,
        PokemonType.PSYCHIC: 2.0,
        PokemonType.GHOST: 2.0,
        PokemonType.DARK: 0.5,
    },
    PokemonType.DRAGON: {PokemonType.DRAGON: 2.0, PokemonType.STEEL: 0.5, PokemonType.FAIRY: 0.0},
    PokemonType.DARK: {
        PokemonType.FIGHTING: 0.5,
        PokemonType.PSYCHIC: 2.0,
        PokemonType.GHOST: 2.0,
        PokemonType.DARK: 0.5,
        PokemonType.FAIRY: 0.5,
    },
    PokemonType.STEEL: {
        PokemonType.FIRE: 0.5,
        PokemonType.WATER: 0.5,
        PokemonType.ELECTRIC: 0.5,
        PokemonType.ICE: 2.0,
        PokemonType.ROCK: 2.0,
        PokemonType.STEEL: 0.5,
        PokemonType.FAIRY: 2.0,
    },
    PokemonType.FAIRY: {
        PokemonType.FIRE: 0.5,
        PokemonType.FIGHTING: 2.0,
        PokemonType.POISON: 0.5,
        PokemonType.DRAGON: 2.0,
        PokemonType.DARK: 2.0,
        PokemonType.STEEL: 0.5,
    },
}


def get_type_effectiveness(
    attacker_type: PokemonType,
    defender_type1: PokemonType,
    defender_type2: PokemonType = PokemonType.NONE,
) -> float:
    """Calculate type effectiveness multiplier.

    Args:
        attacker_type: The attacking Pokemon's type
        defender_type1: The defending Pokemon's primary type
        defender_type2: The defending Pokemon's secondary type (optional)

    Returns:
        Effectiveness multiplier (0.0, 0.25, 0.5, 1.0, 2.0, or 4.0)
    """
    if attacker_type == PokemonType.NONE:
        return 1.0

    # Get effectiveness against first type
    type_chart = TYPE_EFFECTIVENESS.get(attacker_type, {})
    eff1 = type_chart.get(defender_type1, 1.0)

    # Get effectiveness against second type
    if defender_type2 != PokemonType.NONE:
        eff2 = type_chart.get(defender_type2, 1.0)
        return eff1 * eff2

    return eff1


def get_attack_modifier(
    attacker_type1: PokemonType,
    attacker_type2: PokemonType,
    defender_type1: PokemonType,
    defender_type2: PokemonType = PokemonType.NONE,
) -> float:
    """Calculate total attack modifier based on both attacker types.

    Uses the better of the two type matchups (like Pokeclicker).

    Args:
        attacker_type1: Attacker's primary type
        attacker_type2: Attacker's secondary type
        defender_type1: Defender's primary type
        defender_type2: Defender's secondary type

    Returns:
        Best effectiveness multiplier from either attacker type
    """
    eff1 = get_type_effectiveness(attacker_type1, defender_type1, defender_type2)
    eff2 = get_type_effectiveness(attacker_type2, defender_type1, defender_type2)

    # Return the better matchup
    return max(eff1, eff2)
