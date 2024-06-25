import discord
from discord.ext import commands

from prisma.enums import CaseType
from prisma.models import Case
from tux.database.controllers import DatabaseController
from tux.utils.constants import Constants as CONST
from tux.utils.embeds import create_embed_footer


class Moderation:
    """
    A utility/helper class to handle moderation-related operations.
    """

    def __init__(self) -> None:
        self.db_controller = DatabaseController()
        self.mod_log_channel_id = CONST.LOG_CHANNELS["MOD"]
        self.mod_log_embed_color = CONST.COLORS["RED"]
        self.mod_log_embed_icon = CONST.ICONS["SUCCESS"]

    async def create_modlog_embed(
        self,
        ctx: commands.Context[commands.Bot],
        case_number: int,
        action: str,
        moderator: discord.Member,
        target: discord.Member,
        reason: str,
        duration: str | None = None,
    ) -> discord.Embed:
        embed = discord.Embed()
        embed.color = self.mod_log_embed_color
        author_name = f"Case #{case_number} | {action} ({duration})" if duration else f"Case #{case_number} | {action}"
        embed.set_author(name=author_name, icon_url=self.mod_log_embed_icon)
        embed.add_field(name="Moderator", value=f"__{moderator.name}__\n`{moderator.id}`", inline=True)
        embed.add_field(name="Target", value=f"__{target.name}__\n`{target.id}`", inline=True)
        embed.add_field(name="Reason", value=f"> {reason}")
        footer = create_embed_footer(ctx)
        embed.set_footer(text=footer[0], icon_url=footer[1])
        embed.timestamp = ctx.message.created_at
        return embed

    async def send_modlog_embed(
        self,
        ctx: commands.Context[commands.Bot],
        embed: discord.Embed,
    ) -> None:
        if (
            ctx.guild
            and (mod_log_channel := ctx.guild.get_channel(self.mod_log_channel_id))
            and isinstance(mod_log_channel, discord.TextChannel)
        ):
            await mod_log_channel.send(embed=embed)

    async def send_command_response(
        self,
        ctx: commands.Context[commands.Bot],
        embed: discord.Embed,
    ) -> None:
        await ctx.reply(embed=embed, delete_after=5)

    async def insert_case(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        case_type: CaseType,
        reason: str,
    ) -> Case | None:
        if ctx.guild:
            return await self.db_controller.cases.insert_case(
                guild_id=ctx.guild.id,
                case_target_id=target.id,
                case_moderator_id=ctx.author.id,
                case_type=case_type,
                case_reason=reason,
            )
        return None
