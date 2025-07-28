# Dependency Injection Migration Guide

This guide provides step-by-step instructions for migrating existing Tux cogs to use the new dependency injection system.

## Overview

The new dependency injection (DI) system eliminates repetitive initialization code and provides better testability and maintainability. Instead of manually instantiating services in each cog, services are automatically injected based on declared dependencies.

## Migration Process

### Phase 1: Preparation

1. **Backup your code** before starting any migration
2. **Run the migration analysis tool** to identify candidates:

   ```python
   from tux.core.migration import CogMigrationTool
   
   tool = CogMigrationTool()
   results = tool.scan_cogs_directory(Path("tux/cogs"))
   report = tool.create_migration_report(results)
   print(report)
   ```

### Phase 2: Bot Integration

1. **Update bot initialization** to include DI container:

   ```python
   # In tux/bot.py, add to setup method:
   from tux.core.service_registry import ServiceRegistry
   
   async def setup(self) -> None:
       # ... existing setup code ...
       
       # Add DI integration
       self.container = ServiceRegistry.configure_container(self)
   ```

### Phase 3: Cog Migration

#### Step 1: Update Imports

**Before:**

```python
from discord.ext import commands
from tux.database.controllers import DatabaseController
```

**After:**

```python
from discord.ext import commands
from tux.core.base_cog import BaseCog
from tux.core.interfaces import IDatabaseService
```

#### Step 2: Change Base Class

**Before:**

```python
class MyCog(commands.Cog):
```

**After:**

```python
class MyCog(BaseCog):
```

#### Step 3: Update Constructor

**Before:**

```python
def __init__(self, bot: Tux) -> None:
    self.bot = bot
    self.db = DatabaseController()
    self.github = GithubService()
```

**After:**

```python
def __init__(self, bot: Tux) -> None:
    super().__init__(bot)
    # Services are automatically injected via BaseCog
```

#### Step 4: Update Service Usage

**Before:**

```python
@commands.command()
async def my_command(self, ctx):
    result = await self.db.some_table.get_something()
```

**After:**

```python
@commands.command()
async def my_command(self, ctx):
    if self.db_service:
        controller = self.db_service.get_controller()
        result = await controller.some_table.get_something()
    else:
        # Fallback for backward compatibility
        from tux.database.controllers import DatabaseController
        db = DatabaseController()
        result = await db.some_table.get_something()
```

## Migration Examples

### Example 1: Simple Cog Migration

**Before:**

```python
from discord.ext import commands
from tux.bot import Tux
from tux.database.controllers import DatabaseController

class SimpleCog(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()
    
    @commands.command()
    async def test(self, ctx):
        # Use database
        pass
```

**After:**

```python
from discord.ext import commands
from tux.bot import Tux
from tux.core.base_cog import BaseCog

class SimpleCog(BaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
    
    @commands.command()
    async def test(self, ctx):
        if self.db_service:
            db = self.db_service.get_controller()
            # Use database
```

### Example 2: Complex Cog Migration

**Before:**

```python
from discord.ext import commands
from tux.bot import Tux
from tux.database.controllers import DatabaseController
from tux.wrappers.github import GithubService
from tux.ui.embeds import EmbedCreator, EmbedType

class ComplexCog(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()
        self.github = GithubService()
    
    @commands.command()
    async def complex_command(self, ctx):
        # Database operation
        data = await self.db.some_table.get_data()
        
        # GitHub API call
        repo = await self.github.get_repo()
        
        # Create embed
        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedType.INFO,
            title="Result",
            description="Success"
        )
        await ctx.send(embed=embed)
```

**After:**

```python
from discord.ext import commands
from tux.bot import Tux
from tux.core.base_cog import BaseCog
from tux.core.interfaces import IDatabaseService, IExternalAPIService

class ComplexCog(BaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
    
    @commands.command()
    async def complex_command(self, ctx):
        # Database operation
        if self.db_service:
            db = self.db_service.get_controller()
            data = await db.some_table.get_data()
        
        # GitHub API call (if available)
        github_service = self._container.get_optional(IExternalAPIService)
        if github_service:
            repo = await github_service.get_service().get_repo()
        
        # Create embed
        if self.embed_service:
            embed = self.embed_service.create_info_embed(
                title="Result",
                description="Success"
            )
        else:
            # Fallback
            from tux.ui.embeds import EmbedCreator, EmbedType
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedType.INFO,
                title="Result",
                description="Success"
            )
        
        await ctx.send(embed=embed)
```

## Specialized Base Classes

### ModerationBaseCog

For moderation cogs, use the specialized base class:

```python
from tux.core.base_cog import ModerationBaseCog

class BanCog(ModerationBaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
    
    @commands.command()
    async def ban(self, ctx, user, *, reason=None):
        # Moderation logic here
        await self.log_moderation_action("ban", user.id, ctx.author.id, reason)
```

### UtilityBaseCog

For utility cogs:

```python
from tux.core.base_cog import UtilityBaseCog

class InfoCog(UtilityBaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
    
    @commands.command()
    async def info(self, ctx):
        embed = self.create_info_embed("Bot Info", "Information about the bot")
        await ctx.send(embed=embed)
```

## Testing Migration

### Unit Testing with DI

The DI system makes unit testing much easier:

```python
import pytest
from unittest.mock import Mock
from tux.core.container import ServiceContainer
from tux.core.interfaces import IDatabaseService

def test_my_cog():
    # Create mock services
    mock_db = Mock(spec=IDatabaseService)
    mock_bot = Mock()
    
    # Set up container with mocks
    container = ServiceContainer()
    container.register_instance(IDatabaseService, mock_db)
    mock_bot.container = container
    
    # Test the cog
    cog = MyCog(mock_bot)
    assert cog.db_service == mock_db
```

## Troubleshooting

### Common Issues

1. **Service not found**: Ensure the service is registered in `ServiceRegistry`
2. **Circular dependencies**: Check for circular imports or dependencies
3. **Fallback not working**: Verify fallback code matches original implementation

### Debugging

Enable debug logging to see service registration:

```python
import logging
logging.getLogger("tux.core").setLevel(logging.DEBUG)
```

### Rollback Plan

If migration causes issues:

1. Revert to backup
2. Use feature flags to disable DI for specific cogs
3. Gradually re-enable DI after fixing issues

## Best Practices

1. **Migrate incrementally**: Start with simple cogs, then complex ones
2. **Test thoroughly**: Test each migrated cog before moving to the next
3. **Maintain backward compatibility**: Keep fallback code during transition
4. **Document changes**: Update cog documentation to reflect DI usage
5. **Monitor performance**: Ensure DI doesn't impact bot performance

## Benefits After Migration

1. **Reduced boilerplate**: No more repetitive service instantiation
2. **Better testing**: Easy to mock dependencies
3. **Loose coupling**: Services depend on interfaces, not implementations
4. **Centralized configuration**: Single place to manage service instances
5. **Performance**: Singleton services reduce memory usage

## Next Steps

After successful migration:

1. Remove fallback code once all cogs are migrated
2. Add more specialized services as needed
3. Consider adding service decorators for common patterns
4. Implement service health checks and monitoring
