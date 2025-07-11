import discord
from bot import Tux
from discord.ext import commands
from utils import checks
from utils.flags import BanFlags
from utils.functions import generate_usage

from prisma.enums import CaseType

from . import ModerationCogBase


class Ban(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.ban.usage = generate_usage(self.ban, BanFlags)

    @commands.hybrid_command(name="ban", aliases=["b"])
    @commands.guild_only()
    @checks.has_pl(3)
    async def ban(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: BanFlags,
    ) -> None:
        """
        Ban a member from the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to ban.
        flags : BanFlags
            The flags for the command. (reason: str, purge: int (< 7), silent: bool)

        Raises
        ------
        discord.Forbidden
            If the bot is unable to ban the user.
        discord.HTTPException
            If an error occurs while banning the user.
        """

        assert ctx.guild

        # Check if moderator has permission to ban the member
        if not await self.check_conditions(ctx, member, ctx.author, "ban"):
            return

        # Execute ban with case creation and DM
        await self.execute_mod_action(
            ctx=ctx,
            case_type=CaseType.BAN,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="banned",
            actions=[
                (ctx.guild.ban(member, reason=flags.reason, delete_message_seconds=flags.purge * 86400), type(None)),
            ],
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(Ban(bot))
