# 003 - Centralized Embed Factory Implementation Examples

## Overview

This document provides concrete code examples for implementing the centralized embed factory that standardizes 30+ embed creation locations and eliminates inconsistent styling patterns.

---

## Current State Analysis

### ❌ Before: Scattered Embed Creation Patterns

**Pattern 1: Direct discord.Embed() Usage (6+ files):**

```python
# tux/cogs/utility/avatar.py
import discord
from discord.ext import commands

class AvatarCog(commands.Cog):
    @commands.command()
    async def avatar(self, ctx: commands.Context, user: discord.Member = None) -> None:
        user = user or ctx.author
        
        # ❌ Direct embed creation with manual styling
        embed = discord.Embed(
            title="Avatar",
            description=f"Avatar for {user.display_name}",
            color=0x00ff00,  # Hardcoded color
            timestamp=datetime.utcnow()
        )
        embed.set_image(url=user.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)
```

**Pattern 2: EmbedCreator Duplication (15+ files):**

```python
# tux/cogs/moderation/ban.py
from tux.ui.embeds import EmbedCreator, EmbedType

class BanCog(commands.Cog):
    @commands.command()
    async def ban(self, ctx: commands.Context, user: discord.Member, *, reason: str = None) -> None:
        # ❌ Repetitive EmbedCreator usage with manual parameters
        embed = EmbedCreator.create_embed(
            bot=self.bot,  # Manual parameter passing
            embed_type=EmbedType.SUCCESS,
            user_name=ctx.author.name,  # Manual user info extraction
            user_display_avatar=ctx.author.display_avatar.url,  # Manual avatar extraction
            title="User Banned",
            description=f"{user.mention} has been banned.",
            footer_text=f"Banned by {ctx.author}",
        )
        await ctx.send(embed=embed)
```

**Pattern 3: Field Addition Duplication (10+ files):**

```python
# tux/cogs/info/serverinfo.py
class ServerInfoCog(commands.Cog):
    @commands.command()
    async def serverinfo(self, ctx: commands.Context) -> None:
        guild = ctx.guild
        
        # ❌ Manual field addition with inconsistent formatting
        embed = discord.Embed(title="Server Information", color=0x3498db)
        embed.add_field(name="Name", value=guild.name, inline=True)
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
        # ... more manual field additions
```

**Problems with Current Patterns:**
- ❌ Inconsistent colors and styling across embeds
- ❌ Manual parameter passing (bot, user_name, user_display_avatar)
- ❌ Duplicated context extraction logic
- ❌ No centralized branding or theme management
- ❌ Difficult to update styling globally

---

## Proposed Implementation

### ✅ After: Centralized Embed Factory Pattern

#### 1. Enhanced Embed Factory

