# commands/ban.py

import discord
from discord.ext import commands

from tux.command_cog import CommandCog
from tux.main import TuxBot
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Ban(CommandCog):
    @commands.hybrid_command(
        name="ban",
        description="Bans a user from the server.",
        usage="ban <user> [reason]",
    )
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided.",
    ) -> None:
        """
        Bans a user from the server.

        Args:
            ctx (commands.Context): The invocation context sent by the Discord API which contains information
            about the command and from where it was called.
            member (discord.Member): The member to ban.
            reason (str): The reason for the ban.
        """

        await member.ban(reason=reason)
        await ctx.send(f"Banned {member} for {reason}.")
        logger.info(f"{ctx.author} banned {member} for {reason}.")


async def setup(bot: TuxBot) -> None:
    await bot.add_cog(Ban(bot))
