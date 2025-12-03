"""
Message purging commands for bulk message deletion.

This module provides commands to delete multiple messages from Discord channels
in bulk, supporting various filtering options and safety measures.
"""

import datetime

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.core.checks import requires_command_permission


class Purge(BaseCog):
    """Discord cog for bulk message deletion commands."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the Purge cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    @app_commands.command(name="purge")
    @app_commands.guild_only()
    @requires_command_permission()
    async def slash_purge(
        self,
        interaction: discord.Interaction,
        limit: int,
        channel: discord.TextChannel
        | discord.Thread
        | discord.VoiceChannel
        | None = None,
    ) -> None:
        """
        Delete a set number of messages in a channel.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object for the command.
        limit : int
            The number of messages to delete.
        channel : discord.TextChannel | discord.Thread | discord.VoiceChannel | None
            The channel to delete messages from.
        """
        assert interaction.guild

        await interaction.response.defer(ephemeral=True)

        # Check if the limit is within the valid range
        if limit < 1 or limit > 500:
            await interaction.followup.send(
                "Invalid amount, maximum 500, minimum 1.",
                ephemeral=True,
            )
            return

        # If the channel is not specified, default to the current channel
        if channel is None:
            # Check if the current channel is a text channel
            if not isinstance(
                interaction.channel,
                discord.TextChannel | discord.Thread | discord.VoiceChannel,
            ):
                await interaction.followup.send(
                    "Invalid channel type, must be a text channel, thread, or voice channel.",
                    ephemeral=True,
                )
                return

            channel = interaction.channel

        # Calculate the cutoff date for Discord's 14-day bulk delete limit
        cutoff_date = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=14)

        # Purge the specified number of messages
        try:
            await interaction.followup.send("Purging messages...", ephemeral=True)

            # Get the most recent messages first to ensure they're properly captured
            logger.debug(f"Attempting to purge {limit} messages from {channel}")

            # Attempt to purge messages - only delete messages that existed BEFORE the interaction
            deleted = await channel.purge(
                limit=limit,
                before=interaction.created_at,  # Only messages before the interaction was created
                after=cutoff_date,  # Only messages from last 14 days
                bulk=True,  # Use bulk delete when possible
                oldest_first=False,  # Get most recent messages first
            )

            logger.debug(f"Purged {len(deleted)} messages out of requested {limit}")

            if len(deleted) < limit:
                await interaction.edit_original_response(
                    content=f"Purged {len(deleted)} messages in {channel.mention}. "
                    f"Note: Discord only allows bulk deletion of messages less than 14 days old.",
                )

            else:
                await interaction.edit_original_response(
                    content=f"Purged {len(deleted)} messages in {channel.mention}.",
                )

        except discord.Forbidden:
            await interaction.edit_original_response(
                content="I don't have permission to delete messages in that channel.",
            )

        except discord.HTTPException as error:
            await interaction.edit_original_response(
                content=f"An error occurred while purging messages: {error}",
            )

        except Exception as error:
            logger.error(f"Unexpected error in purge command: {error}")
            await interaction.edit_original_response(
                content="An unexpected error occurred while purging messages.",
            )

    @commands.command(
        name="purge",
        aliases=["p"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def prefix_purge(
        self,
        ctx: commands.Context[Tux],
        limit: int,
        channel: discord.TextChannel
        | discord.Thread
        | discord.VoiceChannel
        | None = None,
    ) -> None:
        """
        Delete a set number of messages in a channel.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        limit : int
            The number of messages to delete.
        channel : discord.TextChannel | discord.Thread | discord.VoiceChannel | None
            The channel to delete messages from.
        """
        assert ctx.guild

        # Check if the limit is within the valid range
        if limit < 1 or limit > 500:
            await ctx.send("Invalid amount, maximum 500, minimum 1.", ephemeral=True)
            return

        # If the channel is not specified, default to the current channel
        if channel is None:
            # Check if the current channel is a text channel
            if not isinstance(
                ctx.channel,
                discord.TextChannel | discord.Thread | discord.VoiceChannel,
            ):
                await ctx.send(
                    "Invalid channel type, must be a text channel, thread, or voice channel.",
                    ephemeral=True,
                )
                return

            channel = ctx.channel

        # Calculate the cutoff date for Discord's 14-day bulk delete limit
        cutoff_date = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=14)

        # Purge the specified number of messages
        try:
            # Include the command message itself in the deletion count
            cmd_msg = ctx.message
            await cmd_msg.delete()

            # Then delete the requested number of messages
            deleted = await channel.purge(
                limit=limit,
                before=None,  # Include most recent messages
                after=cutoff_date,  # Only messages from last 14 days
                bulk=True,  # Use bulk delete when possible
                oldest_first=False,  # Get most recent messages first
            )

            # Send a confirmation message
            if len(deleted) < limit:
                await ctx.send(
                    f"Purged {len(deleted)} messages from {channel.mention}. "
                    f"Note: Discord only allows bulk deletion of messages less than 14 days old.",
                    ephemeral=True,
                )

            else:
                await ctx.send(
                    f"Purged {len(deleted)} messages from {channel.mention}.",
                    ephemeral=True,
                )

        except discord.Forbidden:
            await ctx.send(
                "I don't have permission to delete messages in that channel.",
                ephemeral=True,
            )
            return

        except discord.HTTPException as error:
            logger.error(f"An error occurred while purging messages: {error}")
            await ctx.send(
                f"An error occurred while purging messages: {error}",
                ephemeral=True,
            )
            return

        except Exception as error:
            logger.error(f"Unexpected error in purge command: {error}")
            await ctx.send(
                "An unexpected error occurred while purging messages.",
                ephemeral=True,
            )
            return


async def setup(bot: Tux) -> None:
    """Set up the Purge cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Purge(bot))
