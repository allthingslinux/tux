# UI Components Walkthrough

Learn how to create interactive UI components in Tux.

## Prerequisites

Before starting this tutorial, make sure you have:

- Completed the [Development Setup](development-setup.md) tutorial
- Created your first command using the [Creating Your First Command](creating-first-command.md) tutorial

## Step 1: Understanding UI Components

Tux uses Discord.py's UI components for interactive elements:

- **Buttons** - Clickable buttons
- **Select Menus** - Dropdown selections
- **Modals** - Form inputs
- **Views** - Container for components

## Step 2: Creating a Simple Button

Here's a basic button example:

```python
from discord.ext import commands
from discord.ui import Button, View
from tux.core import BaseCog

class MyCog(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
    
    @commands.command(name="button-test")
    async def button_test(self, ctx):
        """Test a simple button."""
        button = Button(label="Click me!", style=discord.ButtonStyle.primary)
        
        async def button_callback(interaction):
            await interaction.response.send_message("Button clicked!", ephemeral=True)
        
        button.callback = button_callback
        
        view = View()
        view.add_item(button)
        
        await ctx.send("Click the button below:", view=view)
```

## Step 3: Creating a Select Menu

Here's a select menu example:

```python
from discord.ui import Select, View

@commands.command(name="select-test")
async def select_test(self, ctx):
    """Test a select menu."""
    select = Select(
        placeholder="Choose an option...",
        options=[
            discord.SelectOption(label="Option 1", value="1"),
            discord.SelectOption(label="Option 2", value="2"),
            discord.SelectOption(label="Option 3", value="3"),
        ]
    )
    
    async def select_callback(interaction):
        await interaction.response.send_message(f"You selected: {interaction.data['values'][0]}")
    
    select.callback = select_callback
    
    view = View()
    view.add_item(select)
    
    await ctx.send("Choose an option:", view=view)
```

## Step 4: Using Tux's UI Components

Tux provides pre-built UI components:

```python
from tux.ui.embeds import TuxEmbed
from tux.ui.views import ConfirmationView

@commands.command(name="confirm-test")
async def confirm_test(self, ctx):
    """Test Tux's confirmation view."""
    embed = TuxEmbed(title="Confirm Action", description="Are you sure?")
    view = ConfirmationView()
    
    await ctx.send(embed=embed, view=view)
```

## Next Steps

After completing this tutorial:

- Learn about [Database Integration](database-integration.md)
- Explore the [UI Components Guide](../guides/ui-components.md) for advanced patterns
- Check out [Testing Setup](testing-setup.md) to test your components
