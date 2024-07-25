import discord
from discord.ext import commands
from loguru import logger

from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator


class CommandEventsCog(commands.Cog, name="Command Events Handler"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.dev_log_channel_id: int = CONST.LOG_CHANNELS["DEV"]

    # @commands.Cog.listener()
    # async def on_app_command_completion(
    #     self,
    #     interaction: discord.Interaction,
    #     command: discord.app_commands.AppCommand,
    # ) -> None:
    #     logger.info(f"Command {command.name} completed by {interaction.user}")

    #     dev_log_channel = self.bot.get_channel(self.dev_log_channel_id)

    #     if isinstance(dev_log_channel, discord.TextChannel):
    #         embed = EmbedCreator.create_log_embed(
    #             title="Command Completed",
    #             description=f"Command `{command.name}` completed by {interaction.user.mention}.",
    #         )

    #         await dev_log_channel.send(embed=embed)

    # @commands.Cog.listener()
    # async def on_command_completion(self, ctx: commands.Context[commands.Bot]) -> None:
    #     if ctx.command is not None:
    #         logger.info(f"Command {ctx.command.name} completed by {ctx.author}")

    #         dev_log_channel = self.bot.get_channel(self.dev_log_channel_id)

    #         if isinstance(dev_log_channel, discord.TextChannel):
    #             embed = EmbedCreator.create_log_embed(
    #                 title="Command Completed",
    #                 description=f"Command `{ctx.command.name}` completed by {ctx.author.mention}.",
    #             )

    #             await dev_log_channel.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CommandEventsCog(bot))
