import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.bot import Tux
from tux.database.controllers import DatabaseController
from tux.ui.embeds import EmbedCreator

# TODO: Create option inputs for the poll command instead of using a comma separated string


class Poll(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()

    # TODO: for the moment this is duplicated code from ModerationCogBase in a attempt to get the code out sooner
    async def is_pollbanned(self, guild_id: int, user_id: int) -> bool:
        """
        Check if a user is poll banned.

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

        ban_cases = await self.db.case.find_many(where={"case_type": CaseType.POLLBAN})
        unban_cases = await self.db.case.find_many(where={"case_type": CaseType.POLLUNBAN})

        ban_count = sum(case.case_user_id == user_id for case in ban_cases)
        unban_count = sum(case.case_user_id == user_id for case in unban_cases)

        return (
            ban_count > unban_count
        )  # TODO: this implementation is flawed, if someone bans and unbans the same user multiple times, this will not work as expected

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
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User) -> None:
        # Block any reactions that are not numbers for the poll
        if reaction.message.embeds:
            embed = reaction.message.embeds[0]
            if (
                embed.author.name
                and embed.author.name.startswith("Poll")
                and reaction.emoji not in [f"{num + 1}\u20e3" for num in range(9)]
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
