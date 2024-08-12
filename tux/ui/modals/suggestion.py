import discord
from discord.ext import commands
from loguru import logger

from tux.database.controllers import DatabaseController
from tux.utils.embeds import EmbedCreator


class SuggestionModal(discord.ui.Modal):
    def __init__(self, *, title: str = "Submit a suggestion", bot: commands.Bot) -> None:
        super().__init__(title=title)
        self.bot = bot
        self.config = DatabaseController().guild_config

    short = discord.ui.TextInput(  # type: ignore
        label="Suggestion Summary",
        style=discord.TextStyle.short,
        required=True,
        max_length=100,
        placeholder="Add an AI chatbot to Tux",
    )

    long = discord.ui.TextInput(  # type: ignore
        style=discord.TextStyle.long,
        label="The suggestion",
        required=True,
        max_length=4000,
        placeholder="Please provide as much detail as possible",
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """
        Sends the suggestion to dedicated channel.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        """

        if not interaction.guild:
            logger.error("Guild is None")
            return

        embed = EmbedCreator.create_log_embed(
            title=(f"Suggestion for {self.short.value}"),  # type: ignore
            description=self.long.value,  # type: ignore
            interaction=None,
        )

        try:
            suggestion_log_channel_id = await self.config.get_suggestion_log_channel(interaction.guild.id)
        except Exception as e:
            logger.error(f"Failed to get suggestion log channel for guild {interaction.guild.id}. {e}")
            await interaction.response.send_message(
                "Failed to submit your suggestion. Please try again later.",
                ephemeral=True,
                delete_after=30,
            )
            return

        if not suggestion_log_channel_id:
            logger.error(f"Suggestion log channel not set for guild {interaction.guild.id}")
            await interaction.response.send_message(
                "The suggestion log channel has not been set up. Please contact an administrator.",
                ephemeral=True,
                delete_after=30,
            )
            return

        # Get the suggestion log channel object
        suggestion_log_channel = interaction.guild.get_channel(suggestion_log_channel_id)
        if not suggestion_log_channel or not isinstance(suggestion_log_channel, discord.TextChannel):
            logger.error(f"Failed to get suggestion log channel for guild {interaction.guild.id}")
            await interaction.response.send_message(
                "Failed to submit your suggestion. Please try again later.",
                ephemeral=True,
                delete_after=30,
            )
            return

        # Send confirmation message to user
        await interaction.response.send_message(
            "Your suggestion has been submitted.",
            ephemeral=True,
            delete_after=30,
        )

        await suggestion_log_channel.send(embed=embed)
