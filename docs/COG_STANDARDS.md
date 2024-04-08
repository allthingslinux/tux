# COG_STANDARDS.md

## Introduction
This document outlines the standards contributors should follow when creating or updating cogs for the Tux Discord bot. Following these guidelines ensures consistent code quality, maintainability, and ease of use across the bot's functionality.

## File Structure & Naming
- Place your cogs in the `tux/cogs` directory, organized by functionality (e.g., `admin`, `utility`, `moderation`).
- Name your cog file descriptively based on its primary function (e.g., `info.py` for information-related commands).
- Use lowercase with underscores (`_`) for file names.

## Cog Class
- Each cog should inherit from `commands.Cog`.
- Initialize your cog class with a constructor accepting a `bot` instance and storing it as an instance variable.
- Clearly comment your code to describe the functionality and any nuances or important details.

### Example:
```python
from discord.ext import commands

class MyCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
```

## Commands
- Use the `@commands.command()` decorator for prefix commands.
- Use the `@app_commands.command()` decorator within a group for slash commands.
- Provide a brief description for each command as part of the decorator to improve help documentation.
- Check permissions appropriately using decorators like `@commands.has_guild_permissions()`.

### Prefix Command Example:
```python
@commands.command(name="mycommand", description="This is a sample command.")
async def my_command(self, ctx: commands.Context, *, arg: str) -> None:
    await ctx.send(f"Argument received: {arg}")
```

### Slash Command Example within a Group:
```python
@group.command(name="myslashcommand", description="This is a sample slash command.")
async def my_slash_command(self, interaction: discord.Interaction, arg: str) -> None:
    await interaction.response.send_message(f"Argument received: {arg}")
```

## Event Listeners
See the [EVENT_STANDARDS.md](EVENT_STANDARDS.md) document for guidelines on implementing event listeners in your cogs.


## Async Setup Function
- Each cog file should have an async setup function at the bottom to load the cog.
- The setup function must accept a `bot` instance and use `await bot.add_cog()`.

### Example:
```python
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MyCog(bot))
```

## Logging
- Use `logger` from `loguru` for logging within your cog.
- Log important events like command usage and errors.

### Example:
```python
from loguru import logger

logger.info("Something was done successfully.")
```

## Error Handling
- Handle exceptions and errors locally within the cog where sensible.
- Provide user-friendly error messages back to the command caller.

## Embeds and Utility Functions
- Use predefined utility functions or classes (e.g., `EmbedCreator`) for consistent styling and behavior.
- Keep embeds informative, concise, and visually appealing.

## Final Remarks
- Review existing cogs for examples and inspiration.
- Code readability, consistency, and simplicity are key.
- Test your changes thoroughly before submitting a pull request.

Thank you for contributing to Tux! Your efforts help make Tux a valuable tool for our community. If you have any questions or need further clarification on these standards, please reach out to the project maintainers.

