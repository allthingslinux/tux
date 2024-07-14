import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class Purge(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="purge")
    @app_commands.guild_only()
    async def slash_purge(
        self,
        interaction: discord.Interaction,
        limit: int,
        channel: discord.TextChannel | None = None,
    ) -> None:
        """
        Deletes a set number of messages in a channel.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object for the command.
        limit : int
            The number of messages to delete.
        channel : discord.TextChannel | None
            The channel to delete messages from.

        Raises
        ------
        discord.Forbidden
            If the bot is unable to delete messages.
        discord.HTTPException
            If an error occurs while deleting messages.
        """

        if interaction.guild is None:
            return logger.warning("Purge command used outside of a guild context.")

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
            if not isinstance(interaction.channel, discord.TextChannel):
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
        usage="$[purge|p] <limit> <channel>",
    )
    @commands.guild_only()
    async def prefix_purge(
        self,
        ctx: commands.Context[commands.Bot],
        limit: int,
        channel: discord.TextChannel | None = None,
    ) -> None:
        """
        Purge a specified number of messages from a channel.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        limit : int
            The number of messages to delete.
        channel : discord.TextChannel | None
            The channel to delete messages from.

        Raises
        ------
        discord.Forbidden
            If the bot is unable to delete messages.
        discord.HTTPException
            If an error occurs while deleting messages.
        """

        if ctx.guild is None:
            logger.warning("Purge command used outside of a guild context.")
            return

        # Check if the limit is within the valid range
        if limit < 1 or limit > 500:
            await ctx.reply("Invalid amount, maximum 500, minimum 1.", delete_after=10, ephemeral=True)
            return

        # If the channel is not specified, default to the current channe
        if channel is None:
            # Check if the current channel is a text channel
            if not isinstance(ctx.channel, discord.TextChannel):
                await ctx.reply("Invalid channel type, must be a text channel.", delete_after=10, ephemeral=True)
                return
            channel = ctx.channel

        # Purge the specified number of messages
        await channel.purge(limit=limit)

        # Send a confirmation message
        await ctx.send(f"Purged {limit} messages from {channel.mention}.", delete_after=10, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Purge(bot))
