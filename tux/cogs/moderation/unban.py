from discord.ext import commands

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

        # Get the list of banned users in the guild
        banned_users = [ban.user async for ban in ctx.guild.bans()]

        # Convert the username_or_id to a user object
        try:
            user = await commands.UserConverter().convert(ctx, username_or_id)
        except commands.UserNotFound:
            await ctx.send(f"{username_or_id} was not found.", ephemeral=True)
            return

        # Check if the user is banned
        if user not in banned_users:
            await ctx.send(f"{user} was not found in the guild ban list.", ephemeral=True)
            return

        # Check if moderator has permission to unban the user
        if not await self.check_conditions(ctx, user, ctx.author, "unban"):
            return

        final_reason = reason or self.DEFAULT_REASON

        # Execute unban with case creation
        await self.execute_mod_action(
            ctx=ctx,
            case_type=CaseType.UNBAN,
            user=user,
            final_reason=final_reason,
            # No DM for unbans due to user not being in the guild
            silent=True,
            # No DM for unbans due to user not being in the guild
            dm_action="",
            actions=[(ctx.guild.unban(user, reason=final_reason), type(None))],
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(Unban(bot))
