# Custom Modules

This directory is for custom modules created by self-hosters. Any Python modules placed in this directory will be automatically discovered and loaded by the bot.

## Creating a Custom Module

1. Create a new Python file in this directory (e.g., `my_custom_module.py`)
2. Define your cog class that inherits from `BaseCog`
3. Implement your commands and functionality
4. The module will be automatically loaded when the bot starts

## Example

```python
from discord.ext import commands
from tux.core.base_cog import BaseCog
from tux.core.bot import Tux

class MyCustomModule(BaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)

    @commands.command(name="hello")
    async def hello_command(self, ctx: commands.Context) -> None:
        """Say hello!"""
        await ctx.send("Hello from my custom module!")

async def setup(bot: Tux) -> None:
    await bot.add_cog(MyCustomModule(bot))
```

## Notes

- Custom modules have the same capabilities as built-in modules
- They can use the dependency injection system
- They follow the same patterns as core modules
- Make sure to follow Python naming conventions for your module files
