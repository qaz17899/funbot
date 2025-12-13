from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "player_pokeball_settings" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "new_shiny" SMALLINT NOT NULL DEFAULT 3,
    "new_pokemon" SMALLINT NOT NULL DEFAULT 1,
    "caught_shiny" SMALLINT NOT NULL DEFAULT 1,
    "caught_pokemon" SMALLINT NOT NULL DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" BIGINT NOT NULL UNIQUE REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "player_pokeball_settings"."new_shiny" IS 'Ball for new shiny Pokemon';
COMMENT ON COLUMN "player_pokeball_settings"."new_pokemon" IS 'Ball for new (uncaught) Pokemon';
COMMENT ON COLUMN "player_pokeball_settings"."caught_shiny" IS 'Ball for already caught shiny';
COMMENT ON COLUMN "player_pokeball_settings"."caught_pokemon" IS 'Ball for already caught Pokemon (NONE = don''t catch)';
COMMENT ON TABLE "player_pokeball_settings" IS 'Pokeball auto-catch settings for a player.';
        CREATE TABLE IF NOT EXISTS "pokemon_data" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(50) NOT NULL UNIQUE,
    "name_ja" VARCHAR(50),
    "type1" SMALLINT NOT NULL,
    "type2" SMALLINT,
    "base_hp" SMALLINT NOT NULL,
    "base_attack" SMALLINT NOT NULL,
    "base_defense" SMALLINT NOT NULL,
    "base_sp_attack" SMALLINT NOT NULL,
    "base_sp_defense" SMALLINT NOT NULL,
    "base_speed" SMALLINT NOT NULL,
    "catch_rate" SMALLINT NOT NULL,
    "base_exp" SMALLINT NOT NULL,
    "egg_cycles" SMALLINT NOT NULL DEFAULT 20,
    "sprite_url" VARCHAR(200),
    "sprite_shiny_url" VARCHAR(200),
    "generation" SMALLINT NOT NULL,
    "region" SMALLINT NOT NULL,
    "evolves_from" INT,
    "evolution_level" SMALLINT
);
COMMENT ON COLUMN "pokemon_data"."id" IS 'National Pokedex number';
COMMENT ON COLUMN "pokemon_data"."name" IS 'Pokemon name';
COMMENT ON COLUMN "pokemon_data"."name_ja" IS 'Japanese name (optional)';
COMMENT ON COLUMN "pokemon_data"."type1" IS 'Primary type (PokemonType enum)';
COMMENT ON COLUMN "pokemon_data"."type2" IS 'Secondary type (optional)';
COMMENT ON COLUMN "pokemon_data"."base_hp" IS 'Base HP stat';
COMMENT ON COLUMN "pokemon_data"."base_attack" IS 'Base Attack stat';
COMMENT ON COLUMN "pokemon_data"."base_defense" IS 'Base Defense stat';
COMMENT ON COLUMN "pokemon_data"."base_sp_attack" IS 'Base Sp. Attack stat';
COMMENT ON COLUMN "pokemon_data"."base_sp_defense" IS 'Base Sp. Defense stat';
COMMENT ON COLUMN "pokemon_data"."base_speed" IS 'Base Speed stat';
COMMENT ON COLUMN "pokemon_data"."catch_rate" IS 'Base catch rate (0-255)';
COMMENT ON COLUMN "pokemon_data"."base_exp" IS 'Base experience yield';
COMMENT ON COLUMN "pokemon_data"."egg_cycles" IS 'Egg hatch cycles';
COMMENT ON COLUMN "pokemon_data"."sprite_url" IS 'Sprite image URL';
COMMENT ON COLUMN "pokemon_data"."sprite_shiny_url" IS 'Shiny sprite URL';
COMMENT ON COLUMN "pokemon_data"."generation" IS 'Generation (1-9)';
COMMENT ON COLUMN "pokemon_data"."region" IS 'Native region (Region enum)';
COMMENT ON COLUMN "pokemon_data"."evolves_from" IS 'Pokemon ID this evolves from';
COMMENT ON COLUMN "pokemon_data"."evolution_level" IS 'Level required to evolve (if level-based)';
COMMENT ON TABLE "pokemon_data" IS 'Static Pokemon data imported from PokeAPI.';
        CREATE TABLE IF NOT EXISTS "player_pokemon" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "nickname" VARCHAR(20),
    "level" SMALLINT NOT NULL DEFAULT 1,
    "exp" INT NOT NULL DEFAULT 0,
    "attack_bonus" SMALLINT NOT NULL DEFAULT 0,
    "shiny" BOOL NOT NULL DEFAULT False,
    "caught_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "pokemon_data_id" INT NOT NULL REFERENCES "pokemon_data" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_player_poke_user_id_d23eab" UNIQUE ("user_id", "pokemon_data_id")
);
COMMENT ON COLUMN "player_pokemon"."level" IS 'Current level (1-100)';
COMMENT ON COLUMN "player_pokemon"."exp" IS 'Current EXP towards next level';
COMMENT ON COLUMN "player_pokemon"."attack_bonus" IS 'Bonus attack from vitamins etc.';
COMMENT ON COLUMN "player_pokemon"."shiny" IS 'Is shiny variant';
COMMENT ON COLUMN "player_pokemon"."caught_at" IS 'When caught';
COMMENT ON TABLE "player_pokemon" IS 'A Pokemon owned by a player.';
        CREATE TABLE IF NOT EXISTS "player_pokemon_wallet" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "pokedollar" BIGINT NOT NULL DEFAULT 0,
    "dungeon_token" BIGINT NOT NULL DEFAULT 0,
    "battle_point" BIGINT NOT NULL DEFAULT 0,
    "quest_point" BIGINT NOT NULL DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" BIGINT NOT NULL UNIQUE REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "player_pokemon_wallet"."pokedollar" IS 'Main Pokemon currency';
