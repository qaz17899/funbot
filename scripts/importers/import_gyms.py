"""Import gyms from gyms_data.json to database."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from tortoise import Tortoise
from tortoise.transactions import in_transaction

from funbot.db.config import TORTOISE_CONFIG
from funbot.db.models.pokemon.gym_data import GymData, GymPokemon

logger = logging.getLogger(__name__)


async def import_gyms() -> None:
    """Import gym data from JSON file."""
    json_path = Path(__file__).parent.parent / "data" / "gyms_data.json"

    if not json_path.exists():
        logger.error("gyms_data.json not found")
        return

    with json_path.open(encoding="utf-8") as f:
        gyms_data = json.load(f)

    logger.info("Importing %d gyms...", len(gyms_data))

    gym_count = 0
    pokemon_count = 0

    for gym_json in gyms_data:
        # Create gym
        gym = await GymData.create(
            name=gym_json["town"],
            leader=gym_json["leader"] or "Unknown",
            region=gym_json["region"] or 0,
            badge=gym_json["badge"] or "",
            badge_id=gym_json["badge_id"],
            money_reward=gym_json["money_reward"] or 0,
            defeat_message=gym_json["defeat_message"],
            is_elite=gym_json["is_elite"],
        )
        gym_count += 1

        # Create gym pokemon
        for i, pmon in enumerate(gym_json.get("pokemon", [])):
            await GymPokemon.create(
                gym=gym,
                pokemon_name=pmon["name"],
                max_health=pmon["max_health"],
                level=pmon["level"],
                order=i,
            )
            pokemon_count += 1

        if gym_count % 20 == 0:
            logger.info("  Progress: %d/%d gyms", gym_count, len(gyms_data))

    logger.info("✅ Gym import complete!")
    logger.info("   - Gyms: %d", gym_count)
    logger.info("   - Pokemon: %d", pokemon_count)


async def main() -> None:
    """Run gym import with database."""
    await Tortoise.init(config=TORTOISE_CONFIG)
    await Tortoise.generate_schemas(safe=True)

    try:
        async with in_transaction():
            await import_gyms()
        logger.info("✅ Transaction committed!")
    except Exception:
        logger.exception("❌ Import failed")
        raise
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
