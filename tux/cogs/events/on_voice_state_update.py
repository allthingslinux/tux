import discord
import discord.utils
from discord.ext import commands
from loguru import logger

from tux.utils.constants import Constants as C


class OnVoiceStateUpdate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """
        Handles the event when a user's voice state is updated in a Discord Guild.

        Called whenever a user changes their voice state. This is applicable to things like joining/leaving a voice channel, muting/unmuting, and deafening/undeafening.

        Note:
            This function requires `Intents.voice_states` to be enabled.

        Args:
            member (Member): The member whose voice states changed.
            before (VoiceState): The voice state prior to the changes.
            after (VoiceState): The voice state after the changes.

        This event is currently used to handle the creation and deletion of temporary voice channels.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_voice_state_update
        """

        logger.info(f"Voice state update: {member.name} {before.channel} -> {after.channel}")
        logger.info(f"Constants: {C.TEMPVC_CATEGORY} {C.TEMPVC_CHANNEL}")

        if (
            before.channel is None
            and after.channel
            and after.channel.id == int(C.TEMPVC_CHANNEL or "0")
        ):
            new_channel = await after.channel.clone(name=f"[TEMP] - {member.name}")
            await member.move_to(new_channel)
            return

        if before.channel is not None:
            category = discord.utils.get(
                before.channel.guild.categories, id=int(C.TEMPVC_CATEGORY or "0") or 0
            )

            # if the category is not found, return
            if category is None:
                return

            # paranoia check
            if before.channel.category_id != category.id:
                return

            # if these are the same, the user is just deafening or muting
            if before.channel == after.channel:
                return

            # if the id of the channel is the same as the temporary channel, return
            # just incase they decide to name the channel starting with [TEMP]
            if before.channel.id == int(C.TEMPVC_CHANNEL or "0"):
                return

            # TODO: Replace this with a database so the user can change the name of the channel
            if not before.channel.name.startswith("[TEMP]"):
                return

            # get the number of members in the channel
            if len(before.channel.members) == 0:
                await before.channel.delete()
                return


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OnVoiceStateUpdate(bot))
