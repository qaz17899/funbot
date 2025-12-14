"""Import temporary battles from temporary_battles_data.json to database."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from tortoise import Tortoise
from tortoise.transactions import in_transaction

from funbot.db.config import TORTOISE_CONFIG
from funbot.db.models.pokemon.temporary_battle_data import (
    TemporaryBattleData,
    TemporaryBattlePokemon,
)

logger = logging.getLogger(__name__)


async def import_temporary_battles() -> None:
    """Import temporary battle data from JSON file."""
    json_path = Path(__file__).parent.parent / "data" / "temporary_battles_data_final.json"

    if not json_path.exists():
        logger.error("temporary_battles_data_final.json not found")
        return

    with json_path.open(encoding="utf-8") as f:
        battles_data = json.load(f)

    logger.info("Importing %d temporary battles...", len(battles_data))

    battle_count = 0
    pokemon_count = 0

    for battle_json in battles_data:
        # Create battle
        battle = await TemporaryBattleData.create(
            name=battle_json["name"],
            display_name=battle_json.get("displayName") or battle_json["name"],
            region=battle_json.get("region", -1),
            defeat_message=battle_json.get("defeatMessage"),
            return_town=battle_json.get("returnTown"),
            image_name=battle_json.get("imageName"),
            reset_daily=battle_json.get("resetDaily", False),
        )
        battle_count += 1

        # Create battle pokemon
        for i, pmon in enumerate(battle_json.get("pokemon", [])):
            await TemporaryBattlePokemon.create(
                battle=battle,
                pokemon_name=pmon["name"],
                health=pmon["health"],
                level=pmon["level"],
                shiny=pmon.get("shiny", False),
                order=i,
            )
            pokemon_count += 1

        if battle_count % 50 == 0:
            logger.info("  Progress: %d/%d battles", battle_count, len(battles_data))

    logger.info("✅ Temporary battle import complete!")
    logger.info("   - Battles: %d", battle_count)
    logger.info("   - Pokemon: %d", pokemon_count)


async def main() -> None:
    """Run temporary battle import with database."""
    await Tortoise.init(config=TORTOISE_CONFIG)
    await Tortoise.generate_schemas(safe=True)

    try:
        async with in_transaction():
            await import_temporary_battles()
        logger.info("✅ Transaction committed!")
    except Exception:
        logger.exception("❌ Import failed")
        raise
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
