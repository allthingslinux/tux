import discord
from discord.ext import commands

from tux.core.checks import require_moderator
from tux.core.flags import BanFlags
from tux.core.types import Tux
from tux.database.models import CaseType as DBCaseType
from tux.shared.functions import generate_usage

from . import ModerationCogBase


class Ban(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.ban.usage = generate_usage(self.ban, BanFlags)

    @commands.hybrid_command(name="ban", aliases=["b"])
    @commands.guild_only()
    @require_moderator()
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

        # Permission checks are handled by the @require_moderator() decorator
        # Additional validation will be handled by the ModerationCoordinator service

        # Execute ban with case creation and DM
        await self.moderate_user(
            ctx=ctx,
            case_type=DBCaseType.BAN,
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
