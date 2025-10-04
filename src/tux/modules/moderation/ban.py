import discord
from discord.ext import commands

from tux.core.bot import Tux
from tux.core.checks import requires_command_permission
from tux.core.flags import BanFlags
from tux.database.models import CaseType as DBCaseType

from . import ModerationCogBase


class Ban(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)

    @commands.hybrid_command(name="ban", aliases=["b"])
    @commands.guild_only()
    @requires_command_permission()
    async def ban(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member | discord.User,
        *,
        flags: BanFlags,
    ) -> None:
        """
        Ban a member from the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member | discord.User
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

        # Execute ban with case creation and DM
        await self.moderate_user(
            ctx=ctx,
            case_type=DBCaseType.BAN,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="banned",
            actions=[
                (
                    lambda: ctx.guild.ban(
                        member,
                        reason=flags.reason,
                        delete_message_seconds=flags.purge * 86400,
                    )
                    if ctx.guild
                    else None,
                    type(None),
                ),
            ],
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(Ban(bot))
