from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "pokemon_dungeon_data" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "region" INT NOT NULL DEFAULT 0,
    "base_health" INT,
    "token_cost" INT
);
COMMENT ON TABLE "pokemon_dungeon_data" IS 'Storage for dungeon data parsed from Pokeclicker Dungeon.ts.';
        CREATE TABLE IF NOT EXISTS "pokemon_dungeon_loot" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "item_name" VARCHAR(100) NOT NULL,
    "tier" VARCHAR(20) NOT NULL,
    "weight" INT NOT NULL DEFAULT 1,
    "dungeon_id" INT NOT NULL REFERENCES "pokemon_dungeon_data" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "pokemon_dungeon_loot" IS 'Loot drops in a dungeon.';
        CREATE TABLE IF NOT EXISTS "pokemon_dungeon_pokemon" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "pokemon_name" VARCHAR(100) NOT NULL,
    "weight" INT NOT NULL DEFAULT 1,
    "is_boss" BOOL NOT NULL DEFAULT False,
    "health" INT,
    "level" INT,
    "dungeon_id" INT NOT NULL REFERENCES "pokemon_dungeon_data" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "pokemon_dungeon_pokemon" IS 'Pokemon encounters in a dungeon.';
        CREATE TABLE IF NOT EXISTS "pokemon_gym_data" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "leader" VARCHAR(50) NOT NULL,
    "region" INT NOT NULL DEFAULT 0,
    "badge" VARCHAR(50) NOT NULL,
    "badge_id" INT,
    "money_reward" INT NOT NULL DEFAULT 0,
    "defeat_message" TEXT,
    "is_elite" BOOL NOT NULL DEFAULT False
);
COMMENT ON TABLE "pokemon_gym_data" IS 'Storage for gym data parsed from Pokeclicker GymList.ts.';
        CREATE TABLE IF NOT EXISTS "pokemon_gym_pokemon" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "pokemon_name" VARCHAR(100) NOT NULL,
    "max_health" INT NOT NULL,
    "level" INT NOT NULL,
    "order" INT NOT NULL DEFAULT 0,
    "gym_id" INT NOT NULL REFERENCES "pokemon_gym_data" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "pokemon_gym_pokemon" IS 'Pokemon in a gym leader''s team.';
        CREATE TABLE IF NOT EXISTS "pokemon_player_badges" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "badge" VARCHAR(50) NOT NULL,
    "badge_id" INT,
    "earned_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "player_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_pokemon_pla_player__e59e18" UNIQUE ("player_id", "badge")
);
COMMENT ON TABLE "pokemon_player_badges" IS 'Badges earned by a player.';
        CREATE TABLE IF NOT EXISTS "pokemon_player_dungeon_progress" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "clears" INT NOT NULL DEFAULT 0,
    "last_cleared" TIMESTAMPTZ,
    "dungeon_id" INT NOT NULL REFERENCES "pokemon_dungeon_data" ("id") ON DELETE CASCADE,
    "player_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_pokemon_pla_player__115126" UNIQUE ("player_id", "dungeon_id")
);
COMMENT ON TABLE "pokemon_player_dungeon_progress" IS 'Track player''s dungeon clear counts.';
        CREATE TABLE IF NOT EXISTS "pokemon_player_key_item" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "key_item" SMALLINT NOT NULL,
    "obtained_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_pokemon_pla_user_id_be33cb" UNIQUE ("user_id", "key_item")
);
COMMENT ON COLUMN "pokemon_player_key_item"."key_item" IS 'KeyItemType enum value';
COMMENT ON TABLE "pokemon_player_key_item" IS 'Key items owned by a player.';
        CREATE TABLE IF NOT EXISTS "pokemon_route_data" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "region" SMALLINT NOT NULL,
    "number" INT NOT NULL,
    "name" VARCHAR(50) NOT NULL,
    "order_number" DOUBLE PRECISION NOT NULL,
    "sub_region" SMALLINT,
    "custom_health" INT,
    "land_pokemon" JSONB NOT NULL,
    "water_pokemon" JSONB NOT NULL,
    "headbutt_pokemon" JSONB NOT NULL,
    "is_implemented" BOOL NOT NULL DEFAULT True,
    CONSTRAINT "uid_pokemon_rou_region_6fefe2" UNIQUE ("region", "number")
);
COMMENT ON COLUMN "pokemon_route_data"."region" IS 'Region index (0=Kanto, 1=Johto...)';
COMMENT ON COLUMN "pokemon_route_data"."number" IS 'Route number (1, 2, 22, 101...)';
COMMENT ON COLUMN "pokemon_route_data"."name" IS 'Display name (Kanto Route 1)';
COMMENT ON COLUMN "pokemon_route_data"."order_number" IS 'Progression order (1.0, 1.1, 2.0 for branching)';
COMMENT ON COLUMN "pokemon_route_data"."sub_region" IS 'Sub-region (Sevii Islands, etc.)';
COMMENT ON COLUMN "pokemon_route_data"."custom_health" IS 'Override route health formula';
COMMENT ON COLUMN "pokemon_route_data"."land_pokemon" IS 'Land encounters [\"Pidgey\", \"Rattata\"]';
COMMENT ON COLUMN "pokemon_route_data"."water_pokemon" IS 'Water encounters (needs Super_rod)';
COMMENT ON COLUMN "pokemon_route_data"."headbutt_pokemon" IS 'Headbutt tree encounters';
COMMENT ON COLUMN "pokemon_route_data"."is_implemented" IS 'False for routes with DevelopmentRequirement';
COMMENT ON TABLE "pokemon_route_data" IS 'Pokemon route data from Pokeclicker.';
        CREATE TABLE IF NOT EXISTS "pokemon_player_route_progress" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "kills" INT NOT NULL DEFAULT 0,
    "is_unlocked" BOOL NOT NULL DEFAULT False,
    "first_cleared_at" TIMESTAMPTZ,
    "route_id" INT NOT NULL REFERENCES "pokemon_route_data" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_pokemon_pla_user_id_d1218c" UNIQUE ("user_id", "route_id")
);
COMMENT ON COLUMN "pokemon_player_route_progress"."kills" IS 'Pokemon defeated on this route';
COMMENT ON COLUMN "pokemon_player_route_progress"."first_cleared_at" IS 'When requirements first met';
COMMENT ON TABLE "pokemon_player_route_progress" IS 'Player''s progress on a specific route.';
        CREATE TABLE IF NOT EXISTS "pokemon_roaming" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "pokemon_name" VARCHAR(50) NOT NULL,
    "region" SMALLINT NOT NULL,
    "sub_region_group" SMALLINT NOT NULL DEFAULT 0,
    "requirement_data" JSONB,
    "is_event" BOOL NOT NULL DEFAULT False,
    "event_name" VARCHAR(50)
);
COMMENT ON COLUMN "pokemon_roaming"."pokemon_name" IS 'Pokemon name';
COMMENT ON COLUMN "pokemon_roaming"."region" IS 'Region where it roams';
COMMENT ON COLUMN "pokemon_roaming"."sub_region_group" IS 'Sub-region group (0=main, 1=Sevii, etc.)';
COMMENT ON COLUMN "pokemon_roaming"."requirement_data" IS 'Requirement config {\"type\": \"quest\", \"quest\": \"Celio''s Errand\"}';
COMMENT ON TABLE "pokemon_roaming" IS 'Roaming legendary Pokemon that appear randomly on routes.';
        CREATE TABLE IF NOT EXISTS "pokemon_route_requirement" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "requirement_type" SMALLINT NOT NULL,
    "parameters" JSONB,
    "parent_id" INT REFERENCES "pokemon_route_requirement" ("id") ON DELETE CASCADE,
    "route_id" INT REFERENCES "pokemon_route_data" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "pokemon_route_requirement"."requirement_type" IS 'RequirementType enum value';
