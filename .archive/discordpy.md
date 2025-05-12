# Discord.py Development Guide

This guide focuses on advanced patterns, architectural decisions, and best practices for developing with discord.py in our project.

## Cogs and Extensions

Cogs are the backbone of our command organization. Each cog represents a collection of related commands, listeners, and state management.

There comes a point in your bot’s development when you want to organize a collection of commands, listeners, and some state into one class. Cogs allow you to do just that.

It should be noted that cogs are typically used alongside with Extensions.

An extension at its core is a python file with an entry point called setup. This setup function must be a Python coroutine. It takes a single parameter of the Bot that loads the extension.

With regards to Tux, we typically define one cog per extension. This allows us to keep our code organized and modular.

Furthermore, we have a `CogLoader` class that loads our cogs (technically, extensions) from the `cogs` directory and registers them with the bot at startup.

### Cog Essentials

- Each cog is a Python class that subclasses commands.Cog.
- Every regular command or "prefix" is marked with the `@commands.command()` decorator.
- Every app or "slash" command is marked with the `@app_commands.command()` decorator.
- Every hybrid command is marked with the `@commands.hybrid_command()` decorator.
- Every listener is marked with the `@commands.Cog.listener()` decorator.

tl;dr - Extensions are imported "modules", cogs are classes that are subclasses of `commands.Cog`.

### Cog Structure

### Extension Loading

We use a custom [CogLoader](https://github.com/allthingslinux/tux/blob/main/tux/cog_loader.py) to manage our extensions.

More information can be found about it in [core.md](core.md#cog-loading-system-cog_loaderpy)

## Advanced Patterns

### Command Groups and Subcommands

### Context Menus

```python
@app_commands.context_menu(name='Report Message')
async def report_message(self, interaction: discord.Interaction, message: discord.Message):
    """Report a message via context menu"""
    modal = ReportModal(message)
    await interaction.response.send_modal(modal)
```

### Views and UI Components

```python
class PaginationView(discord.ui.View):
    def __init__(self, pages: list[discord.Embed]):
        super().__init__(timeout=180)
        self.pages = pages
        self.current_page = 0

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = (self.current_page - 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.current_page])

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = (self.current_page + 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.current_page])
```

### Modals

```python
class ReportModal(discord.ui.Modal, title='Report Message'):
    reason = discord.ui.TextInput(
        label='Reason',
        placeholder='Why are you reporting this message?',
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f'Thank you for your report. We will review it shortly.',
            ephemeral=True
        )
```

### Error Handling

```python
@commands.Cog.listener()
async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command!")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.2f}s")
    else:
        logger.error(f"Unhandled error: {error}", exc_info=error)
```

## Best Practices

### Command Design

1. **Use Type Hints**

```python
async def transfer(self, ctx, amount: int, recipient: discord.Member):
    """Always use type hints for command arguments"""
```

2. **Implement Cooldowns**

```python
@commands.cooldown(1, 60, commands.BucketType.user)
async def expensive_command(self, ctx):
    """Limit command usage"""
```

3. **Add Command Checks**

```python
@commands.has_permissions(ban_members=True)
@commands.bot_has_permissions(ban_members=True)
async def ban(self, ctx, member: discord.Member):
    """Ensure both user and bot have required permissions"""
```

### State Management

1. **Use Cog State**

```python
class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}  # Guild ID: VoiceState
```

2. **Cache Management**

```python
class CachingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._cache = {}
        self._last_update = None

    async def get_data(self, key):
        """Example of cached data retrieval with TTL"""
        if key in self._cache:
            if time.time() - self._last_update < 300:  # 5 minute TTL
                return self._cache[key]
        
        data = await self.fetch_fresh_data(key)
        self._cache[key] = data
        self._last_update = time.time()
        return data
```

### Performance Optimization

1. **Use Bulk Operations**

```python
# Instead of:
for message in messages:
    await message.delete()

# Use:
await ctx.channel.delete_messages(messages)
```

2. **Implement Pagination**

```python
@commands.command()
async def list_members(self, ctx):
    """Example of paginated output"""
    entries_per_page = 10
    entries = [member.name for member in ctx.guild.members]
    pages = [entries[i:i + entries_per_page] for i in range(0, len(entries), entries_per_page)]
    
    embeds = [
        discord.Embed(description='\n'.join(page))
        for page in pages
    ]
    
    view = PaginationView(embeds)
    await ctx.send(embed=embeds[0], view=view)
```

## Additional Resources

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Developer Portal](https://discord.com/developers/docs)
- [Discord.py GitHub](https://github.com/Rapptz/discord.py)