```python
# tux/ui/embed_factory.py
from __future__ import annotations
from tt Any, Optional
from datetime import datetime
from enum import Enum

import discord
from discord.ext import commands

class EmbedType(Enum):
    """Embed type enumeration with consistent styling."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    HELP = "help"
    LIST = "list"

class EmbedTheme:
    """Centralized theme configuration."""
    COLORS = {
        EmbedType.INFO: 0x3498db,      # Blue
        EmbedType.SUCCESS: 0x2ecc71,   # Green
        EmbedType.WARNING: 0xf39c12,   # Orange
        EmbedType.ERROR: 0xe74c3c,     # Red
        EmbedType.HELP: 0x9b59b6,      # Purple
        EmbedType.LIST: 0x95a5a6,      # Gray
    }
    
    ICONS = {
        EmbedType.INFO: "ℹ️",
        EmbedType.SUCCESS: "✅",
        EmbedType.WARNING: "⚠️",
        EmbedType.ERROR: "❌",
        EmbedType.HELP: "❓",
        EmbedType.LIST: "📋",
    }
    
    FOOTER_TEXT = "Tux Bot"
    FOOTER_ICON = "https://example.com/tux-icon.png"

class EmbedFactory:
    """Centralized embed creation with automatic context extraction."""
    
    def __init__(self, bot: Any = None, ctx: commands.Context = None) -> None:
        self.bot = bot
        self.ctx = ctx
        self._auto_extract_context()
    
    def _auto_extract_context(self) -> None:
        """Automatically extract context information."""
        if self.ctx:
            self.user = self.ctx.author
            self.user_name = self.ctx.author.name
            self.user_display_name = self.ctx.author.display_name
            self.user_avatar = self.ctx.author.display_avatar.url
            self.guild = self.ctx.guild
            self.channel = self.ctx.channel
        else:
            self.user = None
            self.user_name = None
            self.user_display_name = None
            self.user_avatar = None
            self.guild = None
            self.channel = None
    
    def create_embed(
        self,
        embed_type: EmbedType,
        title: str,
        description: str = None,
        fields: list[dict] = None,
        thumbnail: str = None,
        image: str = None,
        footer_text: str = None,
        footer_icon: str = None,
        timestamp: bool = True,
        **kwargs
    ) -> discord.Embed:
        """Create a standardized embed with automatic styling."""
        
        # Create embed with theme colors
        embed = discord.Embed(
            title=f"{EmbedTheme.ICONS[embed_type]} {title}",
            description=description,
            color=EmbedTheme.COLORS[embed_type],
            timestamp=datetime.utcnow() if timestamp else None
        )
        
        # Add fields if provided
        if fields:
            for field in fields:
                embed.add_field(
                    name=field.get("name", ""),
                    value=field.get("value", ""),
                    inline=field.get("inline", True)
                )
        
        # Set thumbnail and image
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if image:
            embed.set_image(url=image)
        
        # Set footer with automatic context
        footer_text = footer_text or EmbedTheme.FOOTER_TEXT
        footer_icon = footer_icon or EmbedTheme.FOOTER_ICON
        
        if self.user and not footer_text.startswith("Requested by"):
            footer_text = f"Requested by {self.user_display_name}"
            footer_icon = self.user_avatar
        
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        return embed
    
    def create_info_embed(self, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create an info embed."""
        return self.create_embed(EmbedType.INFO, title, description, **kwargs)
    
    def create_success_embed(self, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create a success embed."""
        return self.create_embed(EmbedType.SUCCESS, title, description, **kwargs)
    
    def create_warning_embed(self, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create a warning embed."""
        return self.create_embed(EmbedType.WARNING, title, description, **kwargs)
    
    def create_error_embed(self, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create an error embed."""
        return self.create_embed(EmbedType.ERROR, title, description, **kwargs)
    
    def create_help_embed(self, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create a help embed."""
        return self.create_embed(EmbedType.HELP, title, description, **kwargs)
    
    def create_list_embed(
        self,
        title: str,
        items: list[str],
        description: str = None,
        items_per_page: int = 10,
        page: int = 1,
        **kwargs
    ) -> discord.Embed:
        """Create a paginated list embed."""
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_items = items[start_idx:end_idx]
        
        # Format items as numbered list
        formatted_items = "\n".join(f"{i + start_idx + 1}. {item}" for i, item in enumerate(page_items))
        
        total_pages = (len(items) + items_per_page - 1) // items_per_page
        page_info = f"Page {page}/{total_pages} • {len(items)} total items"
        
        embed = self.create_embed(
            EmbedType.LIST,
            title,
            description=f"{description}\n\n{formatted_items}" if description else formatted_items,
            footer_text=page_info,
            **kwargs
        )
        
        return embed
```

#### 2. Context-Aware Factory Service

```python
# tux/core/services.py (Addition to existing services)
from tux.ui.embed_factory import EmbedFactory, EmbedType
from tux.core.interfaces import IEmbedService

class EmbedService(IEmbedService):
    """Enhanced embed service with factory integration."""
    
    def __init__(self, bot: Any) -> None:
        self.bot = bot
    
    def create_factory(self, ctx: commands.Context = None) -> EmbedFactory:
        """Create a context-aware embed factory."""
        return EmbedFactory(bot=self.bot, ctx=ctx)
    
    def create_info_embed(self, title: str, description: str = None, ctx: commands.Context = None, **kwargs) -> discord.Embed:
        """Create an info embed with context."""
        factory = self.create_factory(ctx)
        return factory.create_info_embed(title, description, **kwargs)
    
    def create_success_embed(self, title: str, description: str = None, ctx: commands.Context = None, **kwargs) -> discord.Embed:
        """Create a success embed with context."""
        factory = self.create_factory(ctx)
        return factory.create_success_embed(title, description, **kwargs)
    
    def create_error_embed(self, title: str, description: str = None, ctx: commands.Context = None, **kwargs) -> discord.Embed:
        """Create an error embed with context."""
        factory = self.create_factory(ctx)
        return factory.create_error_embed(title, description, **kwargs)
```

#### 3. Base Cog Integration

