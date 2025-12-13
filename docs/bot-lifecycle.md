# Bot Lifecycle

Documentation of the bot's startup, runtime, and shutdown phases.

---

## Startup Flow

```
main.py
    │
    ├── Load environment variables (.env)
    │
    ├── Initialize Tortoise ORM (Database context manager)
    │
    ├── Create Redis connection (optional)
    │
    ├── Instantiate FunBot
    │
    └── bot.start(token)
            │
            ├── setup_hook() [ONCE]
            │   ├── Set error handler
            │   ├── Load all cogs from funbot/cogs/
            │   └── Sync commands (based on ENV)
            │
            └── on_ready() [ON EACH CONNECT]
                └── Log connection status
```

---

## Key Methods

### `setup_hook()`

- Called **once** when the bot is starting
- Use for: loading cogs, syncing commands, one-time initialization
- Does NOT run again on reconnects

### `on_ready()`

- Called **every time** the bot connects to Discord
- Includes initial connection AND reconnections after disconnects
- Use for: logging only, no heavy operations

---

## Database Connection

This project uses **Tortoise ORM** for database operations. The `Database` class is a context manager that initializes and closes Tortoise:

```python
from funbot.db import Database

async with Database():
    # Tortoise ORM is now connected
    # Use models like: await User.get(id=123)
    pass
# Connections automatically closed
```

---

## Shutdown Flow

```
SIGINT/SIGTERM received
    │
    ├── bot.close()
    │   └── Disconnect from Discord
    │
    └── Database.__aexit__()
        └── Close Tortoise connections
```

---

## Cog Loading

Cogs are loaded dynamically from `funbot/cogs/`:

```python
async def _load_cogs(self) -> None:
    cogs_path = anyio.Path("funbot/cogs")
    
    async for filepath in cogs_path.glob("*.py"):
        if not filepath.stem.startswith("_"):
            await self.load_extension(f"funbot.cogs.{filepath.stem}")
```

To add a new cog, simply create a new `.py` file in `funbot/cogs/`.
