import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from prisma.models import Case
from tux.utils.constants import Constants as CONST
from tux.utils.flags import JailFlags

from . import ModerationCogBase


class Jail(ModerationCogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @commands.hybrid_command(
        name="jail",
        aliases=["j"],
        usage="$jail [target] [reason] <silent>",
    )
    @commands.guild_only()
    async def jail(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        flags: JailFlags,
    ) -> None:
        """
        Jail a user in the server.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The discord context object.
        target : discord.Member
            The member to jail.
        flags : JailFlags
            The flags for the command. (reason: str, silent: bool)
        """
        moderator = await commands.MemberConverter().convert(ctx, str(ctx.author.id))

        if ctx.guild is None:
            logger.warning("Jail command used outside of a guild context.")
            return
        if target == ctx.author:
            await ctx.send("You cannot jail yourself.", delete_after=10, ephemeral=True)
            return
        if target.top_role >= moderator.top_role:
            await ctx.send("You cannot jail a user with a higher or equal role.", delete_after=10, ephemeral=True)
            return
        if target == ctx.guild.owner:
            await ctx.send("You cannot jail the server owner.", delete_after=10, ephemeral=True)
            return

        # Convert the jail role ID to a discord.Role object
        jail_role = await self.config.get_jail_role(ctx.guild.id)
        if not jail_role:
            await ctx.send("No jail role has been set up for this server.", delete_after=10, ephemeral=True)
            return
        jail_role = ctx.guild.get_role(jail_role)

        # Get the target roles that are manageable
        target_roles = [
            role
            for role in target.roles
            if not (
                role.is_bot_managed()
                or role.is_premium_subscriber()
                or role.is_integration()
                or role.is_default()
                or role == jail_role
            )
            and role.is_assignable()
        ]

        # Get the target role IDs for the case
        case_target_roles = [role.id for role in target_roles]

        try:
            if jail_role is not None:
                # Send a DM to the target if the silent flag is not set
                await self.send_dm(ctx, flags.silent, target, flags.reason, "jailed")
                # Remove all roles
                await target.remove_roles(*target_roles, reason=flags.reason)
                # Add the jail role
                await target.add_roles(jail_role, reason=flags.reason)
            else:
                await ctx.send("No jail role has been set up for this server.", delete_after=10, ephemeral=True)
                return

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Failed to jail {target}. {e}")
            await ctx.send(f"Failed to jail {target}. {e}", delete_after=10, ephemeral=True)
            return

        case = await self.db.case.insert_case(
            guild_id=ctx.guild.id,
            case_target_id=target.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.JAIL,
            case_reason=flags.reason,
            case_target_roles=case_target_roles,
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
        else:
            embed = await self.create_embed(
                ctx,
                title=f"Case {action} ({CaseType.JAIL})",
                fields=fields,
                color=CONST.EMBED_COLORS["CASE"],
                icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"],
            )

        await self.send_embed(ctx, embed, log_type="mod")
        await ctx.reply(embed=embed, delete_after=10, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Jail(bot))