```python
# tux/core/base_cog.py (Enhanced with embed factory)
from tux.ui.embed_factory import EmbedFactory
from tux.core.interfaces import IEmbedService

class BaseCog(commands.Cog):
    """Base cog with embed factory integration."""
    
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        # Embed service injected via DI
        self.embed_service = self._container.get_optional(IEmbedService) if self._container else None
    
    def create_embed_factory(self, ctx: commands.Context = None) -> EmbedFactory:
        """Create a context-aware embed factory."""
        if self.embed_service:
            return self.embed_service.create_factory(ctx)
        else:
            # Fallback
            return EmbedFactory(bot=self.bot, ctx=ctx)
    
    def create_info_embed(self, ctx: commands.Context, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Convenience method for creating info embeds."""
        factory = self.create_embed_factory(ctx)
        return factory.create_info_embed(title, description, **kwargs)
    
    def create_success_embed(self, ctx: commands.Context, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Convenience method for creating success embeds."""
        factory = self.create_embed_factory(ctx)
        return factory.create_success_embed(title, description, **kwargs)
    
    def create_error_embed(self, ctx: commands.Context, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Convenience method for creating error embeds."""
        factory = self.create_embed_factory(ctx)
        return factory.create_error_embed(title, description, **kwargs)
```

#### 4. Migrated Cog Examples

**Example 1: Avatar Command (was direct discord.Embed):**

```python
# tux/cogs/utility/avatar.py (After migration)
from tux.core.base_cog import BaseCog

class AvatarCog(BaseCog):
    @commands.command()
    async def avatar(self, ctx: commands.Context, user: discord.Member = None) -> None:
        user = user or ctx.author
        
        # ✅ Use centralized embed factory
        embed = self.create_info_embed(
            ctx=ctx,
            title="Avatar",
            description=f"Avatar for {user.display_name}",
            image=user.display_avatar.url
        )
        
        await ctx.send(embed=embed)
```

**Example 2: Ban Command (was EmbedCreator duplication):**

```python
# tux/cogs/moderation/ban.py (After migration)
from tux.core.base_cog import BaseCog

class BanCog(BaseCog):
    @commands.command()
    async def ban(self, ctx: commands.Context, user: discord.Member, *, reason: str = None) -> None:
        # Perform ban logic...
        
        # ✅ Use centralized embed factory with automatic context
        embed = self.create_success_embed(
            ctx=ctx,
            title="User Banned",
            description=f"{user.mention} has been banned.",
            fields=[
                {"name": "Reason", "value": reason or "No reason provided", "inline": False},
                {"name": "Moderator", "value": ctx.author.mention, "inline": True},
                {"name": "User ID", "value": str(user.id), "inline": True}
            ]
        )
        
        await ctx.send(embed=embed)
```

**Example 3: Server Info (was manual field addition):**

```python
# tux/cogs/info/serverinfo.py (After migration)
from tux.core.base_cog import BaseCog

class ServerInfoCog(BaseCog):
    @commands.command()
    async def serverinfo(self, ctx: commands.Context) -> None:
        guild = ctx.guild
        
        # ✅ Use structured field approach
        fields = [
            {"name": "Name", "value": guild.name, "inline": True},
            {"name": "ID", "value": str(guild.id), "inline": True},
            {"name": "Owner", "value": guild.owner.mention, "inline": True},
            {"name": "Members", "value": str(guild.member_count), "inline": True},
            {"name": "Created", "value": guild.created_at.strftime("%Y-%m-%d"), "inline": True},
            {"name": "Boost Level", "value": f"Level {guild.premium_tier}", "inline": True}
        ]
        
        embed = self.create_info_embed(
            ctx=ctx,
            title="Server Information",
            description=f"Information about {guild.name}",
            fields=fields,
            thumbnail=guild.icon.url if guild.icon else None
        )
        
        await ctx.send(embed=embed)
```

---

## Advanced Features

### 1. Paginated List Embeds

```python
# tux/cogs/utility/list_commands.py
class ListCommandsCog(BaseCog):
    @commands.command()
    async def commands(self, ctx: commands.Context, page: int = 1) -> None:
        """List all available commands with pagination."""
        all_commands = [cmd.name for cmd in self.bot.commands]
        
        # ✅ Use built-in pagination support
        embed = self.create_embed_factory(ctx).create_list_embed(
            title="Available Commands",
            description="Here are all the available commands:",
            items=all_commands,
            items_per_page=15,
            page=page
        )
        
        await ctx.send(embed=embed)
```

### 2. Dynamic Theme Support

