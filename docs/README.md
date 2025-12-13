# FunBot Architecture Documentation

Technical documentation for the FunBot Discord bot.

---

## 📁 Documentation Index

| Document | Description |
|----------|-------------|
| [AI_RULES.md](./AI_RULES.md) | **Rules for AI agents** - Read this first |
| [database-migrations.md](./database-migrations.md) | Aerich migration system |
| [project-structure.md](./project-structure.md) | Directory structure |
| [bot-lifecycle.md](./bot-lifecycle.md) | Startup and shutdown flow |
| [command-sync.md](./command-sync.md) | Discord command synchronization |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Bot Framework | discord.py |
| ORM | Tortoise ORM |
| Migrations | Aerich |
| Database | PostgreSQL |
| Cache | Redis (optional) |
| Config | pydantic-settings |
| Package Manager | uv |

---

## Quick Reference

### Common Commands

```bash
# Run the bot
uv run python main.py

# Run tests
uv run pytest

# Type check
uv run pyright

# Lint
uv run ruff check

# Generate migration
uv run aerich migrate --name <name>

# Apply migrations
uv run aerich upgrade
```

### Environment Variables

See `.env.example` for all available options.

Required:
- `DISCORD_TOKEN` - Bot token from Discord Developer Portal
- `DB_URL` - PostgreSQL connection string

Optional:
- `REDIS_URL` - Redis connection string
- `DEV_GUILD_ID` - Guild ID for dev environment command sync
- `ENV` - `dev` or `prod`
