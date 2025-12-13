"""PokeAPI data importer script.

Run this script once to import Pokemon data from PokeAPI into the database.
This will create entries in the PokemonData table for all Gen 1-9 Pokemon.

Usage:
    python -m scripts.import_pokemon_data
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from tortoise import Tortoise

from funbot.db.models.pokemon import PokemonData
from funbot.pokemon.constants.enums import PokemonType, Region

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PokeAPI endpoints
POKEAPI_BASE = "https://pokeapi.co/api/v2"

# Name mapping for PokemonType enum
TYPE_NAME_TO_ENUM: dict[str, int] = {
    "normal": PokemonType.NORMAL,
    "fire": PokemonType.FIRE,
    "water": PokemonType.WATER,
    "electric": PokemonType.ELECTRIC,
    "grass": PokemonType.GRASS,
    "ice": PokemonType.ICE,
    "fighting": PokemonType.FIGHTING,
    "poison": PokemonType.POISON,
    "ground": PokemonType.GROUND,
    "flying": PokemonType.FLYING,
    "psychic": PokemonType.PSYCHIC,
    "bug": PokemonType.BUG,
    "rock": PokemonType.ROCK,
    "ghost": PokemonType.GHOST,
    "dragon": PokemonType.DRAGON,
    "dark": PokemonType.DARK,
    "steel": PokemonType.STEEL,
    "fairy": PokemonType.FAIRY,
}

# Generation to Region mapping
GEN_TO_REGION: dict[int, int] = {
    1: Region.KANTO,
    2: Region.JOHTO,
    3: Region.HOENN,
    4: Region.SINNOH,
    5: Region.UNOVA,
    6: Region.KALOS,
    7: Region.ALOLA,
    8: Region.GALAR,
    9: Region.PALDEA,
}

# Dex ID ranges per generation
GEN_RANGES: dict[int, tuple[int, int]] = {
    1: (1, 151),
    2: (152, 251),
    3: (252, 386),
    4: (387, 493),
    5: (494, 649),
    6: (650, 721),
    7: (722, 809),
    8: (810, 905),
    9: (906, 1025),
}


def get_generation(pokemon_id: int) -> int:
    """Get generation number from Pokemon ID."""
    for gen, (start, end) in GEN_RANGES.items():
        if start <= pokemon_id <= end:
            return gen
    return 9  # Default to latest gen for unknown


async def fetch_pokemon_data(client: httpx.AsyncClient, pokemon_id: int) -> dict[str, Any] | None:
    """Fetch Pokemon data from PokeAPI."""
    try:
        response = await client.get(f"{POKEAPI_BASE}/pokemon/{pokemon_id}")
        if response.status_code == 200:
            return response.json()
        logger.warning(f"Failed to fetch Pokemon {pokemon_id}: {response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching Pokemon {pokemon_id}: {e}")
    return None


async def fetch_species_data(client: httpx.AsyncClient, pokemon_id: int) -> dict[str, Any] | None:
    """Fetch Pokemon species data for evolution info."""
    try:
        response = await client.get(f"{POKEAPI_BASE}/pokemon-species/{pokemon_id}")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None


def parse_pokemon_data(data: dict[str, Any], species_data: dict | None) -> dict:
    """Parse PokeAPI response into PokemonData fields."""
    # Get types
    types = data.get("types", [])
    type1 = TYPE_NAME_TO_ENUM.get(types[0]["type"]["name"], PokemonType.NORMAL)
    type2 = None
    if len(types) > 1:
        type2 = TYPE_NAME_TO_ENUM.get(types[1]["type"]["name"])

    # Get stats
    stats = {s["stat"]["name"]: s["base_stat"] for s in data.get("stats", [])}

    # Get sprites
    sprites = data.get("sprites", {})
    sprite_url = sprites.get("front_default")
    sprite_shiny_url = sprites.get("front_shiny")

    # Get evolution info from species data
    evolves_from = None
    if species_data:
        evo_from = species_data.get("evolves_from_species")
        if evo_from:
            # Extract ID from URL
            url = evo_from.get("url", "")
            if url:
                evolves_from = int(url.rstrip("/").split("/")[-1])

    pokemon_id = data["id"]
    generation = get_generation(pokemon_id)

    return {
        "id": pokemon_id,
        "name": data["name"].replace("-", " ").title(),
        "type1": type1,
        "type2": type2,
        "base_hp": stats.get("hp", 50),
        "base_attack": stats.get("attack", 50),
        "base_defense": stats.get("defense", 50),
        "base_sp_attack": stats.get("special-attack", 50),
        "base_sp_defense": stats.get("special-defense", 50),
        "base_speed": stats.get("speed", 50),
        "catch_rate": species_data.get("capture_rate", 45) if species_data else 45,
        "base_exp": data.get("base_experience") or 50,
        "egg_cycles": species_data.get("hatch_counter", 20) if species_data else 20,
        "sprite_url": sprite_url,
        "sprite_shiny_url": sprite_shiny_url,
        "generation": generation,
        "region": GEN_TO_REGION.get(generation, Region.KANTO),
        "evolves_from": evolves_from,
        "evolution_level": None,  # Could parse from evo chain but complex
    }


async def import_pokemon(start_id: int = 1, end_id: int = 1025) -> None:
    """Import Pokemon from PokeAPI to database."""
    logger.info(f"Importing Pokemon {start_id} to {end_id}...")

    # Use the same config as aerich for consistency
    from funbot.db.aerich_config import TORTOISE_CONFIG

    await Tortoise.init(config=TORTOISE_CONFIG)
    await Tortoise.generate_schemas(safe=True)  # safe=True won't drop existing tables

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Process in batches to avoid rate limiting
        batch_size = 20
        for batch_start in range(start_id, end_id + 1, batch_size):
            batch_end = min(batch_start + batch_size - 1, end_id)
            logger.info(f"Processing batch {batch_start}-{batch_end}...")

            tasks = []
            for pokemon_id in range(batch_start, batch_end + 1):
                tasks.append(process_pokemon(client, pokemon_id))

            await asyncio.gather(*tasks)

            # Small delay between batches
            await asyncio.sleep(0.5)

    await Tortoise.close_connections()
    logger.info("Import complete!")


async def process_pokemon(client: httpx.AsyncClient, pokemon_id: int) -> None:
    """Process a single Pokemon."""
    # Check if already exists
    existing = await PokemonData.filter(id=pokemon_id).first()
    if existing:
        logger.debug(f"Pokemon {pokemon_id} already exists, skipping")
        return

    # Fetch data
    data = await fetch_pokemon_data(client, pokemon_id)
    if not data:
        return

    species_data = await fetch_species_data(client, pokemon_id)

    # Parse and save
    pokemon_dict = parse_pokemon_data(data, species_data)
    await PokemonData.create(**pokemon_dict)
    logger.info(f"Imported: #{pokemon_id} {pokemon_dict['name']}")


async def main() -> None:
    """Main entry point."""
    import sys

    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 1025

    await import_pokemon(start, end)


if __name__ == "__main__":
    asyncio.run(main())
