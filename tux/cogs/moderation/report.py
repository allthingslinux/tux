import discord
from discord import app_commands
from discord.ext import commands

from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator


class ReportModal(discord.ui.Modal):
    def __init__(self, *, title: str = "Submit an anonymous report", bot: commands.Bot) -> None:
        super().__init__(title=title)
        self.bot = bot
        self.channel = CONST.LOG_CHANNELS["REPORTS"]

    short = discord.ui.TextInput(  # type: ignore
        style=discord.TextStyle.short,
        label="Related user(s) or issue(s)",
        required=True,
        max_length=100,
        placeholder="User IDs, usernames, or brief description",
    )

    long = discord.ui.TextInput(  # type: ignore
        style=discord.TextStyle.long,
        label="Your report",
        required=True,
        max_length=4000,
        placeholder="Please provide as much detail as possible",
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """
        Sends the report to the moderation team.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        """

        embed = EmbedCreator.create_log_embed(
            title=(f"Anonymous report for {self.short.value}"),  # type: ignore
            description=self.long.value,  # type: ignore
            interaction=None,
        )

        # Get the channel to send the report to
        channel = self.bot.get_channel(self.channel) or await self.bot.fetch_channel(self.channel)

        # Create a webhook in the channel to send the report
        webhook: discord.Webhook | None = None

        # Check if the channel is a text channel
        if isinstance(channel, discord.TextChannel):
            webhook = await channel.create_webhook(
                name="Tux",
                reason="Anonymous report webhook",
            )

        if webhook:
            # Send the report to the webhook
            await webhook.send(embed=embed)
            # Delete the webhook after sending the report
            await webhook.delete(reason="Report sent")

        # Send a confirmation message to the user
        await interaction.response.send_message(
            "The report has been sent to the moderation team. Thank you for your help!",
            ephemeral=True,
        )


class Report(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="report", description="Report a user or issue anonymously")
    async def report(self, interaction: discord.Interaction) -> None:
        """
        Opens the report modal for users to submit an anonymous report.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        """

        modal = ReportModal(bot=self.bot)
        await interaction.response.send_modal(modal)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Report(bot))
