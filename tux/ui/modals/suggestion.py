import discord
from discord.ext import commands
from loguru import logger

from tux.database.controllers import DatabaseController
from tux.utils import checks
from tux.utils.constants import Constants as CONST
from tux.utils.embeds import create_embed_footer


class ButtonView(discord.ui.View):
    def __init__(self, embed: discord.Embed):
        super().__init__()
        self.embed = embed

    @discord.ui.button(label="Accept Suggestion", style=discord.ButtonStyle.green)
    @checks.has_pl(5)
    async def green_button(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        self.embed.set_author(name="Suggestion Status: Accepted")
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="Deny Suggestion", style=discord.ButtonStyle.red)
    @checks.has_pl(5)
    async def red_button(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        self.embed.set_author(name="Suggestion Status: Rejected")
        await interaction.response.edit_message(embed=self.embed, view=self)


class SuggestionModal(discord.ui.Modal):
    def __init__(self, *, title: str = "Submit a suggestion", bot: commands.Bot) -> None:
        super().__init__(title=title)
        self.bot = bot
        self.config = DatabaseController().guild_config

    suggestion_title = discord.ui.TextInput(  # type: ignore
        label="Suggestion Summary",
        style=discord.TextStyle.short,
        required=True,
        max_length=100,
        placeholder="Summarise your suggestion briefly",
    )

    suggestion_description = discord.ui.TextInput(  # type: ignore
        style=discord.TextStyle.long,
        label="Suggestion Description",
        required=True,
        max_length=4000,
        placeholder="Please provide as much detail as possible on your suggestion",
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

        embed = discord.Embed(
            title=self.suggestion_title.value,  # type: ignore
            description=self.suggestion_description.value,  # type: ignore
            color=CONST.EMBED_COLORS["DEFAULT"],
        )
        embed.set_author(name="Suggestion Status: Under Review")
        embed.add_field(
            name="Review Info",
            value="No review has been submitted",
            inline=False,
        )
        footer_text, footer_icon_url = create_embed_footer(interaction=interaction)
        embed.set_footer(text=footer_text, icon_url=footer_icon_url)

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
                "The suggestion channel has not been set up. Please contact an administrator.",
                ephemeral=True,
                delete_after=30,
            )
            return

        suggestion_log_channel = interaction.guild.get_channel(suggestion_log_channel_id)
        if not suggestion_log_channel or not isinstance(suggestion_log_channel, discord.TextChannel):
            logger.error(f"Failed to get suggestion log channel for guild {interaction.guild.id}")
            await interaction.response.send_message(
                "Failed to submit your suggestion. Please try again later.",
                ephemeral=True,
                delete_after=30,
            )
            return

        await interaction.response.send_message(
            "Your suggestion has been submitted.",
            ephemeral=True,
            delete_after=30,
        )

        view = ButtonView(embed=embed)
        message = await suggestion_log_channel.send(embed=embed, view=view)

        await suggestion_log_channel.create_thread(
            name=f"Suggestion: {self.suggestion_title.value}",  # type: ignore
            message=message,
            auto_archive_duration=1440,
        )

        reactions = ["👍", "👎"]
        for reaction in reactions:
            await message.add_reaction(reaction)
