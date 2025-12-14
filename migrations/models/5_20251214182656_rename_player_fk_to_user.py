from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "pokemon_player_dungeon_progress" DROP CONSTRAINT IF EXISTS "uid_pokemon_pla_player_d38134";
        ALTER TABLE "pokemon_player_dungeon_progress" DROP CONSTRAINT IF EXISTS "fk_pokemon__users_9fb968b5";
        ALTER TABLE "pokemon_player_battle_progress" DROP CONSTRAINT IF EXISTS "uid_pokemon_pla_player_b0013c";
        ALTER TABLE "pokemon_player_battle_progress" DROP CONSTRAINT IF EXISTS "fk_pokemon__users_34915abb";
        ALTER TABLE "pokemon_player_badges" DROP CONSTRAINT IF EXISTS "uid_pokemon_pla_player_0a8c64";
        ALTER TABLE "pokemon_player_badges" DROP CONSTRAINT IF EXISTS "fk_pokemon__users_7a5b93b9";
        CREATE TABLE IF NOT EXISTS "pokemon_quest_line_data" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(128) NOT NULL UNIQUE,
    "description" TEXT NOT NULL,
    "bulletin_board" VARCHAR(32) NOT NULL DEFAULT 'None',
    "total_quests" SMALLINT NOT NULL DEFAULT 0,
    "root_requirement_id" INT REFERENCES "pokemon_route_requirement" ("id") ON DELETE SET NULL
);
COMMENT ON TABLE "pokemon_quest_line_data" IS 'Static quest line data parsed from Pokeclicker.';
        CREATE TABLE IF NOT EXISTS "pokemon_player_quest_progress" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "state" SMALLINT NOT NULL DEFAULT 0,
    "current_quest_index" SMALLINT NOT NULL DEFAULT 0,
    "started_at" TIMESTAMPTZ,
    "completed_at" TIMESTAMPTZ,
    "quest_line_id" INT NOT NULL REFERENCES "pokemon_quest_line_data" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_pokemon_pla_user_id_9e8236" UNIQUE ("user_id", "quest_line_id")
);
COMMENT ON TABLE "pokemon_player_quest_progress" IS 'Track player''s progress through quest lines.';
        CREATE TABLE IF NOT EXISTS "pokemon_quest_data" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "quest_index" SMALLINT NOT NULL,
    "quest_type" VARCHAR(64) NOT NULL,
    "description" TEXT NOT NULL,
    "amount" INT NOT NULL DEFAULT 1,
    "points_reward" INT NOT NULL DEFAULT 0,
    "type_data" JSONB,
    "has_custom_reward" BOOL NOT NULL DEFAULT False,
    "quest_line_id" INT NOT NULL REFERENCES "pokemon_quest_line_data" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "pokemon_quest_data"."type_data" IS 'Quest type-specific parameters';
COMMENT ON TABLE "pokemon_quest_data" IS 'Individual quest within a quest line.';
        ALTER TABLE "pokemon_player_badges" RENAME COLUMN "player_id" TO "user_id";
        ALTER TABLE "pokemon_player_battle_progress" RENAME COLUMN "player_id" TO "user_id";
        ALTER TABLE "pokemon_player_dungeon_progress" RENAME COLUMN "player_id" TO "user_id";
        ALTER TABLE "pokemon_player_badges" ADD CONSTRAINT "fk_pokemon__users_01ca56c5" FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE;
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_pokemon_pla_user_id_10df5f" ON "pokemon_player_badges" ("user_id", "badge");
        ALTER TABLE "pokemon_player_battle_progress" ADD CONSTRAINT "fk_pokemon__users_7636ee9f" FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE;
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_pokemon_pla_user_id_d17749" ON "pokemon_player_battle_progress" ("user_id", "battle_id");
        ALTER TABLE "pokemon_player_dungeon_progress" ADD CONSTRAINT "fk_pokemon__users_7692d3a8" FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE;
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_pokemon_pla_user_id_fe4d35" ON "pokemon_player_dungeon_progress" ("user_id", "dungeon_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "uid_pokemon_pla_user_id_fe4d35";
        ALTER TABLE "pokemon_player_dungeon_progress" DROP CONSTRAINT IF EXISTS "fk_pokemon__users_7692d3a8";
        DROP INDEX IF EXISTS "uid_pokemon_pla_user_id_d17749";
        ALTER TABLE "pokemon_player_battle_progress" DROP CONSTRAINT IF EXISTS "fk_pokemon__users_7636ee9f";
        DROP INDEX IF EXISTS "uid_pokemon_pla_user_id_10df5f";
        ALTER TABLE "pokemon_player_badges" DROP CONSTRAINT IF EXISTS "fk_pokemon__users_01ca56c5";
        ALTER TABLE "pokemon_player_badges" RENAME COLUMN "user_id" TO "player_id";
        ALTER TABLE "pokemon_player_battle_progress" RENAME COLUMN "user_id" TO "player_id";
        ALTER TABLE "pokemon_player_dungeon_progress" RENAME COLUMN "user_id" TO "player_id";
        DROP TABLE IF EXISTS "pokemon_quest_data";
        DROP TABLE IF EXISTS "pokemon_quest_line_data";
        DROP TABLE IF EXISTS "pokemon_player_quest_progress";
        ALTER TABLE "pokemon_player_badges" ADD CONSTRAINT "fk_pokemon__users_7a5b93b9" FOREIGN KEY ("player_id") REFERENCES "users" ("id") ON DELETE CASCADE;
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_pokemon_pla_player_0a8c64" ON "pokemon_player_badges" ("player", "badge");
        ALTER TABLE "pokemon_player_battle_progress" ADD CONSTRAINT "fk_pokemon__users_34915abb" FOREIGN KEY ("player_id") REFERENCES "users" ("id") ON DELETE CASCADE;
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_pokemon_pla_player_b0013c" ON "pokemon_player_battle_progress" ("player", "battle_id");
        ALTER TABLE "pokemon_player_dungeon_progress" ADD CONSTRAINT "fk_pokemon__users_9fb968b5" FOREIGN KEY ("player_id") REFERENCES "users" ("id") ON DELETE CASCADE;
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_pokemon_pla_player_d38134" ON "pokemon_player_dungeon_progress" ("player", "dungeon_id");"""


MODELS_STATE = (
    "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"
)
