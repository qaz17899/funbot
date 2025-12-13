# Command Synchronization

How Discord slash commands are synced between the bot and Discord's servers.

---

## Overview

Discord slash commands require **synchronization** - the bot must tell Discord what commands it offers. This is done via `tree.sync()`.

---

## Sync Types

| Type | Scope | Propagation Time | Use Case |
|------|-------|------------------|----------|
| Global | All guilds | Up to 1 hour | Production |
| Guild | Specific guild | Instant | Development |

---

## Implementation

### Location: `setup_hook()`

Command sync is in `setup_hook()`, NOT `on_ready()`:

```python
async def setup_hook(self) -> None:
    # ... load cogs ...
    
    guild_to_sync = None
    if self.config.is_dev:
        if self.config.dev_guild_id:
            guild_to_sync = discord.Object(id=self.config.dev_guild_id)
        else:
            logger.warning("DEV_GUILD_ID not set, syncing globally")
    
    await self.tree.sync(guild=guild_to_sync)
```

### Why not `on_ready()`?

`on_ready()` fires on **every connection**, including reconnects after network issues. Syncing commands there would:
- Waste API calls
- Risk rate limiting
- Slow down reconnection

---

## Custom CommandTree

We use a custom `CommandTree` that logs sync results:

```python
class CommandTree(app_commands.CommandTree):
    async def sync(self, *, guild=None):
        commands = await super().sync(guild=guild)
        
        if guild is None:
            logger.info(f"Synced {len(commands)} global commands")
        else:
            logger.info(f"Synced {len(commands)} commands to guild {guild}")
        
        return commands
```

This eliminates the need for logging at each sync call site.

---

## Configuration

### Environment Variables

```bash
# .env
ENV=dev                           # dev or prod
DEV_GUILD_ID=123456789012345678   # Your test server ID
```

### Behavior Matrix

| ENV | DEV_GUILD_ID | Result |
|-----|--------------|--------|
| `dev` | Set | Guild sync (instant) |
| `dev` | Not set | Global sync + warning |
| `prod` | - | Global sync |

---

## Best Practices

1. **Always set `DEV_GUILD_ID` in development** for instant feedback
2. **Only sync when commands change** (names, parameters, descriptions)
3. **Don't sync in loops or frequently** to avoid rate limits
4. **Use guild sync for testing** before deploying globally
