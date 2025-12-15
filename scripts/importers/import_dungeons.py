"""Import dungeons from dungeons_data_v3.json to database.

Updated for v3 JSON structure with enemies/trainers/requirements.
Now properly imports DungeonTrainer and DungeonTrainerPokemon records.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from tortoise import Tortoise
from tortoise.transactions import in_transaction

from funbot.db.config import TORTOISE_CONFIG
from funbot.db.models.pokemon.dungeon_data import (
    DungeonData,
    DungeonLoot,
    DungeonPokemon,
    DungeonTrainer,
    DungeonTrainerPokemon,
)

logger = logging.getLogger(__name__)


async def import_trainer(
    dungeon: DungeonData, trainer_json: dict, is_boss: bool
) -> tuple[int, int]:
    """Import a single trainer and their Pokemon team.

    Args:
        dungeon: The dungeon this trainer belongs to
        trainer_json: The trainer data from JSON
        is_boss: Whether this trainer is a boss

    Returns:
        Tuple of (trainer_count, trainer_pokemon_count)
    """
    # Create the trainer record
    trainer = await DungeonTrainer.create(
        dungeon=dungeon,
        trainer_class=trainer_json.get("trainerClass", "Unknown"),
        trainer_name=trainer_json.get("name"),
        weight=trainer_json.get("weight", 1),
        is_boss=is_boss,
    )

    # Create trainer's Pokemon team
    trainer_pokemon_count = 0
    for order, team_member in enumerate(trainer_json.get("team", [])):
        await DungeonTrainerPokemon.create(
            trainer=trainer,
            pokemon_name=team_member["name"],
            health=team_member.get("health", 0),
            level=team_member.get("level", 1),
            order=order,
        )
        trainer_pokemon_count += 1

    return 1, trainer_pokemon_count


async def import_dungeons(trainers_only: bool = False) -> None:
    """Import dungeon data from JSON file.

    This imports:
    - DungeonData: Basic dungeon info
    - DungeonPokemon: Wild Pokemon encounters and boss Pokemon
    - DungeonTrainer: Trainer encounters with their teams
    - DungeonTrainerPokemon: Pokemon in trainer teams
    - DungeonLoot: Loot table entries

    Args:
        trainers_only: If True, only import trainer data for existing dungeons.
                       Useful when dungeons already exist but trainers need to be added.
    """
    json_path = Path(__file__).parent.parent / "data" / "dungeons_data_v3.json"

    if not json_path.exists():
        logger.error("dungeons_data_v3.json not found")
        return

    with json_path.open(encoding="utf-8") as f:
        dungeons_data = json.load(f)

    if trainers_only:
        logger.info(
            "Importing trainers for %d dungeons (trainers only mode)...",
            len(dungeons_data),
        )
    else:
        logger.info("Importing %d dungeons...", len(dungeons_data))

    dungeon_count = 0
    pokemon_count = 0
    trainer_count = 0
    trainer_pokemon_count = 0
    loot_count = 0

    for dg_json in dungeons_data:
        if trainers_only:
            # In trainers_only mode, look up existing dungeon by name
            dungeon = await DungeonData.get_or_none(name=dg_json["name"])
            if dungeon is None:
                logger.warning("Dungeon not found: %s, skipping", dg_json["name"])
                continue
        else:
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
                if not trainers_only:
                    await DungeonPokemon.create(
                        dungeon=dungeon,
                        pokemon_name=enemy["name"],
                        weight=enemy.get("weight", 1),
                        is_boss=False,
                    )
                    pokemon_count += 1
            elif enemy.get("type") == "DungeonTrainer":
                # Import trainer with their team using the new models
                t_count, tp_count = await import_trainer(dungeon, enemy, is_boss=False)
                trainer_count += t_count
                trainer_pokemon_count += tp_count

        # Import bosses
        for boss in dg_json.get("bosses", []):
            if boss.get("type") == "DungeonBossPokemon":
                if not trainers_only:
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
                # Import boss trainer with their team using the new models
                t_count, tp_count = await import_trainer(dungeon, boss, is_boss=True)
                trainer_count += t_count
                trainer_pokemon_count += tp_count
            elif boss.get("generated") and not trainers_only:
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
        if not trainers_only:
            loot_table = dg_json.get("loot", {})
            for tier, items in loot_table.items():
                for item in items:
                    await DungeonLoot.create(
                        dungeon=dungeon,
                        item_name=item["item"],
                        tier=tier,
                        weight=item.get("weight", 1),
                    )
                    loot_count += 1

        if dungeon_count % 30 == 0:
            logger.info("  Progress: %d/%d dungeons", dungeon_count, len(dungeons_data))

    logger.info("✅ Dungeon import complete!")
    logger.info("   - Dungeons: %d", dungeon_count)
    logger.info("   - Wild Pokemon: %d", pokemon_count)
    logger.info("   - Trainers: %d", trainer_count)
    logger.info("   - Trainer Pokemon: %d", trainer_pokemon_count)
    logger.info("   - Loot entries: %d", loot_count)


async def main(trainers_only: bool = False) -> None:
    """Run dungeon import with database.

    Args:
        trainers_only: If True, only import trainer data for existing dungeons.
    """
    await Tortoise.init(config=TORTOISE_CONFIG)
    await Tortoise.generate_schemas(safe=True)

    try:
        async with in_transaction():
            await import_dungeons(trainers_only=trainers_only)
        logger.info("✅ Transaction committed!")
    except Exception:
        logger.exception("❌ Import failed")
        raise
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    # Check for --trainers-only flag
    trainers_only = "--trainers-only" in sys.argv

    asyncio.run(main(trainers_only=trainers_only))
