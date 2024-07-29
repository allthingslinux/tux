import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from prisma.models import Case
from tux.utils.constants import Constants as CONST
from tux.utils.flags import UnjailFlags

from . import ModerationCogBase


class Unjail(ModerationCogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @commands.hybrid_command(
        name="unjail",
        aliases=["uj"],
        usage="$unjail [target] [reason] <silent>",
    )
    @commands.guild_only()
    async def unjail(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        flags: UnjailFlags,
    ) -> None:
        """
        Unjail a user in the server.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The discord context object.
        target : discord.Member
            The member to unjail.
        flags : UnjailFlags
            The flags for the command. (reason: str, silent: bool)
        """
        moderator = await commands.MemberConverter().convert(ctx, str(ctx.author.id))

        if ctx.guild is None:
            logger.warning("Unjail command used outside of a guild context.")
            return
        if target == ctx.author:
            await ctx.send("You cannot unjail yourself.", delete_after=10, ephemeral=True)
            return
        if target.top_role >= moderator.top_role:
            await ctx.send("You cannot unjail a user with a higher or equal role.", delete_after=10, ephemeral=True)
            return
        if target == ctx.guild.owner:
            await ctx.send("You cannot unjail the server owner.", delete_after=10, ephemeral=True)
            return

        # Convert the jail role ID to a discord.Role object
        jail_role = await self.config.get_jail_role(ctx.guild.id)
        if not jail_role:
            await ctx.send("No jail role has been set up for this server.", delete_after=10, ephemeral=True)
            return

        jail_role = await commands.RoleConverter().convert(ctx, str(jail_role))
        if not jail_role:
            await ctx.send("The jail role has been deleted.", delete_after=10, ephemeral=True)
            return

        # Check if the target is jailed or not
        if jail_role not in target.roles:
            await ctx.send("The user is not jailed.", delete_after=10, ephemeral=True)
            return

        # Check if the jail channel is set up
        jail_channel = await self.config.get_jail_channel(ctx.guild.id)
        if not jail_channel:
            await ctx.send("No jail channel has been set up for this server.", delete_after=10, ephemeral=True)
            return

        # Get the last jail case for the target
        case = await self.db.case.get_last_jail_case_by_target_id(ctx.guild.id, target.id)
        if case is None:
            await ctx.send("No jail case found for the user.", delete_after=10, ephemeral=True)
            return

        # Remove the jail role from the target
        await target.remove_roles(jail_role, reason=flags.reason)

        # Add the previous roles back to the target
        previous_roles = [await commands.RoleConverter().convert(ctx, str(role)) for role in case.case_target_roles]

        if previous_roles:
            await target.add_roles(*previous_roles, reason=flags.reason)
        else:
            await ctx.send("No previous roles found for the user.", delete_after=10, ephemeral=True)
            return

        # Insert the unjail case to the database
        case = await self.db.case.insert_case(
            case_target_id=target.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.UNJAIL,
            case_reason=flags.reason,
            guild_id=ctx.guild.id,
        )

        await self.handle_case_response(ctx, case, "created", flags.reason, target)

    async def handle_case_response(
        self,
        ctx: commands.Context[commands.Bot],
        case: Case | None,
        action: str,
        reason: str,
        target: discord.Member | discord.User,
        previous_reason: str | None = None,
    ) -> None:
        moderator = ctx.author

        fields = [
            ("Moderator", f"__{moderator}__\n`{moderator.id}`", True),
            ("Target", f"__{target}__\n`{target.id}`", True),
            ("Reason", f"> {reason}", False),
        ]

        if previous_reason:
            fields.append(("Previous Reason", f"> {previous_reason}", False))

        if case is not None:
            embed = await self.create_embed(
                ctx,
                title=f"Case #{case.case_number} ({case.case_type}) {action}",
                fields=fields,
                color=CONST.EMBED_COLORS["CASE"],
                icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"],
            )
            embed.set_thumbnail(url=target.avatar)
        else:
            embed = await self.create_embed(
                ctx,
                title=f"Case {action} ({CaseType.BAN})",
                fields=fields,
                color=CONST.EMBED_COLORS["CASE"],
                icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"],
            )

        await self.send_embed(ctx, embed, log_type="mod")
        await ctx.reply(embed=embed, delete_after=10, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Unjail(bot))
