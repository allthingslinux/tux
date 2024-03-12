# commands/kick.py

import discord
from discord.ext import commands

from tux.command_cog import CommandCog
from tux.main import TuxBot
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Kick(CommandCog):
    @commands.hybrid_command(
        name="kick",
        description="Kicks a user from the server.",
        usage="kick <user> [reason]",
    )
    async def kick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided.",
    ) -> None:
        """
        Kicks a user from the server.

        Args:
            ctx (commands.Context): The invocation context sent by the Discord API which contains information
            about the command and from where it was called.
            member (discord.Member): The member to kick.
            reason (str): The reason for the kick.
        """

        await member.kick(reason=reason)
        await ctx.send(f"Kicked {member} for {reason}.")
        logger.info(f"{ctx.author} kicked {member} for {reason}.")


async def setup(bot: TuxBot) -> None:
    await bot.add_cog(Kick(bot))
