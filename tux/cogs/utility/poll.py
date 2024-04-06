import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class Poll(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="poll", description="Creates a poll.")
    @app_commands.describe(title="Title of the poll", options="Poll options, comma separated")
    # allows up to 10 options
    async def poll(self, interaction: discord.Interaction, title: str, options: str) -> None:
        # split the options by comma, and validate that there are at least 2 options and at most 10
        options_list = options.split(",")

        if len(options_list) < 2 or len(options_list) > 9:
            embed = discord.Embed(
                title="Error",
                description=f"Poll options count needs to be between 2-9, you provided {len(options_list)} options.",
                color=discord.Colour.red(),
            )

            embed.timestamp = interaction.created_at

            embed.set_footer(
                text=f"Requested by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url,
            )

            await interaction.response.send_message(embed=embed)

            return

        description = "\n".join(
            [f"{num + 1}\u20e3 {option}" for num, option in enumerate(options_list)]
        )

        # create the embed
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Colour.green(),
        )

        embed.timestamp = interaction.created_at

        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )

        logger.info(f"{interaction.user} used the ping command in {interaction.channel}.")

        # send the embed
        await interaction.response.send_message(embed=embed)

        # add reactions to the message
        # we can use  await interaction.original_response() to get the message object
        message = await interaction.original_response()
        for num in range(len(options_list)):
            await message.add_reaction(f"{num + 1}\u20e3")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Poll(bot))
