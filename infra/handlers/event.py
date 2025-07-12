import discord
from discord.ext import commands

from core.bot import Tux
from core.ui.embeds import EmbedCreator, EmbedType
from core.utils.functions import is_harmful, strip_formatting
from infra.database.controllers import DatabaseController


class EventHandler(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        await self.db.guild.insert_guild_by_id(guild.id)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        await self.db.guild.delete_guild_by_id(guild.id)

    @staticmethod
    async def handle_harmful_message(message: discord.Message) -> None:
        """
        This function detects harmful linux commands and replies to the user with a warning.

        Parameters
        ----------
        message : discord.Message
            The message to check.

        Returns
        -------
        None
        """

        if message.author.bot:
            return

        stripped_content = strip_formatting(message.content)
        harmful = is_harmful(stripped_content)

        if harmful == "RM_COMMAND":
            await message.reply(
                "-# ⚠️ **This command is likely harmful. By running it, all directory contents will be deleted. There is no undo. Ensure you fully understand the consequences before proceeding. If you have received this message in error, please disregard it.**",
            )
            return
        if harmful == "FORK_BOMB":
            await message.reply(
                "-# ⚠️ **This command is likely harmful. By running it, all the memory in your system will be used. Ensure you fully understand the consequences before proceeding. If you have received this message in error, please disregard it.**",
            )
            return
        if harmful == "DD_COMMAND":
            await message.reply(
                "-# ⚠️ **This command is likely harmful. By running it, your disk will be overwritten or erased irreversibly. Ensure you fully understand the consequences before proceeding. If you have received this message in error, please disregard it.**",
            )
            return
        if harmful == "FORMAT_COMMAND":
            await message.reply(
                "-# ⚠️ **This command is likely harmful. By running it, your disk will be formatted. Ensure you fully understand the consequences before proceeding. If you have received this message in error, please disregard it.**",
            )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if not is_harmful(before.content) and is_harmful(after.content):
            await self.handle_harmful_message(after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        await self.handle_harmful_message(message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        flag_list = ["🏳️‍🌈", "🏳️‍⚧️"]

        user = self.bot.get_user(payload.user_id)
        if user is None or user.bot:
            return

        if payload.guild_id is None:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if channel is None or channel.id != 1172343581495795752 or not isinstance(channel, discord.TextChannel):
            return

        message = await channel.fetch_message(payload.message_id)

        emoji = payload.emoji
        if (
            any(0x1F1E3 <= ord(char) <= 0x1F1FF for char in emoji.name)
            or "flag" in emoji.name.lower()
            or emoji.name in flag_list
        ):
            await message.remove_reaction(emoji, member)
            return

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread) -> None:
        # TODO: Add database configuration for primmary support forum
        support_forum = 1172312653797007461

        if thread.parent_id == support_forum:
            owner_mention = thread.owner.mention if thread.owner else {thread.owner_id}

            if tags := [tag.name for tag in thread.applied_tags]:
                tag_list = ", ".join(tags)
                msg = f"<:tux_notify:1274504953666474025> **New support thread created** - help is appreciated!\n{thread.mention} by {owner_mention}\n<:tux_tag:1274504955163709525> **Tags**: `{tag_list}`"

            else:
                msg = f"<:tux_notify:1274504953666474025> **New support thread created** - help is appreciated!\n{thread.mention} by {owner_mention}"

            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.INFO,
                description=msg,
                custom_color=discord.Color.random(),
                hide_author=True,
            )

            general_chat = 1172245377395728467
            channel = self.bot.get_channel(general_chat)

            if channel is not None and isinstance(channel, discord.TextChannel):
                # TODO: Add database configuration for primary support role
                support_role = "<@&1274823545087590533>"

                await channel.send(content=support_role, embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(EventHandler(bot))
