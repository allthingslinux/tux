import json
import os
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.utils.constants import Constants

config_file = Path("config/settings.json")
config = json.loads(config_file.read_text())

# Access role IDs from the JSON data
admin_role_id = Constants.USER_IDS["ADMIN"]
owner_role_id = Constants.USER_IDS["OWNER"]
mod_role_id = Constants.USER_IDS["MOD"]
jr_mod_role_id = Constants.USER_IDS["JR MOD"]
testing_role_id = Constants.USER_IDS["TESTING"] if os.getenv("STAGING") == "True" else "foobar"


class Purge(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def send_embed(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        color: discord.Colour,
        error_info: str | None = None,
    ) -> None:
        embed = discord.Embed(
            title=title, description=description, color=color, timestamp=interaction.created_at
        )
        if error_info:
            embed.add_field(name="Error Details", value=f"`{error_info}`", inline=False)
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )
        await interaction.followup.send(embed=embed)  # Send the embed to the interaction

    @app_commands.checks.has_any_role(
        admin_role_id,
        owner_role_id,
        mod_role_id,
        jr_mod_role_id,
        *testing_role_id,
    )
    @app_commands.command(
        name="purge", description="Deletes a set number of messages in a channel."
    )
    @app_commands.describe(number_messages="The number of messages to be purged.")
    async def purge_messages(
        self, interaction: discord.Interaction, number_messages: int = 10
    ) -> None:
        if not interaction.channel or interaction.channel.type != discord.ChannelType.text:
            return None
        if number_messages <= 0:
            await interaction.response.defer(ephemeral=True)
            return await self.send_embed(
                interaction,
                "Error",
                "The number of messages to purge must be greater than 0.",
                discord.Colour.red(),
            )
        embed = discord.Embed
        try:
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(content="Purging messages...")
            deleted = await interaction.channel.purge(limit=number_messages)
            description = f"Deleted {len(deleted)} messages in {interaction.channel.mention}"
            await self.send_embed(interaction, "Success!", description, discord.Colour.blue())
            logger.info(
                f"{interaction.user} purged {len(deleted)} messages from {interaction.channel.name}"
            )
        except discord.Forbidden as e:
            logger.error(f"Failed to purge messages in {interaction.channel.name}: {e}")
            await self.send_embed(
                interaction,
                "Permission Denied",
                "Failed to purge messages due to insufficient permissions.",
                discord.Colour.red(),
                error_info=str(e),
            )
            embed.timestamp = interaction.created_at  # Add timestamp to the error embed
        except discord.HTTPException as e:
            logger.error(f"Failed to purge messages in {interaction.channel.name}: {e}")
            await self.send_embed(
                interaction,
                "Error",
                f"An error occurred while purging messages: {e}",
                discord.Colour.red(),
            )


# ... you can add other methods here ...


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Purge(bot))
