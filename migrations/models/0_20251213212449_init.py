from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON COLUMN "users"."id" IS 'Discord user ID';
COMMENT ON TABLE "users" IS 'Represents a Discord user in the database.';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztVl1v2jAU/SsWT1TqEA1QGG/px1amFaaWrlM/FJnYBIvESW1nLar47/N1EkICpK00qZ"
    "00nuDcc+zrc5xcnmtBSKgvG1eSilofPdc4Dqj+UsD3UQ1HUY4CoPDEN8RYMwyCJ1IJ7CoN"
    "TrEvqYYIla5gkWIhB+oFjQSVlCuJMDph0g0FQaBHjCM1o4hgvSyWtAHrkdDVCzLuvU16x+"
    "+4rbRwEisq+3cc6Q8j/aJqcILqkWABFgs0p4u9RsJzBcWKEgerPrqe0WRpI3jEEk2ZkApJ"
    "SnlKjyOygy6o2QtUPtailGkOFnP2EFNHhR7VfLD99l7DjBP6RGX2M5o7U0Z9UkiFEVjA4I"
    "5aRAY7Yt6Aqy+GC7ZNHDf044Dn/GihZiFfCRhXgHqUUwFNaUyJGPLise+nuWYRJs3mlKTL"
    "NQ2hUxz7kDqoN0Mv2V5ONhW5IYfbo1uT5sAebPnps2W1Wl2r2TrsddrdbqfX7Gmu6W+z1F"
    "0mp8/dSZYyHg2+DoZj2DvUVzS5uAAsjUZfnURlzM/dzm/DpusnuqJYQLf7XlSW/CeptJF9"
    "KaeReV8VRwbkeeQPXWUgGfhyBvoMZMT9RZp1hb3jwfnp5dg+/wEnCaR88I1F9vgUKpZBFy"
    "W0frhXzGO1CLoejM8Q/EQ3o+GpcTCUyhNmx5w3vqlBTzhWocPDRweTtWuZoZkxmpkHmz+3"
    "bw22qPwf7LsGa5qHd+V0vvb8AjDB7vwRC+JsVEIr3MXdLAVWUEYwx55JBbyFLtNBaVPB3N"
    "m2EZpWKocozjkvTdHdMf/lufKBh8rrr3oyR6yDdrfdax22V+NjhVRNjZcnxG/93wda2jDv"
    "eIbFdvfWJCULdeMf9IUR4CfHp9xTcMGtTqfCs5/2xfGZfVHXrNJrYJiWrKS2LLyR4dF4g4"
    "kp/d808KDZfIWBmrXTQFMrGqh3VJRvmWffLkfDHX9ScknJyCuuD3hLmKv2kc+kuv+Ytla4"
    "CKcuzKzMvPq5/avs6/H30VF5GMECR9rjdx0vyz8i/Ftp"
)
