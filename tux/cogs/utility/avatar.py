import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class Avatar(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="avatar", description="Get the avatar of a member.")
    @app_commands.describe(member="The member to get the avatar of.")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member) -> None:
        logger.info(f"{interaction.user} used the avatar command in {interaction.channel}.")

        await interaction.response.send_message(
            member.avatar.url if member.avatar else "Member has no avatar."
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Avatar(bot))
