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
        ALTER TABLE "player_pokemon" ADD "gender" SMALLINT NOT NULL DEFAULT 1;
        ALTER TABLE "player_pokemon" ADD "held_item" VARCHAR(50);
        ALTER TABLE "player_pokemon" ADD "display_gender" SMALLINT NOT NULL DEFAULT 1;
        ALTER TABLE "player_pokemon" ADD "stat_hatched" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "vitamins_protein" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "stat_shiny_encountered" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "pokerus" SMALLINT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "stat_encountered" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "stat_shiny_captured" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "hide_shiny_sprite" BOOL NOT NULL DEFAULT False;
        ALTER TABLE "player_pokemon" ADD "stat_shiny_defeated" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "stat_captured" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "evs" DOUBLE PRECISION NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "stat_shiny_hatched" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "vitamins_carbos" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "stat_defeated" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" ADD "vitamins_calcium" INT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" DROP COLUMN "attack_bonus";
        COMMENT ON COLUMN "player_pokemon"."caught_at" IS 'When first caught';
        ALTER TABLE "pokemon_data" ADD "gender_ratio" SMALLINT NOT NULL DEFAULT 4;
        COMMENT ON COLUMN "player_pokemon"."gender" IS 'Gender: 0=genderless, 1=male, 2=female';
COMMENT ON COLUMN "player_pokemon"."held_item" IS 'Held item name';
COMMENT ON COLUMN "player_pokemon"."display_gender" IS 'Displayed gender (can differ from actual for some Pokemon)';
COMMENT ON COLUMN "player_pokemon"."stat_hatched" IS 'Times hatched from egg';
COMMENT ON COLUMN "player_pokemon"."vitamins_protein" IS 'Protein vitamins used';
COMMENT ON COLUMN "player_pokemon"."stat_shiny_encountered" IS 'Shiny encounters';
COMMENT ON COLUMN "player_pokemon"."pokerus" IS '0=none, 1=infected, 2=cured';
COMMENT ON COLUMN "player_pokemon"."stat_encountered" IS 'Times encountered in wild';
COMMENT ON COLUMN "player_pokemon"."stat_shiny_captured" IS 'Shiny captures';
COMMENT ON COLUMN "player_pokemon"."hide_shiny_sprite" IS 'Show normal sprite instead';
COMMENT ON COLUMN "player_pokemon"."stat_shiny_defeated" IS 'Shiny defeats';
COMMENT ON COLUMN "player_pokemon"."stat_captured" IS 'Times captured';
COMMENT ON COLUMN "player_pokemon"."evs" IS 'Effort Values (increases attack)';
COMMENT ON COLUMN "player_pokemon"."stat_shiny_hatched" IS 'Shiny hatches';
COMMENT ON COLUMN "player_pokemon"."vitamins_carbos" IS 'Carbos vitamins used';
COMMENT ON COLUMN "player_pokemon"."stat_defeated" IS 'Times defeated in battle';
COMMENT ON COLUMN "player_pokemon"."vitamins_calcium" IS 'Calcium vitamins used';
COMMENT ON COLUMN "pokemon_data"."gender_ratio" IS 'Gender ratio: -1=genderless, 0-8 female proportion (4=50%)';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "pokemon_data" DROP COLUMN "gender_ratio";
        ALTER TABLE "player_pokemon" ADD "attack_bonus" SMALLINT NOT NULL DEFAULT 0;
        ALTER TABLE "player_pokemon" DROP COLUMN "gender";
        ALTER TABLE "player_pokemon" DROP COLUMN "held_item";
        ALTER TABLE "player_pokemon" DROP COLUMN "display_gender";
        ALTER TABLE "player_pokemon" DROP COLUMN "stat_hatched";
        ALTER TABLE "player_pokemon" DROP COLUMN "vitamins_protein";
        ALTER TABLE "player_pokemon" DROP COLUMN "stat_shiny_encountered";
        ALTER TABLE "player_pokemon" DROP COLUMN "pokerus";
        ALTER TABLE "player_pokemon" DROP COLUMN "stat_encountered";
        ALTER TABLE "player_pokemon" DROP COLUMN "stat_shiny_captured";
        ALTER TABLE "player_pokemon" DROP COLUMN "hide_shiny_sprite";
        ALTER TABLE "player_pokemon" DROP COLUMN "stat_shiny_defeated";
        ALTER TABLE "player_pokemon" DROP COLUMN "stat_captured";
        ALTER TABLE "player_pokemon" DROP COLUMN "evs";
        ALTER TABLE "player_pokemon" DROP COLUMN "stat_shiny_hatched";
        ALTER TABLE "player_pokemon" DROP COLUMN "vitamins_carbos";
        ALTER TABLE "player_pokemon" DROP COLUMN "stat_defeated";
        ALTER TABLE "player_pokemon" DROP COLUMN "vitamins_calcium";
        COMMENT ON COLUMN "player_pokemon"."caught_at" IS 'When caught';
        COMMENT ON COLUMN "player_pokemon"."attack_bonus" IS 'Bonus attack from vitamins etc.';
        DROP TABLE IF EXISTS "pokemon_player_quest_progress";
        DROP TABLE IF EXISTS "pokemon_quest_line_data";
        DROP TABLE IF EXISTS "pokemon_quest_data";"""


MODELS_STATE = (
    "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"
    "rSIU9uuqTu5VWr//3/8H2rKocA=="
)
