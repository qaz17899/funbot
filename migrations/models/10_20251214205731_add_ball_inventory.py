from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "player_ball_inventory" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "pokeball" INT NOT NULL DEFAULT 25,
    "greatball" INT NOT NULL DEFAULT 0,
    "ultraball" INT NOT NULL DEFAULT 0,
    "masterball" INT NOT NULL DEFAULT 0,
    "pokeball_used" INT NOT NULL DEFAULT 0,
    "greatball_used" INT NOT NULL DEFAULT 0,
    "ultraball_used" INT NOT NULL DEFAULT 0,
    "masterball_used" INT NOT NULL DEFAULT 0,
    "pokeball_purchased" INT NOT NULL DEFAULT 0,
    "greatball_purchased" INT NOT NULL DEFAULT 0,
    "ultraball_purchased" INT NOT NULL DEFAULT 0,
    "masterball_purchased" INT NOT NULL DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" BIGINT NOT NULL UNIQUE REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "player_ball_inventory"."pokeball" IS 'Poké Ball quantity';
COMMENT ON COLUMN "player_ball_inventory"."greatball" IS 'Great Ball quantity';
COMMENT ON COLUMN "player_ball_inventory"."ultraball" IS 'Ultra Ball quantity';
COMMENT ON COLUMN "player_ball_inventory"."masterball" IS 'Master Ball quantity';
COMMENT ON COLUMN "player_ball_inventory"."pokeball_used" IS 'Poké Balls used';
COMMENT ON COLUMN "player_ball_inventory"."greatball_used" IS 'Great Balls used';
COMMENT ON COLUMN "player_ball_inventory"."ultraball_used" IS 'Ultra Balls used';
COMMENT ON COLUMN "player_ball_inventory"."masterball_used" IS 'Master Balls used';
COMMENT ON COLUMN "player_ball_inventory"."pokeball_purchased" IS 'Poké Balls purchased';
COMMENT ON COLUMN "player_ball_inventory"."greatball_purchased" IS 'Great Balls purchased';
COMMENT ON COLUMN "player_ball_inventory"."ultraball_purchased" IS 'Ultra Balls purchased';
COMMENT ON COLUMN "player_ball_inventory"."masterball_purchased" IS 'Master Balls purchased';
COMMENT ON TABLE "player_ball_inventory" IS 'Pokeball inventory for a player.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "player_ball_inventory";"""


MODELS_STATE = (
    "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"
    "sIpPhtXXnfRru//P3/H2Plfg=="
)
