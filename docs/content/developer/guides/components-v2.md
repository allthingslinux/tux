---
title: Components V2 Guide
description: Complete guide to using Discord.py Components V2 in Tux, including LayoutView, modals, and all component types with practical examples.
tags:
  - developer-guide
  - guides
  - ui
  - components
---

# Components V2 Guide

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

Discord.py 2.6+ introduced Components V2, a modern component system that provides enhanced layout capabilities and better organization. This guide covers how to use Components V2 in Tux.

## Overview

Components V2 introduces a new layout system with enhanced capabilities:

- **LayoutView** - Modern component system with flexible layouts
- **Container** - Embed-like boxes with accent colors
- **Section** - Text with accessory components
- **TextDisplay** - Markdown-formatted text
- **Enhanced Limits** - Up to 40 components total (including nested)

## Key Constraints

**Important limitations to be aware of:**

- Cannot send `content`, `embeds`, `stickers`, or `polls` with Components V2
- TextDisplay and Container replace content/embeds
- Max 40 components total (including nested)
- Max 4000 characters across all TextDisplay items (accumulative)
- Can convert old messages to V2, but cannot convert V2 back to old format
- Links in TextDisplay don't auto-embed website previews
- Container doesn't support fields, author, or footer
- Attachments won't show by default - they must be exposed through components

## LayoutView vs View

### LayoutView (Components V2)

**Modern system with enhanced capabilities:**

- Define items as class variables (no manual `add_item` needed)
- Buttons/Selects must be in ActionRow (except Section accessory)
- `row=` kwarg ignored
- Supports: ActionRow, Container, File, MediaGallery, Section, Separator, TextDisplay

### View (Legacy System)

**Still supported, but limited:**

- Max 25 top-level components
- Max 5 ActionRows
- Auto-arranges components

## Basic LayoutView Example

```python
from discord.ext import commands
from discord import ui
import discord

class MyLayout(ui.LayoutView):
    text = ui.TextDisplay("Hello", id=1234)
    action_row = ui.ActionRow()

    @action_row.button(label="Click")
    async def btn(self, i: discord.Interaction, btn: ui.Button):
        await i.response.send_message("Hi!")

# Usage
@bot.command()
async def test(ctx):
    await ctx.send(view=MyLayout())
```

## Component Types & Limits

### Component Reference Table

| Component | Type | Max Children | Char Limit | Notes |
|-----------|------|--------------|------------|-------|
| ActionRow | 1 | 5 buttons OR 1 select | - | Top-level in LayoutView |
| Button | 2 | - | 80 (label) | In ActionRow or Section accessory |
| StringSelect | 3 | 25 options | 150 (placeholder) | In ActionRow/Label |
| TextInput | 4 | - | 4000 (value), 100 (placeholder) | In Label only |
| UserSelect | 5 | - | 150 (placeholder) | In ActionRow/Label |
| RoleSelect | 6 | - | 150 (placeholder) | In ActionRow/Label |
| MentionableSelect | 7 | - | 150 (placeholder) | In ActionRow/Label |
| ChannelSelect | 8 | - | 150 (placeholder) | In ActionRow/Label |
| Section | 9 | 1-3 TextDisplay | - | Top-level, 1 accessory |
| TextDisplay | 10 | - | 4000 (total per message) | LayoutView/Modal/Section/Container |
| Thumbnail | 11 | - | 1024 (description) | Section accessory only |
| MediaGallery | 12 | 1-10 items | 1024 (description per item) | Top-level |
| File | 13 | - | - | Top-level, local files only |
| Separator | 14 | - | - | Top-level only |
| Container | 17 | ≥1 | - | Top-level, embed-like box |
| Label | 18 | 1 component | 45 (text), 100 (description) | Modal only |
| FileUpload | 19 | - | - | In Label, 0-10 files |

### Global Limits

- `custom_id`: 100 chars, must be unique per component on same message
- `id`: Optional 32-bit integer (0 to 2,147,483,647), auto-generated sequentially if omitted
- Sending `id` of `0` is treated as empty and replaced by API
- LayoutView: 40 components (including nested)
- Modal: 5 top-level components
- View: 25 top-level components

## ActionRow

Container for interactive components. In LayoutView, must be manually defined.

**Weight system:**

- Each button/select has width of 5
- Maximum total weight is 5 (can hold 5 buttons OR 1 select)

```python
class MyRow(ui.ActionRow):
    @ui.button(label="Btn", style=discord.ButtonStyle.primary)
    async def btn(self, i: discord.Interaction, btn: ui.Button):
        await i.response.send_message("Hi!")

# Or inline
row = ui.ActionRow()
@row.button(label="Click")
async def click(self, i: discord.Interaction, btn: ui.Button):
    pass
```