```python
# tux/ui/embed_factory.py (Theme customization)
class EmbedFactory:
    def __init__(self, bot: Any = None, ctx: commands.Context = None, theme: str = "default") -> None:
        self.bot = bot
        self.ctx = ctx
        self.theme = self._load_theme(theme)
        self._auto_extract_context()
    
    def _load_theme(self, theme_name: str) -> dict:
        """Load theme configuration."""
        themes = {
            "default": EmbedTheme,
            "dark": DarkEmbedTheme,
            "light": LightEmbedTheme,
            "christmas": ChristmasEmbedTheme
        }
        return themes.get(theme_name, EmbedTheme)
    
    @classmethod
    def with_theme(cls, theme: str, bot: Any = None, ctx: commands.Context = None) -> 'EmbedFactory':
        """Create factory with specific theme."""
        return cls(bot=bot, ctx=ctx, theme=theme)

# Usage in cogs
class SpecialEventCog(BaseCog):
    @commands.command()
    async def christmas_info(self, ctx: commands.Context) -> None:
        factory = EmbedFactory.with_theme("christmas", bot=self.bot, ctx=ctx)
        embed = factory.create_info_embed(
            title="Christmas Event",
            description="Special Christmas event is now active!"
        )
        await ctx.send(embed=embed)
```

### 3. Embed Templates

```python
# tux/ui/embed_templates.py
class EmbedTemplates:
    """Pre-defined embed templates for common use cases."""
    
    @staticmethod
    def user_profile(factory: EmbedFactory, user: discord.Member) -> discord.Embed:
        """Standard user profile embed."""
        return factory.create_info_embed(
            title=f"User Profile: {user.display_name}",
            description=f"Profile information for {user.mention}",
            fields=[
                {"name": "Username", "value": str(user), "inline": True},
                {"name": "ID", "value": str(user.id), "inline": True},
                {"name": "Joined Server", "value": user.joined_at.strftime("%Y-%m-%d"), "inline": True},
                {"name": "Account Created", "value": user.created_at.strftime("%Y-%m-%d"), "inline": True},
                {"name": "Roles", "value": f"{len(user.roles)} roles", "inline": True},
                {"name": "Status", "value": str(user.status).title(), "inline": True}
            ],
            thumbnail=user.display_avatar.url
        )
    
    @staticmethod
    def moderation_action(factory: EmbedFactory, action: str, target: discord.Member, moderator: discord.Member, reason: str = None) -> discord.Embed:
        """Standard moderation action embed."""
        return factory.create_success_embed(
            title=f"Moderation Action: {action.title()}",
            description=f"{target.mention} has been {action}.",
            fields=[
                {"name": "Target", "value": f"{target.mention} ({target.id})", "inline": True},
                {"name": "Moderator", "value": f"{moderator.mention} ({moderator.id})", "inline": True},
                {"name": "Reason", "value": reason or "No reason provided", "inline": False}
            ]
        )

# Usage in cogs
class ModerationCog(BaseCog):
    @commands.command()
    async def userinfo(self, ctx: commands.Context, user: discord.Member = None) -> None:
        user = user or ctx.author
        factory = self.create_embed_factory(ctx)
        embed = EmbedTemplates.user_profile(factory, user)
        await ctx.send(embed=embed)
```

---

## Migration Steps

### Phase 1: Infrastructure Setup (Week 1)

1. **Create Embed Factory:**
```bash
touch tux/ui/embed_factory.py
touch tux/ui/embed_templates.py
```

2. **Implement Core Factory:**
```python
# Implement EmbedFactory class
# Define EmbedType enum
# Create EmbedTheme configuration
```

### Phase 2: Service Integration (Week 1)

1. **Enhance Embed Service:**
```python
# Update IEmbedService interface
# Implement EmbedService with factory integration
# Register service in ServiceRegistry
```

2. **Update Base Cog:**
```python
# Add embed factory methods to BaseCog
# Provide convenience methods
# Maintain backward compatibility
```

### Phase 3: Cog Migration (Week 2-3)

1. **Migration Priority:**
```python
# Week 2: High-usage cogs (moderation, utility)
# Week 3: Remaining cogs (info, fun, admin)
```

2. **Migration Pattern:**
```python
# Replace direct discord.Embed() -> self.create_info_embed()
# Replace EmbedCreator calls -> factory methods
# Consolidate field addition -> fields parameter
# Remove manual parameter passing
```

### Phase 4: Testing and Polish (Week 3-4)

