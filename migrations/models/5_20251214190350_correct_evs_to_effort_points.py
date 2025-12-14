from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
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
    "player_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "quest_line_id" INT NOT NULL REFERENCES "pokemon_quest_line_data" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_pokemon_pla_player__9c29b9" UNIQUE ("player_id", "quest_line_id")
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
        ALTER TABLE "player_pokemon" ADD "hide_shiny_sprite" BOOL NOT NULL DEFAULT False;
        ALTER TABLE "player_pokemon" ADD "stat_hatched" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "vitamins_calcium" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "stat_shiny_encountered" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "stat_shiny_hatched" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "stat_shiny_defeated" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "pokerus" SMALLINT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "stat_shiny_captured" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "vitamins_carbos" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "stat_encountered" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "effort_points" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "held_item" VARCHAR(50);
        ALTER TABLE "player_pokemon" ADD "gender" SMALLINT NOT NULL DEFAULT 1;
        ALTER TABLE "player_pokemon" ADD "stat_captured" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "display_gender" SMALLINT NOT NULL DEFAULT 1;
        ALTER TABLE "player_pokemon" ADD "stat_defeated" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "vitamins_protein" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" DROP COLUMN "attack_bonus";
        COMMENT ON COLUMN "player_pokemon"."caught_at" IS 'When first caught';
        ALTER TABLE "pokemon_data" ADD "gender_ratio" SMALLINT NOT NULL DEFAULT 4;
        COMMENT ON COLUMN "player_pokemon"."hide_shiny_sprite" IS 'Show normal sprite instead';
COMMENT ON COLUMN "player_pokemon"."stat_hatched" IS 'Times hatched';
COMMENT ON COLUMN "player_pokemon"."vitamins_calcium" IS 'Calcium vitamins used';
COMMENT ON COLUMN "player_pokemon"."stat_shiny_encountered" IS 'Shiny encounters';
COMMENT ON COLUMN "player_pokemon"."stat_shiny_hatched" IS 'Shiny hatches';
COMMENT ON COLUMN "player_pokemon"."stat_shiny_defeated" IS 'Shiny defeats';
COMMENT ON COLUMN "player_pokemon"."pokerus" IS 'Pokerus state (0-3)';
COMMENT ON COLUMN "player_pokemon"."stat_shiny_captured" IS 'Shiny captures';
COMMENT ON COLUMN "player_pokemon"."vitamins_carbos" IS 'Carbos vitamins used';
COMMENT ON COLUMN "player_pokemon"."stat_encountered" IS 'Times encountered';
COMMENT ON COLUMN "player_pokemon"."effort_points" IS 'Raw effort points (EVs = EP/1000)';
COMMENT ON COLUMN "player_pokemon"."held_item" IS 'Held item name';
COMMENT ON COLUMN "player_pokemon"."gender" IS '0=genderless, 1=male, 2=female';
COMMENT ON COLUMN "player_pokemon"."stat_captured" IS 'Times captured';
COMMENT ON COLUMN "player_pokemon"."display_gender" IS 'Displayed gender preference';
COMMENT ON COLUMN "player_pokemon"."stat_defeated" IS 'Times defeated';
COMMENT ON COLUMN "player_pokemon"."vitamins_protein" IS 'Protein vitamins used';
COMMENT ON COLUMN "pokemon_data"."gender_ratio" IS 'Gender ratio: -1=genderless, 0-8 female proportion (4=50%)';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "pokemon_data" DROP COLUMN "gender_ratio";
        ALTER TABLE "player_pokemon" ADD "attack_bonus" SMALLINT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" DROP COLUMN "hide_shiny_sprite";
        ALTER TABLE "player_pokemon" DROP COLUMN "stat_hatched";
        ALTER TABLE "player_pokemon" DROP COLUMN "vitamins_calcium";
        ALTER TABLE "player_pokemon" DROP COLUMN "stat_shiny_encountered";
        ALTER TABLE "player_pokemon" DROP COLUMN "stat_shiny_hatched";
        ALTER TABLE "player_pokemon" DROP COLUMN "stat_shiny_defeated";
        ALTER TABLE "player_pokemon" DROP COLUMN "pokerus";
        ALTER TABLE "player_pokemon" DROP COLUMN "stat_shiny_captured";
        ALTER TABLE "player_pokemon" DROP COLUMN "vitamins_carbos";
        ALTER TABLE "player_pokemon" DROP COLUMN "stat_encountered";
        ALTER TABLE "player_pokemon" DROP COLUMN "effort_points";
        ALTER TABLE "player_pokemon" DROP COLUMN "held_item";
        ALTER TABLE "player_pokemon" DROP COLUMN "gender";
        ALTER TABLE "player_pokemon" DROP COLUMN "stat_captured";
        ALTER TABLE "player_pokemon" DROP COLUMN "display_gender";
        ALTER TABLE "player_pokemon" DROP COLUMN "stat_defeated";
        ALTER TABLE "player_pokemon" DROP COLUMN "vitamins_protein";
        COMMENT ON COLUMN "player_pokemon"."caught_at" IS 'When caught';
        COMMENT ON COLUMN "player_pokemon"."attack_bonus" IS 'Bonus attack from vitamins etc.';
        DROP TABLE IF EXISTS "pokemon_quest_line_data";
        DROP TABLE IF EXISTS "pokemon_player_quest_progress";
        DROP TABLE IF EXISTS "pokemon_quest_data";"""


MODELS_STATE = (
    "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"
)
