"""
Interactive polling system for Discord.

This module provides functionality for creating and managing polls with
reaction-based voting, poll banning checks, and result tracking.
"""

import discord
from discord import app_commands
from discord.ext import commands

from tux.core.bot import Tux
from tux.core.converters import get_channel_safe
from tux.modules.moderation import ModerationCogBase
from tux.ui.embeds import EmbedCreator

# TODO: Create option inputs for the poll command instead of using a comma separated string


class Poll(ModerationCogBase):
    """Discord cog for interactive polling functionality."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the Poll cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

        # Uses ModerationCogBase.is_pollbanned

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self,
        payload: discord.RawReactionActionEvent,
    ) -> None:
        """On raw reaction add event handler."""
        # get reaction from payload.message_id, payload.channel_id, payload.guild_id, payload.emoji
        channel = await get_channel_safe(self.bot, payload.channel_id)
        if channel is None:
            return

        message: discord.Message = await channel.fetch_message(payload.message_id)
        # Lookup the reaction object for this event
        if payload.emoji.id:
            # Custom emoji: match by ID
            reaction = next(
                (
                    r
                    for r in message.reactions
                    if getattr(r.emoji, "id", None) == payload.emoji.id
                ),
                None,
            )
        else:
            # Unicode emoji: try multiple matching strategies
            reaction = discord.utils.get(message.reactions, emoji=str(payload.emoji))
            if reaction is None and hasattr(payload.emoji, "name"):
                # Fallback: try matching by emoji name if available
                reaction = discord.utils.get(
                    message.reactions,
                    emoji=payload.emoji.name,
                )
        if reaction is None:
            # Don't log as error for non-poll reactions, just silently ignore
            return

        # Block any reactions that are not numbers for the poll
        if reaction.message.embeds:
            embed = reaction.message.embeds[0]
            if (
                embed.author.name
                and embed.author.name.startswith("Poll")
                and str(reaction.emoji) not in [f"{num + 1}\u20e3" for num in range(9)]
            ):
                await reaction.clear()

    @app_commands.command(name="poll", description="Creates a poll.")
    @app_commands.describe(
        title="Title of the poll",
        options="Poll options, comma separated",
    )
    async def poll(
        self,
        interaction: discord.Interaction,
        title: str,
        options: str,
    ) -> None:
        """
        Create a poll with a title and options.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        title : str
            The title of the poll.
        options : str
            The options for the poll, separated by commas.


        """
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        # Split the options by comma
        options_list = options.split(",")

        # Remove any leading or trailing whitespaces from the options
        options_list = [option.strip() for option in options_list]

        # Check if the options count is between 2-9
        if len(options_list) < 2 or len(options_list) > 9:
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                user_name=interaction.user.name,
                user_display_avatar=interaction.user.display_avatar.url,
                title="Invalid options count",
                description=f"Poll options count needs to be between 2-9, you provided {len(options_list)} options.",
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Create the description for the poll embed
        description = "\n".join(
            [f"{num + 1}\u20e3 {option}" for num, option in enumerate(options_list)],
        )

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.POLL,
            user_name=interaction.user.name,
            user_display_avatar=interaction.user.display_avatar.url,
            title=title,
            description=description,
        )

        await interaction.response.send_message(embed=embed)

        # We can use  await interaction.original_response() to get the message object
        message = await interaction.original_response()

        for num, _ in enumerate(options_list, start=1):
            # Add the number emoji reaction to the message
            await message.add_reaction(f"{num}\u20e3")


async def setup(bot: Tux) -> None:
    """Cog setup for poll cog.

    Parameters
    ----------
    bot : Tux
        The bot instance.
    """
    await bot.add_cog(Poll(bot))
