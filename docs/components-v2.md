# Discord Components V2 Guide (funbot/ui/components_v2)

> **For AI Agents**: This document explains Discord.py 2.6+ Components V2 system in detail. Use this as a reference when working with `funbot/ui/v2/` module.

## Overview

Components V2 is a new Discord UI system introduced in discord.py 2.6 that allows mixing text, media, and interactive components in a single message. It uses `discord.ui.LayoutView` instead of `discord.ui.View`.

## Key Differences from Legacy Components

| Aspect | Legacy (`ui.View`) | Components V2 (`ui.LayoutView`) |
|--------|-------------------|--------------------------------|
| Base Class | `discord.ui.View` | `discord.ui.LayoutView` |
| Text Content | Use `content` parameter | Use `ui.TextDisplay` component |
| Embeds | Use `embed`/`embeds` parameter | Use `ui.Container` with components |
| Button/Select Placement | Automatically arranged | Must be in `ui.ActionRow` |
| Images | Single embed image/thumbnail | `ui.MediaGallery` (1-10 images) |
| Max Components | 25 (5 rows × 5) | 40 total (including nested) |
| Sending | `send(content, embed, view)` | `send(view=layout_view)` only |

## Critical Rules

> [!CAUTION]
> When using LayoutView, you **CANNOT** send:
> - `content` parameter
> - `embed` / `embeds` parameter
> - `stickers`
> - `poll`
>
> All content must be inside the LayoutView as components.

> [!WARNING]
> You can convert legacy messages to V2, but **cannot** convert V2 messages back to legacy.

## Top-Level Components

These can be placed directly in a `LayoutView` or `Container`:

### TextDisplay

Displays text content with full markdown support.

```python
import discord
from discord import ui

class MyLayout(ui.LayoutView):
    text = ui.TextDisplay("# Hello World\n**Bold** and *italic* work here!")
```

**Properties:**
- Supports full markdown (headers, bold, italic, code blocks, etc.)
- Mentions (`@user`, `@role`, `@everyone`) will ping
- 4000 character limit shared across ALL TextDisplays in the LayoutView

### ActionRow

Container for buttons and select menus. Max 5 buttons OR 1 select per row.

```python
class MyLayout(ui.LayoutView):
    row = ui.ActionRow()
    
    @row.button(label="Click Me", style=discord.ButtonStyle.primary)
    async def my_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Clicked!", ephemeral=True)
```

**Alternative: Subclass ActionRow**
```python
class MyButtons(ui.ActionRow):
    @ui.button(label="Button A")
    async def button_a(self, interaction, button):
        ...
    
    @ui.button(label="Button B")
    async def button_b(self, interaction, button):
        ...

class MyLayout(ui.LayoutView):
    buttons = MyButtons()
```

### Section

Combines up to 3 TextDisplays with an accessory (Thumbnail or Button).

```python
class MyLayout(ui.LayoutView):
    section = ui.Section(
        ui.TextDisplay("## Title"),
        ui.TextDisplay("Description text here"),
        accessory=ui.Thumbnail("https://example.com/image.png")
    )
```

**Layout visualization:**
```
+--------------------Section--------------------+
| +----------------------------+  +-Accessory-+ |
| |  TextDisplay 1             |  | Thumbnail | |
| |  TextDisplay 2             |  | or Button | |
| |  TextDisplay 3             |  |           | |
| +----------------------------+  +-----------+ |
+-----------------------------------------------+
```

### Separator

Adds visual spacing between components.

```python
class MyLayout(ui.LayoutView):
    text1 = ui.TextDisplay("Above")
    sep = ui.Separator(spacing=discord.SeparatorSpacing.large, divider=True)
    text2 = ui.TextDisplay("Below")
```

**Options:**
- `spacing`: `SeparatorSpacing.small` or `SeparatorSpacing.large`
- `divider`: `True` to show a visible line, `False` for just spacing

### MediaGallery

Displays 1-10 images in a gallery grid.

```python
class MyLayout(ui.LayoutView):
    gallery = ui.MediaGallery(
        discord.MediaGalleryItem("https://example.com/image1.png", description="Alt text"),
        discord.MediaGalleryItem("https://example.com/image2.png", spoiler=True),
    )
```

**With local files:**
```python
file = discord.File("local_image.png")
gallery = ui.MediaGallery(
    discord.MediaGalleryItem(file)
)
# Remember to pass files when sending:
await channel.send(view=layout, files=[file])
```

### Container

Wraps components in a box with optional accent color (like an embed).

```python
class MyLayout(ui.LayoutView):
    container = ui.Container(
        ui.TextDisplay("# Header"),
        ui.Separator(),
        ui.TextDisplay("Content here"),
        accent_color=discord.Color.blurple()
    )
```

**Subclass pattern:**
```python
class MyContainer(ui.Container):
    title = ui.TextDisplay("# My Title")
    sep = ui.Separator()
    content = ui.TextDisplay("My content")

class MyLayout(ui.LayoutView):
    box = MyContainer(accent_color=0x7289da)
```

### File

Displays a file inline (no preview for images - use MediaGallery instead).

```python
file = discord.File("document.pdf")
class MyLayout(ui.LayoutView):
    attached = ui.File(file)

await channel.send(view=layout, files=[file])
```

## Non-Top-Level Components

These MUST be placed inside other components:

### Thumbnail

Image displayed on the right side of a Section.

```python
section = ui.Section(
    ui.TextDisplay("Description"),
    accessory=ui.Thumbnail("https://example.com/thumb.png")
)
```

### Button / Select (in ActionRow)

Same as legacy, but MUST be in an ActionRow for LayoutView:

