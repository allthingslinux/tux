import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.bot import Tux
from tux.utils import checks
from tux.utils.flags import UnbanFlags, generate_usage

from . import ModerationCogBase


class Unban(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.unban.usage = generate_usage(self.unban, UnbanFlags)

    @commands.hybrid_command(
        name="unban",
        aliases=["ub"],
    )
    @commands.guild_only()
    @checks.has_pl(3)
    async def unban(
        self,
        ctx: commands.Context[Tux],
        username_or_id: str,
        reason: str | None = None,
        *,
        flags: UnbanFlags,
    ) -> None:
        """
        Unban a user from the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        username_or_id : str
            The username or ID of the user to unban.
        reason : str | None
            The reason for the unban.
        flags : UnbanFlags
            The flags for the command.

        Raises
        ------
        discord.Forbidden
            If the bot does not have the necessary permissions.
        discord.HTTPException
            If an error occurs while unbanning the user.
        """

        assert ctx.guild
        await ctx.defer(ephemeral=True)

        # Get the list of banned users in the guild
        banned_users = [ban.user async for ban in ctx.guild.bans()]
        user = await commands.UserConverter().convert(ctx, username_or_id)

        if user not in banned_users:
            await ctx.send(f"{user} was not found in the guild ban list.", ephemeral=True)
            return

        final_reason: str = reason if reason is not None else "No reason provided"

        try:
            await ctx.guild.unban(user, reason=final_reason)

        except (discord.Forbidden, discord.HTTPException, discord.NotFound) as e:
            logger.error(f"Failed to unban {user}. {e}")
            await ctx.send(f"Failed to unban {user}. {e}", ephemeral=True)
            return

        case = await self.db.case.insert_case(
            guild_id=ctx.guild.id,
            case_user_id=user.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.UNBAN,
            case_reason=final_reason,
        )

        await self.handle_case_response(ctx, CaseType.UNBAN, case.case_number, final_reason, user, dm_sent=False)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Unban(bot))
