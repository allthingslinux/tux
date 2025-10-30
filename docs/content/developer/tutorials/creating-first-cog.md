# Creating Your First Cog

Learn how to create your first cog in Tux.

## Prerequisites

Before starting this tutorial, make sure you have:

- Completed the [Development Setup](development-setup.md) tutorial
- Understanding of Python basics
- Familiarity with Discord.py concepts

## What is a Cog?

A cog is a class that contains commands, event listeners, and other functionality. Cogs help organize your bot's code into logical modules.

## Step 1: Basic Cog Structure

Create a new file `my_cog.py`:

```python
from discord.ext import commands
from tux.core import BaseCog

class MyCog(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
    
    @commands.command(name="hello")
    async def hello_command(self, ctx):
        """Say hello to the user."""
        await ctx.send(f"Hello, {ctx.author.mention}!")
```

## Step 2: Adding Event Listeners

Add event listeners to your cog:

```python
class MyCog(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready."""
        print(f"{self.bot.user} is ready!")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Called when a message is sent."""
        if message.author.bot:
            return
        
        # Your message handling logic here
        pass
```

## Step 3: Using Tux Features

Leverage Tux's built-in features:

```python
from tux.ui.embeds import TuxEmbed
from tux.services.database import DatabaseService

class MyCog(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.db = DatabaseService()
    
    @commands.command(name="userinfo")
    async def userinfo_command(self, ctx, member: discord.Member = None):
        """Get user information."""
        member = member or ctx.author
        
        embed = TuxEmbed(
            title=f"User Info: {member.display_name}",
            description=f"ID: {member.id}"
        )
        embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d"))
        
        await ctx.send(embed=embed)
```

## Step 4: Error Handling

Add proper error handling:

```python
class MyCog(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
    
    @commands.command(name="divide")
    async def divide_command(self, ctx, a: int, b: int):
        """Divide two numbers."""
        try:
            result = a / b
            await ctx.send(f"{a} ÷ {b} = {result}")
        except ZeroDivisionError:
            await ctx.send("Cannot divide by zero!")
        except commands.BadArgument:
            await ctx.send("Please provide valid numbers!")
```

## Step 5: Loading Your Cog

### Development Loading

```python
# In your main bot file
bot.load_extension("my_cog")
```

### Hot Reload (Development)

```bash
# Use Tux's hot reload feature
tux dev reload my_cog
```

## Step 6: Testing Your Cog

### Basic Testing

```python
# Test your commands
@commands.command(name="test")
async def test_command(self, ctx):
    """Test command for development."""
    await ctx.send("Cog is working!")
```

### Unit Testing

```python
import unittest
from unittest.mock import AsyncMock

class TestMyCog(unittest.TestCase):
    def setUp(self):
        self.bot = AsyncMock()
        self.cog = MyCog(self.bot)
    
    async def test_hello_command(self):
        ctx = AsyncMock()
        ctx.author.mention = "<@123456789>"
        
        await self.cog.hello_command(ctx)
        ctx.send.assert_called_once()
```

## Best Practices

### Code Organization

- Keep related commands in the same cog
- Use descriptive class and method names
- Add proper docstrings
- Follow PEP 8 style guidelines

### Error Handling

- Always handle exceptions
- Provide helpful error messages
- Log errors appropriately
- Use Tux's error handling utilities

### Performance

- Use async/await properly
- Avoid blocking operations
- Cache frequently used data
- Optimize database queries

## Next Steps

After completing this tutorial:

- Learn about [Creating Commands](creating-first-command.md)
- Explore [Database Integration](database-integration.md)
- Check out [UI Components Walkthrough](ui-components-walkthrough.md)
- Review the [Creating Commands Guide](../guides/creating-commands.md) for advanced patterns