1. **Visual Testing:**
```python
# Test all embed types for consistency
# Verify theme application
# Check responsive design
```

2. **Performance Testing:**
```python
# Measure embed creation performance
# Test memory usage
# Validate caching effectiveness
```

---

## Testing Examples

### Unit Testing

```python
# tests/test_embed_factory.py
import pytest
from unittest.mock import Mock
from tux.ui.embed_factory import EmbedFactory, EmbedType

def test_embed_factory_creation():
    # Arrange
    ctx = Mock()
    ctx.author.name = "TestUser"
    ctx.author.display_name = "Test User"
    ctx.author.display_avatar.url = "https://example.com/avatar.png"
    
    # Act
    factory = EmbedFactory(ctx=ctx)
    embed = factory.create_info_embed("Test Title", "Test Description")
    
    # Assert
    assert embed.title == "ℹ️ Test Title"
    assert embed.description == "Test Description"
    assert embed.color.value == 0x3498db  # Info color
    assert "Test User" in embed.footer.text

def test_embed_factory_fields():
    # Arrange
    factory = EmbedFactory()
    fields = [
        {"name": "Field 1", "value": "Value 1", "inline": True},
        {"name": "Field 2", "value": "Value 2", "inline": False}
    ]
    
    # Act
    embed = factory.create_info_embed("Test", fields=fields)
    
    # Assert
    assert len(embed.fields) == 2
    assert embed.fields[0].name == "Field 1"
    assert embed.fields[0].value == "Value 1"
    assert embed.fields[0].inline == True
```

### Integration Testing

```python
# tests/integration/test_embed_integration.py
import pytest
from tux.core.base_cog import BaseCog
from tux.ui.embed_factory import EmbedType

class TestCog(BaseCog):
    @commands.command()
    async def test_command(self, ctx):
        embed = self.create_success_embed(ctx, "Test", "Success message")
        await ctx.send(embed=embed)

@pytest.mark.asyncio
async def test_cog_embed_integration(mock_bot, mock_ctx):
    # Arrange
    cog = TestCog(mock_bot)
    
    # Act
    await cog.test_command(mock_ctx)
    
    # Assert
    mock_ctx.send.assert_called_once()
    embed = mock_ctx.send.call_args[1]['embed']
    assert embed.title == "✅ Test"
    assert embed.description == "Success message"
```

### Visual Testing

```python
# tests/visual/test_embed_appearance.py
def test_embed_color_consistency():
    """Test that all embed types have consistent colors."""
    factory = EmbedFactory()
    
    embeds = {
        'info': factory.create_info_embed("Info", "Test"),
        'success': factory.create_success_embed("Success", "Test"),
        'warning': factory.create_warning_embed("Warning", "Test"),
        'error': factory.create_error_embed("Error", "Test"),
        'help': factory.create_help_embed("Help", "Test")
    }
    
    expected_colors = {
        'info': 0x3498db,
        'success': 0x2ecc71,
        'warning': 0xf39c12,
        'error': 0xe74c3c,
        'help': 0x9b59b6
    }
    
    for embed_type, embed in embeds.items():
        assert embed.color.value == expected_colors[embed_type]
        assert embed.title.startswith(('ℹ️', '✅', '⚠️', '❌', '❓'))
```

---

## Success Metrics

### Quantitative Targets
- ✅ **6+ direct discord.Embed() eliminated**: `grep -r "discord.Embed(" tux/cogs/` returns 0 results
- ✅ **15+ EmbedCreator patterns standardized**: All use factory methods
- ✅ **30+ embed locations consistent**: All use centralized styling
- ✅ **70% boilerplate reduction**: Average 10 lines removed per embed creation

### Validation Commands
```bash
# Check for remaining direct embed usage
grep -r "discord.Embed(" tux/cogs/

# Check for old EmbedCreator patterns
grep -r "EmbedCreator.create_embed" tux/cogs/

# Check for factory usage
grep -r "create_.*_embed" tux/cogs/ | wc -l

# Visual consistency check
python -c "from tux.ui.embed_factory import EmbedFactory; f = EmbedFactory(); print('Colors consistent:', all(hasattr(f.theme, 'COLORS')))"
```

### Visual Validation
```bash
# Test embed appearance
python tests/visual/embed_preview.py

# Generate embed samples
python scripts/generate_embed_samples.py --output samples/
```

This centralized embed factory provides consistent, professional styling across all bot interactions while dramatically reducing boilerplate code and improving maintainability.
