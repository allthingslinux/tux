import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from prisma.models import Case
from tux.utils import checks
from tux.utils.constants import Constants as CONST
from tux.utils.flags import JailFlags

from . import ModerationCogBase


class Jail(ModerationCogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @app_commands.command(
        name="setup_jail",
    )
    @commands.guild_only()
    @checks.ac_has_pl(7)
    async def setup_jail(self, interaction: discord.Interaction) -> None:
        """
        Set up the jail role channel permissions for the server.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        """

        if interaction.guild is None:
            return

        jail_role_id = await self.config.get_guild_config_field_value(interaction.guild.id, "jail_role_id")
        if not jail_role_id:
            await interaction.response.send_message("No jail role has been set up for this server.", ephemeral=True)
            return

        jail_role = interaction.guild.get_role(jail_role_id)
        if not jail_role:
            await interaction.response.send_message("The jail role has been deleted.", ephemeral=True)
            return

        jail_channel_id = await self.config.get_guild_config_field_value(interaction.guild.id, "jail_channel_id")
        if not jail_channel_id:
            await interaction.response.send_message("No jail channel has been set up for this server.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        await self._set_permissions_for_channels(interaction, jail_role, jail_channel_id)

        await interaction.edit_original_response(
            content="Permissions have been set up for the jail role.",
        )

    async def _set_permissions_for_channels(
        self,
        interaction: discord.Interaction,
        jail_role: discord.Role,
        jail_channel_id: int,
    ) -> None:
        if interaction.guild is None:
            return

        for channel in interaction.guild.channels:
            if not isinstance(channel, discord.TextChannel | discord.VoiceChannel | discord.ForumChannel):
                continue

            if (
                jail_role in channel.overwrites
                and channel.overwrites[jail_role].send_messages is False
                and channel.overwrites[jail_role].read_messages is False
                and channel.id != jail_channel_id
            ):
                continue

            await channel.set_permissions(jail_role, send_messages=False, read_messages=False)
            if channel.id == jail_channel_id:
                await channel.set_permissions(jail_role, send_messages=True, read_messages=True)

            await interaction.edit_original_response(content=f"Setting up permissions for {channel.name}.")

    @commands.hybrid_command(
        name="jail",
        aliases=["j"],
        usage="$jail [target] [reason] <silent>",
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def jail(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        *,
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

        if not ctx.guild:
            logger.warning("Jail command used outside of a guild context.")
            return

        moderator = ctx.author

        if not await self.check_conditions(ctx, target, moderator, "jail"):
            return

        jail_role_id = await self.config.get_jail_role(ctx.guild.id)
        if not jail_role_id:
            await ctx.send("No jail role has been set up for this server.", delete_after=30, ephemeral=True)
            return

        jail_role = ctx.guild.get_role(jail_role_id)
        if not jail_role:
            await ctx.send("The jail role has been deleted.", delete_after=30, ephemeral=True)
            return

        target_roles: list[discord.Role] = self._get_manageable_roles(target, jail_role)
        if jail_role in target.roles:
            await ctx.send("The user is already jailed.", delete_after=30, ephemeral=True)
            return

        case_target_roles = [role.id for role in target_roles]

        await self._jail_user(ctx, target, flags, jail_role, target_roles)

        case = await self._insert_jail_case(ctx, target, flags.reason, case_target_roles)

        await self.handle_case_response(ctx, case, "created", flags.reason, target)

    async def _insert_jail_case(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        reason: str,
        case_target_roles: list[int] | None = None,
    ) -> Case | None:
        if not ctx.guild:
            logger.warning("Jail command used outside of a guild context.")
            return None

        try:
            return await self.db.case.insert_case(
                case_target_id=target.id,
                case_moderator_id=ctx.author.id,
                case_type=CaseType.JAIL,
                case_reason=reason,
                guild_id=ctx.guild.id,
                case_target_roles=case_target_roles,
            )
        except Exception as e:
            logger.error(f"Failed to insert jail case for {target}. {e}")
            await ctx.send(f"Failed to insert jail case for {target}. {e}", delete_after=30, ephemeral=True)
            return None

    def _get_manageable_roles(self, target: discord.Member, jail_role: discord.Role) -> list[discord.Role]:
        return [
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

    async def _jail_user(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        flags: JailFlags,
        jail_role: discord.Role,
        target_roles: list[discord.Role],
    ) -> None:
        try:
            await self.send_dm(ctx, flags.silent, target, flags.reason, "jailed")

            if target_roles:
                await target.remove_roles(*target_roles, reason=flags.reason, atomic=False)
            await target.add_roles(jail_role, reason=flags.reason)

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Failed to jail {target}. {e}")
            await ctx.send(f"Failed to jail {target}. {e}", delete_after=30, ephemeral=True)
            return

    async def handle_case_response(
        self,
        ctx: commands.Context[commands.Bot],
        case: Case | None,
        action: str,
        reason: str,
        target: discord.Member | discord.User,
        previous_reason: str | None = None,
    ) -> None:
        fields = [
            ("Moderator", f"__{ctx.author}__\n`{ctx.author.id}`", True),
            ("Target", f"__{target}__\n`{target.id}`", True),
            ("Reason", f"> {reason}", False),
        ]

        if previous_reason:
            fields.append(("Previous Reason", f"> {previous_reason}", False))

        embed = await self._create_case_embed(ctx, case, action, fields, target)

        await self.send_embed(ctx, embed, log_type="mod")
        await ctx.send(embed=embed, delete_after=30, ephemeral=True)

    async def _create_case_embed(
        self,
        ctx: commands.Context[commands.Bot],
        case: Case | None,
        action: str,
        fields: list[tuple[str, str, bool]],
        target: discord.Member | discord.User,
    ) -> discord.Embed:
        title = f"Case #{case.case_number} ({case.case_type}) {action}" if case else f"Case {action} ({CaseType.JAIL})"

        embed = await self.create_embed(
            ctx,
            title=title,
            fields=fields,
            color=CONST.EMBED_COLORS["CASE"],
            icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"],
        )

        embed.set_thumbnail(url=target.avatar)
        return embed


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Jail(bot))
