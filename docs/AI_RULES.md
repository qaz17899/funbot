# AI Agent Rules

> Instructions for AI agents working on this codebase. Follow these rules strictly.

---

## Database Migrations (Aerich)

### When to run migrations

| Situation | Required Action |
|-----------|-----------------|
| Modified a model in `funbot/db/models/` | Run `uv run aerich migrate --name <descriptive_name>` |
| Pulled new code with new migration files | Run `uv run aerich upgrade` |
| Need to rollback a migration | Run `uv run aerich downgrade` |

### Migration naming convention

Use descriptive snake_case names:
- `add_language_to_user`
- `create_settings_table`
- `remove_deprecated_field`

### Critical rules

1. **Always review generated migrations** before committing
2. **Never modify a migration that has been merged** to main
3. **Always implement both `upgrade` and `downgrade`** functions
4. **Test locally** before pushing migration changes

### Example workflow

```bash
# After modifying funbot/db/models/user.py

# 1. Generate migration
uv run aerich migrate --name add_language_field

# 2. Review the generated file in migrations/models/

# 3. Apply to local database
uv run aerich upgrade

# 4. Test the bot works

# 5. Commit and push
git add -A && git commit -m "feat(db): add language field to user model"
```

---

## UI Components

### Available components

This project has custom UI components in `funbot/ui/`. **Always check what's available before creating new ones:**

```
funbot/ui/
├── button.py       # Button, GoBackButton
├── confirm.py      # ConfirmView (yes/no dialog)
├── modal.py        # Modal (popup form)
├── paginator.py    # PaginatorView, Page (multi-page content)
├── select.py       # Select, SelectOption (dropdown)
├── text_input.py   # TextInput (text field for modals)
├── toggle.py       # ToggleButton (on/off button)
├── url_button.py   # URLButtonView (link button)
└── view.py         # View (base class)
```

### Usage

```python
from funbot.ui import Button, View, PaginatorView, ConfirmView
```

### Critical rules

1. **Check existing components first** - don't reinvent the wheel
2. **Read the component source** before using - understand parameters and behavior
3. **Use `View` as base class** for custom views
4. **Follow existing patterns** when creating new components

---

## Command Sync

### Environment behavior

| ENV | DEV_GUILD_ID | Behavior |
|-----|--------------|----------|
| dev | Set | Sync to dev guild only (instant) |
| dev | Not set | Sync globally + warning log |
| prod | - | Sync globally |

### Critical rules

1. **Never add sync logic to `on_ready()`** - it runs on every reconnect
2. **CommandTree.sync() already logs** - don't add redundant logging

---

## Code Style

### File organization

```
funbot/
├── bot/       # Bot core (bot.py, command_tree.py, error_handler.py)
├── cogs/      # Feature modules (one file per feature group)
├── db/        # Database (models/, config, database manager)
├── ui/        # Discord UI components
└── utils/     # Shared utilities
```

### Naming conventions

| Type | Convention | Example |
|------|------------|---------|
| Files | snake_case | `user_service.py` |
| Classes | PascalCase | `UserService` |
| Functions | snake_case | `get_user_by_id()` |
| Constants | UPPER_SNAKE | `MAX_RETRIES` |

### Imports

1. Use `TYPE_CHECKING` for type-only imports
2. Order: stdlib → third-party → local

---

## Git Workflow

### Branch naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/<name>` | `feature/add-gacha` |
| Fix | `fix/<issue>` | `fix/sync-rate-limit` |
| Docs | `docs/<topic>` | `docs/architecture` |
| Refactor | `refactor/<scope>` | `refactor/db-layer` |

### Commit messages

Follow Conventional Commits:

```
<type>(<scope>): <description>

Types: feat, fix, docs, refactor, test, chore
```

Examples:
- `feat(db): add language field to user model`
- `fix(bot): prevent duplicate command sync`
- `docs: update migration guide`

---

## Testing

Before pushing any changes:

1. Run `uv run pytest` for unit tests
2. Run `uv run pyright` for type checking
3. Run `uv run ruff check` for linting

---

## Common Mistakes to Avoid

| ❌ Don't | ✅ Do |
|---------|------|
| Put sync in `on_ready()` | Put sync in `setup_hook()` |
| Modify merged migrations | Create new migration to fix |
| Skip `downgrade()` implementation | Always implement rollback |
| Create new UI without checking existing | Check `funbot/ui/` first |
| Use `from x import *` | Import specific names |
| Hardcode config values | Use `CONFIG` from `funbot.config` |
