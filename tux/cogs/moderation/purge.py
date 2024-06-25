import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.utils.embeds import EmbedCreator


class Purge(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.checks.has_any_role("Root", "Admin", "Sr. Mod", "Mod")
    @app_commands.command(name="purge", description="Deletes a set number of messages in a channel.")
    @app_commands.describe(number_messages="The number of messages to be purged.")
    async def purge_messages(self, interaction: discord.Interaction, number_messages: int = 10) -> None:
        """
        Deletes a set number of messages in a channel.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        number_messages : int, optional
            The number of messages to be purged, by default 10.
        """

        if not interaction.channel or interaction.channel.type != discord.ChannelType.text:
            return await interaction.response.send_message(
                "This command can only be used in text channels.", ephemeral=True
            )

        if number_messages <= 0:
            await interaction.response.defer(ephemeral=True)
            embed = EmbedCreator.create_error_embed(
                title="Invalid Number",
                description="Please provide a number greater than 0.",
            )

            return await interaction.followup.send(embed=embed, ephemeral=True)

        try:
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(content="Purging messages...")

            deleted = await interaction.channel.purge(limit=number_messages)
            description = f"Deleted {len(deleted)} messages in {interaction.channel.mention}"

            embed = EmbedCreator.create_success_embed(
                title="Purge Successful",
                description=description,
                interaction=interaction,
            )

            logger.info(f"{interaction.user} purged {len(deleted)} messages from {interaction.channel.name}")

            await interaction.edit_original_response(embed=embed)

        except Exception as error:
            embed = EmbedCreator.create_error_embed(
                title="Purge Failed",
                description=f"Failed to purge messages in {interaction.channel.mention}.",
                interaction=interaction,
            )

            logger.error(f"Failed to purge messages in {interaction.channel.name}. Error: {error}")

            await interaction.edit_original_response(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Purge(bot))