COMMENT ON COLUMN "pokemon_route_requirement"."parameters" IS 'Requirement-specific parameters';
COMMENT ON TABLE "pokemon_route_requirement" IS 'Unlock requirement for a route.';
        CREATE TABLE IF NOT EXISTS "pokemon_special_route_pokemon" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "pokemon_names" JSONB NOT NULL,
    "root_requirement_id" INT REFERENCES "pokemon_route_requirement" ("id") ON DELETE SET NULL,
    "route_id" INT NOT NULL REFERENCES "pokemon_route_data" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "pokemon_special_route_pokemon"."pokemon_names" IS 'Pokemon names [\"Sunkern\"]';
COMMENT ON TABLE "pokemon_special_route_pokemon" IS 'Pokemon that appear on routes under special conditions.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "pokemon_gym_pokemon";
        DROP TABLE IF EXISTS "pokemon_player_key_item";
        DROP TABLE IF EXISTS "pokemon_route_data";
        DROP TABLE IF EXISTS "pokemon_player_dungeon_progress";
        DROP TABLE IF EXISTS "pokemon_dungeon_pokemon";
        DROP TABLE IF EXISTS "pokemon_dungeon_data";
        DROP TABLE IF EXISTS "pokemon_route_requirement";
        DROP TABLE IF EXISTS "pokemon_player_badges";
        DROP TABLE IF EXISTS "pokemon_player_route_progress";
        DROP TABLE IF EXISTS "pokemon_gym_data";
        DROP TABLE IF EXISTS "pokemon_special_route_pokemon";
        DROP TABLE IF EXISTS "pokemon_roaming";
        DROP TABLE IF EXISTS "pokemon_dungeon_loot";"""


MODELS_STATE = (
    "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"
)
