from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "pokemon_temporary_battle_data" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "display_name" VARCHAR(100) NOT NULL,
    "region" INT NOT NULL DEFAULT -1,
    "defeat_message" TEXT,
    "return_town" VARCHAR(100),
    "image_name" VARCHAR(100),
    "reset_daily" BOOL NOT NULL DEFAULT False
);
COMMENT ON TABLE "pokemon_temporary_battle_data" IS 'Storage for temporary battle data parsed from Pokeclicker TemporaryBattleList.ts.';
        CREATE TABLE IF NOT EXISTS "pokemon_player_battle_progress" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "defeats" INT NOT NULL DEFAULT 0,
    "last_defeated" TIMESTAMPTZ,
    "battle_id" INT NOT NULL REFERENCES "pokemon_temporary_battle_data" ("id") ON DELETE CASCADE,
    "player_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_pokemon_pla_player__a7ee78" UNIQUE ("player_id", "battle_id")
);
COMMENT ON TABLE "pokemon_player_battle_progress" IS 'Track player''s temporary battle defeats.';
        CREATE TABLE IF NOT EXISTS "pokemon_temporary_battle_pokemon" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "pokemon_name" VARCHAR(100) NOT NULL,
    "health" INT NOT NULL,
    "level" INT NOT NULL,
    "shiny" BOOL NOT NULL DEFAULT False,
    "order" INT NOT NULL DEFAULT 0,
    "battle_id" INT NOT NULL REFERENCES "pokemon_temporary_battle_data" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "pokemon_temporary_battle_pokemon" IS 'Pokemon in a temporary battle.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "pokemon_temporary_battle_pokemon";
        DROP TABLE IF EXISTS "pokemon_temporary_battle_data";
        DROP TABLE IF EXISTS "pokemon_player_battle_progress";"""


MODELS_STATE = (
    "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"
    "XA58uqys5qbZD+6/8B/Lmysg=="
)
