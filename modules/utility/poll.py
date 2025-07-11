import discord
from bot import Tux
from database.controllers import DatabaseController
from discord import app_commands
from discord.ext import commands
from loguru import logger
from ui.embeds import EmbedCreator
from utils.converters import get_channel_safe

from prisma.enums import CaseType

# TODO: Create option inputs for the poll command instead of using a comma separated string


class Poll(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()

    async def is_pollbanned(self, guild_id: int, user_id: int) -> bool:
        """
        Check if a user is currently poll banned.
        The user is considered poll banned if their latest relevant case (POLLBAN or POLLUNBAN) is a POLLBAN.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to check in.
        user_id : int
            The ID of the user to check.

        Returns
        -------
        bool
            True if the user is poll banned, False otherwise.
        """
        latest_case = await self.db.case.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
            case_types=[CaseType.POLLBAN, CaseType.POLLUNBAN],
        )

        # If no relevant cases exist, the user is not poll banned.
        return latest_case.case_type == CaseType.POLLBAN if latest_case else False

    @commands.Cog.listener()  # listen for messages
    async def on_message(self, message: discord.Message) -> None:
        poll_channel = self.bot.get_channel(1228717294788673656)

        if message.channel != poll_channel:
            return

        # check if the message is a poll from tux, we can check the author id
        if self.bot.user is None:
            logger.error("Something has seriously gone wrong, the bot user is None.")
            return

        if message.author.id == self.bot.user.id and message.embeds:
            await message.create_thread(name=f"Poll by {message.author.name}")
            return

        # check if the message is a discord poll
        if message.poll:
            await message.create_thread(name=f"Poll by {message.author.name}")
            return

        # delete the message
        await message.delete()

        # Ensure command processing continues for other messages
        await self.bot.process_commands(message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        # get reaction from payload.message_id, payload.channel_id, payload.guild_id, payload.emoji
        channel = await get_channel_safe(self.bot, payload.channel_id)
        if channel is None:
            return

        message = await channel.fetch_message(payload.message_id)
        # Lookup the reaction object for this event
        if payload.emoji.id:
            # Custom emoji: match by ID
            reaction = next(
                (r for r in message.reactions if getattr(r.emoji, "id", None) == payload.emoji.id),
                None,
            )
        else:
            # Unicode emoji: match by full emoji string
            reaction = discord.utils.get(message.reactions, emoji=str(payload.emoji))
        if reaction is None:
            logger.error(f"Reaction with emoji {payload.emoji} not found.")
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
    @app_commands.describe(title="Title of the poll", options="Poll options, comma separated")
    async def poll(self, interaction: discord.Interaction, title: str, options: str) -> None:
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
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        # Split the options by comma
        options_list = options.split(",")

        # Remove any leading or trailing whitespaces from the options
        options_list = [option.strip() for option in options_list]

        if await self.is_pollbanned(interaction.guild_id, interaction.user.id):
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                user_name=interaction.user.name,
                user_display_avatar=interaction.user.display_avatar.url,
                title="Poll Banned",
                description="You are poll banned and cannot create a poll.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
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

            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=30)
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

        for num in range(len(options_list)):
            # Add the number emoji reaction to the message
            await message.add_reaction(f"{num + 1}\u20e3")


async def setup(bot: Tux) -> None:
    await bot.add_cog(Poll(bot))
