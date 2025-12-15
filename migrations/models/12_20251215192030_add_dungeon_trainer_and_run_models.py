from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "pokemon_dungeon_trainer" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "trainer_class" VARCHAR(100) NOT NULL,
    "trainer_name" VARCHAR(100),
    "weight" INT NOT NULL DEFAULT 1,
    "is_boss" BOOL NOT NULL DEFAULT False,
    "dungeon_id" INT NOT NULL REFERENCES "pokemon_dungeon_data" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "pokemon_dungeon_trainer" IS 'Trainer encounters in a dungeon.';
        CREATE TABLE IF NOT EXISTS "pokemon_dungeon_trainer_pokemon" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "pokemon_name" VARCHAR(100) NOT NULL,
    "health" BIGINT NOT NULL,
    "level" INT NOT NULL,
    "order" INT NOT NULL DEFAULT 0,
    "trainer_id" INT NOT NULL REFERENCES "pokemon_dungeon_trainer" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "pokemon_dungeon_trainer_pokemon" IS 'Pokemon in a dungeon trainer''s team.';
        CREATE TABLE IF NOT EXISTS "pokemon_player_dungeon_run" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "started_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "map_data" JSONB NOT NULL,
    "current_position" JSONB NOT NULL,
    "chests_opened" INT NOT NULL DEFAULT 0,
    "enemies_defeated" INT NOT NULL DEFAULT 0,
    "loot_collected" JSONB NOT NULL,
    "status" VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    "dungeon_id" INT NOT NULL REFERENCES "pokemon_dungeon_data" ("id") ON DELETE CASCADE,
    "player_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "pokemon_player_dungeon_run"."map_data" IS 'Serialized map state with tiles and visibility';
COMMENT ON COLUMN "pokemon_player_dungeon_run"."current_position" IS 'Player position {x, y, floor}';
COMMENT ON COLUMN "pokemon_player_dungeon_run"."loot_collected" IS 'List of collected loot items';
COMMENT ON TABLE "pokemon_player_dungeon_run" IS 'Active dungeon run session.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "pokemon_dungeon_trainer_pokemon";
        DROP TABLE IF EXISTS "pokemon_player_dungeon_run";
        DROP TABLE IF EXISTS "pokemon_dungeon_trainer";"""


MODELS_STATE = (
    "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"
    "h//T87dCdU"
)
