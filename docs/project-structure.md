# Project Structure

Directory layout and module organization.

---

## Root Directory

```
funbot/
├── funbot/          # Main application code
├── migrations/      # Aerich database migrations
├── tests/           # Test suite
├── docs/            # Documentation
├── reference/       # Reference projects
├── .github/         # GitHub Actions workflows
├── main.py          # Entry point
├── pyproject.toml   # Project configuration
└── .env             # Environment variables (gitignored)
```

---

## Application Code (`funbot/`)

```
funbot/
├── bot/
│   ├── bot.py              # FunBot class
│   ├── command_tree.py     # Custom CommandTree with logging
│   └── error_handler.py    # Global error handling
│
├── cogs/
│   └── general.py          # General commands
│
├── db/
│   ├── models/
│   │   ├── __init__.py     # Model exports
│   │   └── user.py         # User model
│   ├── __init__.py         # Lazy imports for Aerich compatibility
│   ├── aerich_config.py    # Aerich CLI configuration
│   ├── config.py           # Tortoise ORM runtime config
│   └── database.py         # Database context manager
│
├── ui/
│   └── ...                 # Discord UI components
│
├── utils/
│   └── ...                 # Utility functions
│
├── __init__.py
├── config.py               # App configuration (pydantic-settings)
├── constants.py            # Constant values
├── embeds.py               # Embed templates
├── enums.py                # Enumerations
├── exceptions.py           # Custom exceptions
└── types.py                # Type aliases
```

---

## Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `bot/` | Discord bot core, command tree, error handling |
| `cogs/` | Feature implementations (one cog per feature group) |
| `db/` | Database models, configuration, connection management |
| `ui/` | Discord UI components (buttons, modals, selects) |
| `utils/` | Shared utility functions |

---

## Key Files

### `config.py`

Application configuration using pydantic-settings:

```python
class Config(BaseSettings):
    discord_token: str
    db_url: str
    redis_url: str | None = None
    env: Literal["dev", "prod"] = "dev"
    dev_guild_id: int | None = None
```

### `db/aerich_config.py`

Lightweight config for Aerich CLI that only loads `DB_URL`, avoiding full app validation.

### `db/__init__.py`

Uses lazy imports to prevent Aerich from triggering config validation:

```python
def __getattr__(name: str):
    if name == "Database":
        from funbot.db.database import Database
        return Database
    raise AttributeError(...)
```

---

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Modules | snake_case | `user_service.py` |
| Classes | PascalCase | `UserService` |
| Functions | snake_case | `get_user_by_id` |
| Constants | UPPER_SNAKE | `MAX_RETRIES` |
| Type Aliases | PascalCase | `UserId = int` |
