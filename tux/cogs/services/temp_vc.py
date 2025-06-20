import discord
from discord.ext import commands

from tux.bot import Tux
from tux.utils.config import CONFIG


class TempVc(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.base_vc_name: str = "/tmp/"

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """
        Temporarily create a voice channel for a user when they join the temporary voice channel.
        If the user leaves the temporary voice channel, the channel will be deleted.

        Parameters
        ----------
        member : discord.Member
            The member that triggered the event.
        before : discord.VoiceState
            The voice state before the event.
        after : discord.VoiceState
            The voice state after the event.
        """

        # Ensure CONFIGants are set correctly
        temp_channel_id = int(CONFIG.TEMPVC_CHANNEL_ID or "0")
        temp_category_id = int(CONFIG.TEMPVC_CATEGORY_ID or "0")
        if temp_channel_id == 0 or temp_category_id == 0:
            return

        # When user joins the temporary voice channel
        if after.channel and after.channel.id == temp_channel_id:
            await self._handle_user_join(member, after.channel)

        # When user leaves any voice channel
        elif before.channel:
            await self._handle_user_leave(before.channel, after.channel, temp_channel_id, temp_category_id)

    async def _handle_user_join(
        self,
        member: discord.Member,
        channel: discord.VoiceChannel | discord.StageChannel,
    ) -> None:
        """
        Handle the case when a user joins the temporary voice channel.

        Parameters
        ----------
        member : discord.Member
            The member that joined the channel.
        channel : discord.VoiceChannel
            The channel that the member joined.
        """

        for voice_channel in channel.guild.voice_channels:
            # Check if the channel is a temporary channel and if it is the user's channel
            if voice_channel.name == self.base_vc_name + member.name:
                await member.move_to(voice_channel)
                return

        # Create a new channel for the user if it doesn't exist
        new_channel = await channel.clone(name=self.base_vc_name + member.name)
        await member.move_to(new_channel)

    async def _handle_user_leave(
        self,
        before_channel: discord.VoiceChannel | discord.StageChannel,
        after_channel: discord.VoiceChannel | discord.StageChannel | None,
        temp_channel_id: int,
        temp_category_id: int,
    ) -> None:
        """
        Handle the case when a user leaves a voice channel. Deletes empty temporary channels.

        Parameters
        ----------
        before_channel : discord.VoiceChannel
            The channel the user was in before.
        after_channel : discord.VoiceChannel
            The channel the user moved to. Could be None if the user disconnected.
        temp_channel_id: int
            The ID of the temporary voice channel the bot manages.
        temp_category_id: int
            The ID of the category holding temporary voice channels.
        """

        # Get the category of the temporary channels
        category = discord.utils.get(before_channel.guild.categories, id=temp_category_id)

        # Check if the channel is a temporary channel
        if (
            not category
            or before_channel.category_id != category.id
            or before_channel == after_channel
            or before_channel.id == temp_channel_id
            or not before_channel.name.startswith(self.base_vc_name)
        ):
            return

        # Delete the channel if it is empty
        if len(before_channel.members) == 0:
            await before_channel.delete()

        # Search and delete all empty temporary channels
        for channel in category.voice_channels:
            if (
                not channel.name.startswith(self.base_vc_name)
                or len(channel.members) != 0
                or channel.id == temp_channel_id
            ):
                continue

            await channel.delete()


async def setup(bot: Tux) -> None:
    await bot.add_cog(TempVc(bot))