```python
class MyLayout(ui.LayoutView):
    row = ui.ActionRow()
    
    @row.button(label="Click")
    async def click(self, interaction, button):
        ...
    
    @row.select(placeholder="Choose", options=[...], cls=ui.Select)
    async def choose(self, interaction, select):
        ...
```

## Complete Example: Settings Panel

```python
from discord import ui
import discord

class SettingsView(ui.LayoutView):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        
        # Build the layout
        container = ui.Container(accent_color=discord.Color.blue())
        
        # Header
        container.add_item(ui.TextDisplay("# ⚙️ Settings"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
        
        # Setting with toggle button
        container.add_item(ui.Section(
            ui.TextDisplay("## Notifications"),
            ui.TextDisplay("-# Enable or disable notifications"),
            accessory=NotificationToggle(settings)
        ))
        
        # Add container to view
        self.add_item(container)
        
        # Action buttons at bottom
        row = ui.ActionRow()
        self.add_item(row)
    
    @row.button(label="Save", style=discord.ButtonStyle.green)
    async def save(self, interaction, button):
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("Saved!", ephemeral=True)

class NotificationToggle(ui.Button):
    def __init__(self, settings):
        super().__init__(
            label="On" if settings.notifications else "Off",
            style=discord.ButtonStyle.success if settings.notifications else discord.ButtonStyle.secondary
        )
        self.settings = settings
    
    async def callback(self, interaction):
        self.settings.notifications = not self.settings.notifications
        self.label = "On" if self.settings.notifications else "Off"
        self.style = discord.ButtonStyle.success if self.settings.notifications else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self.view)
```

## Component IDs

All components have a numerical `id` property (different from `custom_id`).

```python
COUNT_DISPLAY_ID = 12345

class MyLayout(ui.LayoutView):
    counter = ui.TextDisplay("Count: 0", id=COUNT_DISPLAY_ID)
    
    def update_count(self, new_count):
        display = self.find_item(COUNT_DISPLAY_ID)
        display.content = f"Count: {new_count}"
```

## Migration Patterns

### From Embed to Container

**Before (Legacy):**
```python
embed = discord.Embed(title="Title", description="Content", color=0x7289da)
await ctx.send(embed=embed, view=my_view)
```

**After (V2):**
```python
class MyLayout(ui.LayoutView):
    container = ui.Container(
        ui.TextDisplay("# Title"),
        ui.TextDisplay("Content"),
        accent_color=0x7289da
    )

await ctx.send(view=MyLayout())
```

### From content to TextDisplay

**Before:**
```python
await ctx.send("Hello, world!", view=my_view)
```

**After:**
```python
class MyLayout(ui.LayoutView):
    text = ui.TextDisplay("Hello, world!")

await ctx.send(view=MyLayout())
```

## Common Pitfalls

1. **Buttons/Selects not in ActionRow**
   ```python
   # ❌ Wrong
   class MyLayout(ui.LayoutView):
       button = ui.Button(label="Click")  # Won't work!
   
   # ✅ Correct
   class MyLayout(ui.LayoutView):
       row = ui.ActionRow()
       @row.button(label="Click")
       async def click(self, i, b): ...
   ```

2. **Sending content with LayoutView**
   ```python
   # ❌ Wrong
   await ctx.send(content="Hello", view=layout_view)
   
   # ✅ Correct
   class Layout(ui.LayoutView):
       text = ui.TextDisplay("Hello")
   await ctx.send(view=Layout())
   ```

3. **Exceeding 40 component limit**
   - Each TextDisplay, Button, Select, Section, etc. counts as 1
   - Nested components also count

4. **Trying to convert V2 message back to legacy**
   ```python
   # ❌ Cannot do this
   message = await ctx.send(view=layout_view)
   await message.edit(content="Back to legacy")  # Error!
   ```

## Best Practices

1. **Use Container for embed-like styling** - accent_color provides the colored border
2. **Use Section for side-by-side layouts** - pair text with button/thumbnail
3. **Use Separator for visual organization** - helps break up content
4. **Keep interactive components in ActionRow** - always wrap buttons/selects
5. **Use TextDisplay's markdown** - headers, bold, code blocks all work
6. **Set component IDs** - makes finding nested items easier

## Project Structure (`funbot/ui/components_v2/`)

```
funbot/ui/components_v2/
├── __init__.py          # Exports all V2 components
├── layout_view.py       # Base LayoutView with error handling
├── container.py         # Container wrapper
├── action_row.py        # ActionRow wrapper
├── text_display.py      # TextDisplay wrapper
├── section.py           # Section wrapper
├── separator.py         # Separator wrapper
├── media_gallery.py     # MediaGallery wrapper
├── thumbnail.py         # Thumbnail wrapper
├── button.py            # V2 Button with loading states
├── select.py            # V2 Select with loading states
├── modal.py             # Re-export of Modal (unchanged)
├── paginator.py         # V2 Paginator
└── confirm.py           # V2 Confirmation view
```

## Usage in Commands

```python
from funbot.ui.components_v2 import LayoutView, Container, TextDisplay, ActionRow

@bot.command()
async def hello(ctx):
    class HelloLayout(LayoutView):
        container = Container(
            TextDisplay("# Hello! 👋"),
            TextDisplay(f"Welcome, {ctx.author.mention}!"),
            accent_color=discord.Color.green()
        )
    
    await ctx.send(view=HelloLayout())
```

## References

- [discord.py Components V2 Documentation](https://discordpy.readthedocs.io/en/stable/interactions/ui.html)
- [Discord Developer Documentation](https://discord.com/developers/docs/components)