## Button Styles

**Available styles:**

- **Primary (1)** - Most important (one per ActionRow recommended)
- **Secondary (2)** - Alternative actions (use for equal-significance buttons)
- **Success (3)** - Positive confirmation
- **Danger (4)** - Irreversible consequences
- **Link (5)** - URL navigation (requires `url`, no `custom_id`)
- **Premium (6)** - Purchase (requires `sku_id`, no `custom_id`/`label`/`url`/`emoji`)

**Content limits:**

- 34 chars max with icon/emoji
- 38 chars max without icon/emoji

**Field requirements:**

- Non-link/non-premium: Must have `custom_id`, cannot have `url` or `sku_id`
- Link: Must have `url`, cannot have `custom_id`
- Premium: Must have `sku_id`, cannot have `custom_id`, `label`, `url`, or `emoji`

## Select Menus

All select types support:

- `min_values` (0-25)
- `max_values` (1-25)
- `placeholder` (150 chars)
- `default_values`

**Common behavior:**

- `required`: Only available in modals
- `disabled`: Only available in messages (defaults to `false`)
- `default_values`: Array of objects with `id` (snowflake) and `type`

### StringSelect

Custom options (max 25):

```python
select = ui.StringSelect(
    placeholder="Choose an option",
    options=[
        discord.SelectOption(label="Option 1", value="1"),
        discord.SelectOption(label="Option 2", value="2"),
    ]
)

@select.callback
async def select_callback(self, i: discord.Interaction):
    selected = select.values  # Array of option values
```

### Entity Selects

**UserSelect** - Members/users:

```python
user_select = ui.UserSelect(placeholder="Select users")
# Access: user_select.values (array of user IDs)
# Full data in: i.data['resolved']['users']
```

**RoleSelect** - Guild roles:

```python
role_select = ui.RoleSelect(placeholder="Select roles")
# Access: role_select.values (array of role IDs)
```

**MentionableSelect** - Members + roles:

```python
mentionable = ui.MentionableSelect(placeholder="Select user or role")
# Access: mentionable.values (array of IDs)
```

**ChannelSelect** - Channels:

```python
channel_select = ui.ChannelSelect(
    placeholder="Select channel",
    channel_types=[discord.ChannelType.text]
)
# Access: channel_select.values (array of channel IDs)
```

## TextDisplay

Markdown-formatted text component:

```python
text = ui.TextDisplay("# Header\n**Bold** *italic* `code`", id=100)
```

**Features:**

- Can be used in LayoutView, Modal, Section, or Container
- 4000 char limit shared across entire LayoutView/Modal
- Supports full markdown
- Pings work everywhere (even in Container)

## Container

Embed-like box with border and optional accent color:

```python
container = ui.Container(
    ui.TextDisplay("Content"),
    ui.Section(...),
    ui.MediaGallery(...),
    accent_color=0x5865F2,
    spoiler=False
)
```

**Can contain:** ActionRow, TextDisplay, Section, MediaGallery, Separator, File

**Differences from Embeds:**

- No fields, author, footer, timestamp
- Multiple images via MediaGallery
- Multiple Sections
- Mentions ping
- 4000 char limit (accumulative)
- Extreme layout flexibility

## Section

Associates text with an accessory (Button or Thumbnail):

```python
section = ui.Section(
    "Text auto-wrapped in TextDisplay",
    ui.TextDisplay("Or explicit TextDisplay"),
    accessory=ui.Thumbnail(media="attachment://img.png")
)
```

- 1-3 TextDisplay children
- 1 accessory (Button or Thumbnail)
- Strings auto-wrapped in TextDisplay

## MediaGallery

Display 1-10 images/videos in gallery:

```python
file = discord.File("img.png")
gallery = ui.MediaGallery(
    discord.MediaGalleryItem("https://url.com/img.png", description="Alt text"),
    discord.MediaGalleryItem(file, spoiler=True)
)
await channel.send(view=view, files=[file])
```

**Notes:**

- MediaGalleryItem: `description` (1024 chars), `spoiler`, `media`
- Can use URLs or local files (discord.File)
- Must send files separately

## Modals

Modals support TextDisplay, Label (with TextInput, Selects, FileUpload), and up to 5 top-level components.

```python
class MyModal(ui.Modal, title="Survey"):
    header = ui.TextDisplay("# Survey")

    feedback = ui.Label(
        text="Feedback",
        description="Tell us what you think",
        component=ui.TextInput(
            custom_id="feedback",
            style=discord.TextStyle.paragraph,
            min_length=100,
            max_length=4000
        )
    )

    async def on_submit(self, i: discord.Interaction):
        value = self.feedback.component.value
        await i.response.send_message(f"Thanks! You said: {value}")
```

