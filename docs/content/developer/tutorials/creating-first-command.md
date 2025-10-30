# Creating Your First Command

Learn how to create your first command in Tux.

## Prerequisites

Before starting this tutorial, make sure you have:

- Completed the [Development Setup](development-setup.md) tutorial
- Created your first cog using the [Creating Your First Cog](creating-first-cog.md) tutorial

## Step 1: Understanding Commands

Commands in Tux are functions that users can invoke with a prefix. They're organized within cogs and follow Discord.py conventions.

## Step 2: Basic Command Structure

Here's a simple command example:

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

## Step 3: Adding Parameters

Commands can accept parameters:

```python
@commands.command(name="greet")
async def greet_command(self, ctx, *, name: str):
    """Greet someone by name."""
    await ctx.send(f"Hello, {name}!")
```

## Step 4: Error Handling

Add proper error handling:

```python
@commands.command(name="divide")
async def divide_command(self, ctx, a: int, b: int):
    """Divide two numbers."""
    try:
        result = a / b
        await ctx.send(f"{a} ÷ {b} = {result}")
    except ZeroDivisionError:
        await ctx.send("Cannot divide by zero!")
```

## Next Steps

After completing this tutorial:

- Learn about [Database Integration](database-integration.md)
- Explore [UI Components Walkthrough](ui-components-walkthrough.md)
- Check out the [Creating Commands Guide](../guides/creating-commands.md) for advanced patterns
