import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.bot import Tux
from tux.utils import checks


class Purge(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot

    @app_commands.command(name="purge")
    @app_commands.guild_only()
    @checks.ac_has_pl(2)
    async def slash_purge(
        self,
        interaction: discord.Interaction,
        limit: int,
        channel: discord.TextChannel | discord.Thread | None = None,
    ) -> None:
        """
        Deletes a set number of messages in a channel.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object for the command.
        limit : int
            The number of messages to delete.
        channel : discord.TextChannel | discord.Thread | None
            The channel to delete messages from.

        Raises
        ------
        discord.Forbidden
            If the bot is unable to delete messages.
        discord.HTTPException
            If an error occurs while deleting messages.
        """

        assert interaction.guild

        # Check if the limit is within the valid range
        if limit < 1 or limit > 500:
            await interaction.response.defer(ephemeral=True)
            return await interaction.followup.send(
                "Invalid amount, maximum 500, minimum 1.",
                ephemeral=True,
            )

        # If the channel is not specified, default to the current channel
        if channel is None:
            # Check if the current channel is a text channel
            if not isinstance(interaction.channel, discord.TextChannel | discord.Thread):
                await interaction.response.defer(ephemeral=True)
                return await interaction.followup.send(
                    "Invalid channel type, must be a text channel.",
                    ephemeral=True,
                )
            channel = interaction.channel

        # Purge the specified number of messages
        try:
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(content="Purging messages...")
            await channel.purge(limit=limit)
            await interaction.edit_original_response(content=f"Purged {limit} messages in {channel.mention}.")
        except Exception as error:
            await interaction.edit_original_response(content=f"An error occurred while purging messages: {error}")

    @commands.command(
        name="purge",
        aliases=["p"],
        usage="purge [limit] <channel>",
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def prefix_purge(
        self,
        ctx: commands.Context[Tux],
        limit: int,
        channel: discord.TextChannel | discord.Thread | None = None,
    ) -> None:
        """
        Deletes a set number of messages in a channel.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        limit : int
            The number of messages to delete.
        channel : discord.TextChannel | discord.Thread | None
            The channel to delete messages from.

        Raises
        ------
        discord.Forbidden
            If the bot is unable to delete messages.
        discord.HTTPException
            If an error occurs while deleting messages.
        """

        assert ctx.guild

        # Check if the limit is within the valid range
        if limit < 1 or limit > 500:
            await ctx.send("Invalid amount, maximum 500, minimum 1.", delete_after=30, ephemeral=True)
            return

        # If the channel is not specified, default to the current channe
        if channel is None:
            # Check if the current channel is a text channel
            if not isinstance(ctx.channel, discord.TextChannel | discord.Thread):
                await ctx.send("Invalid channel type, must be a text channel.", delete_after=30, ephemeral=True)
                return

            channel = ctx.channel

        # Purge the specified number of messages
        try:
            await channel.purge(limit=limit + 1)

        except Exception as error:
            logger.error(f"An error occurred while purging messages: {error}")
            await ctx.send(f"An error occurred while purging messages: {error}", delete_after=30, ephemeral=True)
            return

        # Send a confirmation message
        await ctx.send(f"Purged {limit} messages from {channel.mention}.", delete_after=30, ephemeral=True)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Purge(bot))
