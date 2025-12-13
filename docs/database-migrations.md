# Database Migrations

> Aerich + Tortoise ORM migration system for schema version control.

---

## Overview

This project uses **Aerich** for database migrations with **Tortoise ORM**. Migrations track schema changes as versioned Python files, enabling rollback, team synchronization, and audit trails.

---

## Architecture

```
funbot/db/
├── models/              # Tortoise ORM model definitions
│   ├── __init__.py     # Model exports
│   └── user.py         # User model
├── __init__.py         # Module entry (lazy imports)
├── aerich_config.py    # CLI-only config (avoids full app validation)
├── config.py           # Runtime Tortoise config
└── database.py         # Connection lifecycle manager

migrations/models/
└── 0_YYYYMMDDHHMMSS_init.py   # Migration files
```

---

## Migration File Structure

Each migration contains:

```python
from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True

async def upgrade(db: BaseDBAsyncClient) -> str:
    """Forward migration SQL."""
    return """CREATE TABLE ..."""

async def downgrade(db: BaseDBAsyncClient) -> str:
    """Rollback migration SQL."""
    return """DROP TABLE ..."""

MODELS_STATE = (...)  # Serialized model state for diff detection
```

---

## Configuration

### pyproject.toml

```toml
[tool.aerich]
tortoise_orm = "funbot.db.aerich_config.TORTOISE_CONFIG"
location = "./migrations"
src_folder = "./."
```

### aerich_config.py

Lightweight config that only loads `DB_URL`, avoiding Discord token validation issues with pydantic-settings.

---

## Commands

| Command | Description |
|---------|-------------|
| `uv run aerich init-db` | Initialize database and create first migration |
| `uv run aerich migrate --name <name>` | Generate migration from model changes |
| `uv run aerich upgrade` | Apply pending migrations |
| `uv run aerich downgrade` | Rollback last migration |
| `uv run aerich history` | Show applied migrations |

---

## Workflow

### Adding a new field

1. Modify model in `funbot/db/models/`
2. Run `uv run aerich migrate --name add_field_name`
3. Review generated migration file
4. Run `uv run aerich upgrade`

### Rolling back

1. Run `uv run aerich downgrade`
2. Fix the issue
3. Run `uv run aerich upgrade` again

---

## References

- [Tortoise ORM Documentation](https://tortoise.github.io/)
- [Aerich GitHub](https://github.com/tortoise/aerich)
