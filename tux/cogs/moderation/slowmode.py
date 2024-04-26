import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.utils.embeds import EmbedCreator


class Slowmode(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.checks.has_any_role("Root", "Admin", "Sr. Mod", "Mod", "Jr. Mod")
    @app_commands.command(name="slowmode", description="Sets slowmode for the current channel.")
    @app_commands.describe(delay="The slowmode time in seconds, max is 21600, default is 5")
    async def set_slowmode(
        self,
        interaction: discord.Interaction,
        delay: int = 5,
        channel: discord.TextChannel | discord.ForumChannel | discord.Thread | None = None,
    ) -> None:
        # Get the target channel (default to the current channel if not provided)
        target_channel = channel or interaction.channel

        # Check if the channel is a thread and get the parent channel
        if isinstance(target_channel, discord.Thread):
            target_channel = target_channel.parent

        # Check if the channel is valid (TextChannel or ForumChannel)
        if not isinstance(target_channel, discord.TextChannel | discord.ForumChannel):
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="Failed to set slowmode. Please provide a valid channel.",
                interaction=interaction,
            )
            await interaction.response.send_message(embed=embed)
            logger.error(f"Failed to set slowmode. Invalid channel: {channel}")

        # Check if the delay is within the valid range
        if delay < 0 or delay > 21600:
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="The slowmode delay must be between 0 and 21600 seconds.",
                interaction=interaction,
            )
            await interaction.response.send_message(embed=embed)
            logger.error(f"Failed to set slowmode. Invalid delay: {delay}")

        try:
            # If the target channel is a valid channel, set the slowmode
            if isinstance(target_channel, discord.TextChannel | discord.ForumChannel):
                await target_channel.edit(slowmode_delay=delay)
                embed = EmbedCreator.create_info_embed(
                    title="Slowmode Set",
                    description=f"Slowmode set to {delay} seconds in {target_channel.mention}.",
                    interaction=interaction,
                )
                await interaction.response.send_message(embed=embed)
                logger.info(f"Slowmode set to {delay} seconds in {target_channel.mention}.")

            else:
                embed = EmbedCreator.create_error_embed(
                    title="Error",
                    description="Failed to set slowmode. Please provide a valid channel.",
                    interaction=interaction,
                )
                await interaction.response.send_message(embed=embed)
                logger.error(f"Failed to set slowmode. Invalid channel: {channel}")

        except Exception as error:
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description=f"Failed to set slowmode. Error: {error}",
                interaction=interaction,
            )

            await interaction.response.send_message(embed=embed)
            logger.error(f"Failed to set slowmode. Error: {error}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Slowmode(bot))
