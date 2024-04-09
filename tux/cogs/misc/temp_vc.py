import discord
from discord.ext import commands
from loguru import logger

from tux.utils.constants import Constants as CONST


class TempVc(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.base_vc_name: str = "/tmp/"

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if after.channel and after.channel.id == int(CONST.TEMPVC_CHANNEL_ID or "0"):
            # check if the user already has a temporary channel
            # if so move the user to the existing channel
            for channel in after.channel.guild.voice_channels:
                if channel.name == self.base_vc_name + member.name:
                    await member.move_to(channel)
                    logger.info(f"Moved {member.name} to existing temporary channel.")
                    return
            new_channel = await after.channel.clone(name=self.base_vc_name + member.name)
            await member.move_to(new_channel)
            logger.info(f"Created temporary channel for {member.name}.")
            return

        if before.channel is not None:
            category = discord.utils.get(
                before.channel.guild.categories, id=int(CONST.TEMPVC_CATEGORY_ID or "0")
            )

            if (
                not category
                or before.channel.category_id != category.id
                or before.channel == after.channel
                or before.channel.id == int(CONST.TEMPVC_CHANNEL_ID or "0")
                or not before.channel.name.startswith(self.base_vc_name)
            ):
                return

            if len(before.channel.members) == 0:
                await before.channel.delete()
                logger.info(
                    f"Deleted temporary channel {before.channel.name} as it has no members."
                )

            # search all lost temporary channels and delete them
            for channel in category.voice_channels:
                # checks if the channel is a temporary channel
                if (
                    not channel.name.startswith(self.base_vc_name)
                    or len(channel.members) != 0
                    or channel.id == int(CONST.TEMPVC_CHANNEL_ID or "0")
                ):
                    continue

                if len(channel.members) == 0:
                    await channel.delete()
                    logger.info(f"Deleted temporary channel {channel.name} as it has no members.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TempVc(bot))
