"""Import dungeons from dungeons_data_v3.json to database.

Updated for v3 JSON structure with enemies/trainers/requirements.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from tortoise import Tortoise
from tortoise.transactions import in_transaction

from funbot.db.config import TORTOISE_CONFIG
from funbot.db.models.pokemon.dungeon_data import DungeonData, DungeonLoot, DungeonPokemon

logger = logging.getLogger(__name__)


async def import_dungeons() -> None:
    """Import dungeon data from JSON file."""
    json_path = Path(__file__).parent.parent / "data" / "dungeons_data_v3.json"

    if not json_path.exists():
        logger.error("dungeons_data_v3.json not found")
        return

    with json_path.open(encoding="utf-8") as f:
        dungeons_data = json.load(f)

    logger.info("Importing %d dungeons...", len(dungeons_data))

    dungeon_count = 0
    pokemon_count = 0
    loot_count = 0

    for dg_json in dungeons_data:
        # Create dungeon
        dungeon = await DungeonData.create(
            name=dg_json["name"],
            region=dg_json["region"],
            base_health=dg_json.get("baseHealth") or 0,
            token_cost=dg_json.get("tokenCost") or 0,
        )
        dungeon_count += 1

        # Import enemies (can be Pokemon or DungeonTrainer)
        for enemy in dg_json.get("enemies", []):
            if enemy.get("type") == "Pokemon":
                await DungeonPokemon.create(
                    dungeon=dungeon,
                    pokemon_name=enemy["name"],
                    weight=enemy.get("weight", 1),
                    is_boss=False,
                )
                pokemon_count += 1
            elif enemy.get("type") == "DungeonTrainer":
                # For trainers, save the trainer name and team info
                for team_member in enemy.get("team", []):
                    await DungeonPokemon.create(
                        dungeon=dungeon,
                        pokemon_name=team_member["name"],
                        weight=enemy.get("weight", 1),
                        is_boss=False,
                        health=team_member.get("health"),
                        level=team_member.get("level"),
                    )
                    pokemon_count += 1

        # Import bosses
        for boss in dg_json.get("bosses", []):
            if boss.get("type") == "DungeonBossPokemon":
                await DungeonPokemon.create(
                    dungeon=dungeon,
                    pokemon_name=boss["name"],
                    weight=1,
                    is_boss=True,
                    health=boss.get("health"),
                    level=boss.get("level"),
                )
                pokemon_count += 1
            elif boss.get("type") == "DungeonTrainer":
                # Boss trainers
                for team_member in boss.get("team", []):
                    await DungeonPokemon.create(
                        dungeon=dungeon,
                        pokemon_name=team_member["name"],
                        weight=boss.get("weight", 1),
                        is_boss=True,
                        health=team_member.get("health"),
                        level=team_member.get("level"),
                    )
                    pokemon_count += 1
            elif boss.get("generated"):
                # Generated Unown bosses
                await DungeonPokemon.create(
                    dungeon=dungeon,
                    pokemon_name=boss["name"],
                    weight=1,
                    is_boss=True,
                    health=boss.get("health"),
                    level=boss.get("level"),
                )
                pokemon_count += 1

        # Import loot entries
        loot_table = dg_json.get("loot", {})
        for tier, items in loot_table.items():
            for item in items:
                await DungeonLoot.create(
                    dungeon=dungeon, item_name=item["item"], tier=tier, weight=item.get("weight", 1)
                )
                loot_count += 1

        if dungeon_count % 30 == 0:
            logger.info("  Progress: %d/%d dungeons", dungeon_count, len(dungeons_data))

    logger.info("✅ Dungeon import complete!")
    logger.info("   - Dungeons: %d", dungeon_count)
    logger.info("   - Pokemon: %d", pokemon_count)
    logger.info("   - Loot entries: %d", loot_count)


async def main() -> None:
    """Run dungeon import with database."""
    await Tortoise.init(config=TORTOISE_CONFIG)
    await Tortoise.generate_schemas(safe=True)

    try:
        async with in_transaction():
            await import_dungeons()
        logger.info("✅ Transaction committed!")
    except Exception:
        logger.exception("❌ Import failed")
        raise
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
