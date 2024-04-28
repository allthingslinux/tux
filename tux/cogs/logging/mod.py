import discord
from discord.ext import commands

from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator


class ModLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.mod_log_channel_id: int = CONST.LOG_CHANNELS["MOD"]

    async def send_to_mod_log(self, embed: discord.Embed):
        channel = self.bot.get_channel(self.mod_log_channel_id)
        if isinstance(channel, discord.TextChannel):
            await channel.send(embed=embed)

    # @commands.Cog.listener()
    # async def on_member_ban(self, guild: discord.Guild, user: discord.User):
    #     embed = EmbedCreator.create_log_embed(
    #         title="Member Banned",
    #         description=f"{user.mention} has been banned.",
    #     )

    #     embed.add_field(name="User", value=user.name)
    #     embed.add_field(name="ID", value=f"`{user.id}`")
    #     embed.set_thumbnail(url=user.display_avatar)

    #     await self.send_to_mod_log(embed)

    # @commands.Cog.listener()
    # async def on_member_unban(self, guild: discord.Guild, user: discord.User):
    #     embed = EmbedCreator.create_log_embed(
    #         title="Member Unbanned",
    #         description=f"User: {user.name}",
    #     )

    #     await self.send_to_mod_log(embed)

    @commands.Cog.listener()
    async def on_automod_rule_create(self, rule: discord.AutoModRule):
        embed = EmbedCreator.create_log_embed(
            title="Automod Rule Created",
            description=f"Rule: {rule.name}",
        )

        await self.send_to_mod_log(embed)

    @commands.Cog.listener()
    async def on_automod_rule_update(self, rule: discord.AutoModRule):
        embed = EmbedCreator.create_log_embed(
            title="Automod Rule Updated",
            description=f"Rule: {rule.name}",
        )

        await self.send_to_mod_log(embed)

    @commands.Cog.listener()
    async def on_automod_rule_delete(self, rule: discord.AutoModRule):
        embed = EmbedCreator.create_log_embed(
            title="Automod Rule Deleted",
            description=f"Rule: {rule.name}",
        )

        await self.send_to_mod_log(embed)

    @commands.Cog.listener()
    async def on_reaction_clear(self, message: discord.Message, reactions: list[discord.Reaction]):
        embed = EmbedCreator.create_log_embed(
            title="Reactions cleared for",
            description=f"Message: {message.jump_url}",
        )

        await self.send_to_mod_log(embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModLogging(bot))
