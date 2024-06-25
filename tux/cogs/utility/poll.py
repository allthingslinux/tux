import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.utils.embeds import EmbedCreator

# TODO: Create option inputs for the poll command instead of using a comma separated string


class Poll(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

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

        # Split the options by comma
        options_list = options.split(",")

        # Remove any leading or trailing whitespaces from the options
        options_list = [option.strip() for option in options_list]

        # Check if the options count is between 2-9
        if len(options_list) < 2 or len(options_list) > 9:
            embed = EmbedCreator.create_error_embed(
                title="Invalid options count",
                description=f"Poll options count needs to be between 2-9, you provided {len(options_list)} options.",
                interaction=interaction,
            )

            await interaction.response.send_message(embed=embed)
            return

        # Create the description for the poll embed
        description = "\n".join([f"{num + 1}\u20e3 {option}" for num, option in enumerate(options_list)])

        embed = EmbedCreator.create_poll_embed(
            title=title,
            description=description,
            interaction=interaction,
        )

        await interaction.response.send_message(embed=embed)

        # We can use  await interaction.original_response() to get the message object
        message = await interaction.original_response()
        for num in range(len(options_list)):
            # Add the number emoji reaction to the message
            await message.add_reaction(f"{num + 1}\u20e3")

        logger.info(f"{interaction.user} used the ping command in {interaction.channel}.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Poll(bot))