COMMENT ON COLUMN "player_pokemon_wallet"."dungeon_token" IS 'Dungeon exploration currency';
COMMENT ON COLUMN "player_pokemon_wallet"."battle_point" IS 'Battle frontier currency';
COMMENT ON COLUMN "player_pokemon_wallet"."quest_point" IS 'Quest reward currency';
COMMENT ON TABLE "player_pokemon_wallet" IS 'Pokemon currency wallet for a player.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "player_pokemon";
        DROP TABLE IF EXISTS "player_pokemon_wallet";
        DROP TABLE IF EXISTS "player_pokeball_settings";
        DROP TABLE IF EXISTS "pokemon_data";"""


MODELS_STATE = (
    "eJztXNty2zgS/RWUXlapjV2SHMWZVM2DfMnEM76t5UymJkmxILItcU2BDAnZVk353xcNgq"
    "J4FSlbJO1VHmIJwAEbBy2gu9HgP62pbYDl7V5adA7upX0LI2pZQ+DcZGOv9ZH802J0CuLD"
    "ipZvSYs6TtgOCzgdWRLqSIzmKJDmLaNGHnepzkW7G2p5IIoM8HTXdLhpM0QHzyJ0xu0dnX"
    "J9QoIeyI3tEkr8B+xif4atiw5FXTnod/adHQEHd2oy8Mj9xBRNF3Buk5kHpC0Q5xfnx/jd"
    "uzWdN7IPoKKp6BvGtjuXMsyY+XMGGrfHwCfgCkm+/RDFJjPgAbzgq3Or3ZhgGRGWTQM7kO"
    "Uanzuy7ITxT7IhDm+k6bY1m7KwsTPnE5stWpuMY+kYGLhCKOyeuzPklc0sS01JQLUvadjE"
    "F3EJY8ANnVk4O4hOTE5QuES6KtJthhMrpPHVaIxP2el13+2/+7D3/t0H0URKsijZf/SHF4"
    "7dB0oGzq9bj7Kecuq3kDSGvDG417yJyeZJ+oZTMYWZHEaAq6kMiMvjMigIyQw1O2BzL6nn"
    "B6hpqFBCJCJFkgo4FbVlKN7r7b9fsItf8ogdng1OTwN2o2w64bPL8rkErY7R7gpG2zOm09"
    "l4wt/URqv//PX0NI5tBrHUcoEac+JLRxbS1UHrmgqbRFdHbac4tUpnSVtuQL8Sw2b/4kRu"
    "aW+qZ1yIJpjQKE+yfSRquDmFDLYjyBjThoLuBh82xfsT9zKcmAtmzdU2mcPf9cnZ8fB6cH"
    "aJI5l63k9LUjS4Psaaniydx0rb7+WE2sIq8s2nRSfk68n1Z4Jfyd9CCySDtsfHrnxi2O76"
    "7xbKhEaPxux7jRpLO3pQGhATmdiZY6w5sVHkdmJrnVgl/NK8esL+TrMtD8xx5sq4BHqeJb"
    "EiI/OXXm9vb7/X2Xv/of9uf7//obNY75JVeavfwclvuPZF5sxfDNF+v7ldskSxYET123vq"
    "Glqixu7ZqVYrMpyckwsG17b4T87KiRghZTqkzILyyL6oTpo2G4+BPgWl4SNcer/wfZbVTA"
    "xODEm4YVh+OBgeDo6OW48RbqNUYtW0N42XUEbHckgoGcqRcF6nciw53q2yBQo5tUHbla7s"
    "YLGN2/cMDDKa5ziveY3RXT30t1LhqwLzDQEBFE3Q2FXILG/020LzlPgaOlatH1svdcNeqq"
    "nfys8J9g4n1M1wqJYwMRKF6AV++IqjKvfRKX3QLGBjPkHuOjmc/Tm4Ovw8uGr3OrG98VzV"
    "9GRV1Py04A6ssnb+AlSr53Q4c11gnEhpSLu70+10qrff4cEp8QNWrWt1iwLejv+6JNzGnc"
    "ATC92DIrIUgU/8dYcsUs7FrqSNbDbzympjHFuvz4lSEF8kcuPaU3Jncjo1mUeA64mdaePq"
    "mREgObBtCyhLJzQrMDISoE1RmbHLn3gqfHdHXZP6M1nYXEq1Qy8uTiN+xsFJzCo9/3J2cH"
    "zV7sqlRDQy+ZKxmhIrWcNxXwY2yr1rffUNIJSvoKq+Fj8v6cBvIzOvdGK3kZlXMbGJyMyy"
    "A5Yaock0IVKQ1VkRTfCzmhbeqoy3OgJcq4JWn2wXzDH7A+YbDlttnuVnC1xl/c6fgT0V4D"
    "lSvb1cElNWsQJRwBUR1ueOGH4VrhzwVmbAUNW/LR4v1O5DSKEMGIwD6tIJ1ufEBxdIflmJ"
    "wkDiBYOgzgEXM13ct0SZg0R0cGO6XngAKaYSUFwzO7y4DSNuNoyIOmTYYnwp63DejhfF1R"
    "pyOBNkkbiGlgo0VLAJLq/fxoyNAekSMqfkGOTRnoDWyvyRLw2BB8cSA8biFzEBI8q5BWL9"
    "VHQV5z+OrDm/A4XBKBvjplhtXwL1YsAeX4f5GLBW4v+DshAX0CZ4EaxvQzmvwuPfhnJe6c"
    "Ruk2y2STa1z0YTk2yWQhNpHnM0cpHjMMciJqv95CEX5qy+cCsQSMypY7voyMpzTawaXJ4k"
    "neXiUJl6I4w3isejI+oBEbrDPUKZIXzjG1sl71qk2+n1/70qE+eVusqtc+lYUEuOX2BFs+"
    "nI/wnV7z+XTsF5SvrNs1Ea6GYgTdk8nH6RPJx+dh5OP5GHg3+1/6aEM/OpVJB6k5lav1OH"
    "MhA/XxSJtG3HV9iiyTgbpha76CaJzU8qWYBqPs9oXbrmlLpzggKQtlLca/wCYh2oPt8JG/"
    "XWYbO3NpvPp6hDEMQYIZ1lNfX5aMTdTpukpI7lE7kEq1sxD3C//nwpt+x66POzrNaiMIQ2"
    "gsaBny9WH5VCSmBeyk5egMslbCPIPPLlqZFNz3mKbkbQjWB06OzWr6KClqdoaRTeGFqboK"
    "wAKR5RIUoVsiFsCmnq4VHeGNFwrGV5jCIbwaP/agd8IGl3dnr9fk3GUWpifQGtrDzFPodL"
    "IQu4JjAdyHwhcaW3E8ZjTZ8LJ6l0Vn0UWR2bvZTzpuPxmEykWoYSVZtF77gmB23mplyVyX"
    "bQo6iaffShFIYIZ3IM5MvV6Tq+ea9T7P5R3gWkhHuuWJJp/msyHMHWzbO8ruAL1iieFQNm"
    "+dc6RJF1L6y/LaTBO1+/VL87uTBeg8QQVTeBGE++A+ILRNpX/t96oklwZ1t34Gl4LFAiKh"
    "+H1RxWCsLJJ0eET0yPKPFIIF71WdwowQzF09a64JkCr5niU3nJ04WfM9MVZj63Fcmkbd74"
    "Fxd30PozqlHhEsep4ZzIq+faKO02nkJ++uMKrKyFNutaffPSErIOUh83mV0sT5VTzkiD0+"
    "bsw1E8zy34/rwrcFzwgOEZJTkyPd12DZnkS0wmfvogDztRD5OnosWheCo64AI4mnHwPn5n"
    "RPwzjY9RlFhr2o46G7iF+Ztdv12Yr/SRyMt82LUE3FNPpR97AEw1D7Ng4s1dkM9ClEUFSL"
    "XcxOFrXk5HA85fY7SXWmAqyXPLPp3d5r29ivSobd7bK53Yxa5Y2pjIfEPf1pZIsSWivCVe"
    "nJvOYJDWVobH+It8G/c+mUw+0y7YhRernoeh8G7Xy+GlpBk6ANfUJ2mGqKrJNUVp2GaVLZ"
    "o9sv+f1LjG3CK7Ex5EakwoO3S5BHmeXLgKtt1okLLfLxKkVOdHqUFKrIu9B8hJOfTJJlE1"
    "f5kEdgtFebs5Ud5uMsornsgh7W7R78OL8wxTP4TEiPzCxAC/GabO3xLL9PiPZtKawyKOOm"
    "L5BeS1zwZ/xXk9PL04iJt02MHBUxPonxrlePwfxuP3CA=="
)