**Note:** Modals cannot be sent as response to another modal.

## Label (Modal only)

Wraps modal components with label and description:

```python
ui.Label(
    text="Name",
    description="Enter your name",
    component=ui.TextInput(custom_id="name", style=discord.TextStyle.short)
)
```

**Can contain:** TextInput, all Select types, FileUpload

**Limits:**

- `label`: Max 45 characters
- `description`: Max 100 characters

## FileUpload (Modal only)

Allow users to upload files in modals:

```python
ui.FileUpload(custom_id="files", min_values=0, max_values=10, required=True)
```

**Features:**

- 0-10 files (`min_values` 0-10, `max_values` 1-10)
- `min_values`: Defaults to `0`
- `max_values`: Defaults to `1`
- `required`: Defaults to `True`
- Must be in Label

**Accessing uploaded files:**

```python
async def on_submit(self, i: discord.Interaction):
    files = self.file_upload.values  # List[discord.Attachment]
    # Or via Label
    files = self.label.component.values
```

## Common Patterns

### Embed-like Container

```python
class EmbedView(ui.LayoutView):
    def __init__(self, url: str):
        super().__init__()
        section = ui.Section(
            ui.TextDisplay("Description"),
            accessory=ui.Thumbnail(media=url)
        )
        container = ui.Container(section, accent_color=0x5865F2)
        self.add_item(container)
```

### Dynamic Updates

```python
TEXT_ID = 100

class CounterView(ui.LayoutView):
    def __init__(self):
        super().__init__()
        self.count = 0
        container = ui.Container(
            ui.Section(
                ui.TextDisplay(f"Count: {self.count}", id=TEXT_ID),
                accessory=self.CounterButton()
            )
        )
        self.add_item(container)

    class CounterButton(ui.Button):
        def __init__(self):
            super().__init__(label="+1", style=discord.ButtonStyle.primary)

        async def callback(self, i: discord.Interaction):
            self.view.count += 1
            text = self.view.find_item(TEXT_ID)
            text.content = f"Count: {self.view.count}"
            await i.response.edit_message(view=self.view)
```

### Settings Panel

```python
class Settings(ui.LayoutView):
    def __init__(self):
        super().__init__()
        container = ui.Container()
        container.add_item(ui.TextDisplay("# Settings"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
        container.add_item(ui.Section(
            ui.TextDisplay("Option description"),
            accessory=MyButton()
        ))
        self.add_item(container)
```

## Best Practices

1. **Use Container for embed-like grouping** - Provides visual organization
2. **Use Section for label + accessory layouts** - Clean text + button/thumbnail combinations
3. **Use Separator for visual organization** - Improves readability
4. **Store component refs as instance vars** - Easier updates and access
5. **Use `find_item(id)` for nested access** - Find components by numerical ID
6. **Subclass ActionRow for reusable button/select groups** - Better code organization
7. **Pass strings to Section for auto-wrapped TextDisplay** - Cleaner code
8. **One Primary button per ActionRow** - Follows design guidelines
9. **Use Secondary for equal-significance buttons** - Better UX
10. **Remember limits** - 40 components, 4000 chars total, 1-10 gallery items

## LayoutView Methods

**Useful methods for component management:**

- `walk_children()` - Yields all children including nested
- `find_item(id)` - Find component by numerical ID
- `content_length()` - Total characters across all TextDisplay
- `total_children_count` - Count including nested children
- `add_item()`, `remove_item()`, `clear_items()` - Standard methods

## Component IDs

All components have numerical `id` (not `custom_id`):

```python
TEXT_ID = 100
text = ui.TextDisplay("Count: 0", id=TEXT_ID)
# Later:
text = self.view.find_item(TEXT_ID)
text.content = "Count: 1"
```

## Sending Messages

```python
# LayoutView only
await channel.send(view=MyLayout())

# With files
await channel.send(view=MyLayout(), files=[file1, file2])

# Webhooks (non-interactive only)
await webhook.send(view=MyLayout())
```

## Persistent Views

- Same `custom_id` buttons/selects work when migrating View → LayoutView
- Can edit old messages to use V2 (clear `content`/`embeds` with None)
- Cannot edit V2 back to old components

## Legacy Behavior

Pre-V2 messages:

- Max 5 ActionRows as top-level
- Can include `content` and `embeds`
- Components have `id` of 0
- Still supported, not deprecated
- Both systems can coexist in same bot

## Resources

- **Discord.py Documentation**: <https://discordpy.readthedocs.io/en/stable/interactions/ui.html>
- **Components V2 API**: <https://discord.com/developers/docs/interactions/message-components>
- **Source Code**: `src/tux/ui/` (Tux UI components)
