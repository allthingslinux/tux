import discord
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.services.onboarding import GuildOnboardingService
from tux.shared.config import CONFIG
from tux.shared.functions import is_harmful, strip_formatting


class EventHandler(BaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self._guilds_registered = False

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Register all guilds the bot is in on startup."""
        if self._guilds_registered:
            return

        logger.info("🔄 Registering all guilds in database...")
        registered_count = 0

        for guild in self.bot.guilds:
            try:
                await self.db.guild.insert_guild_by_id(guild.id)
                registered_count += 1
            except Exception as e:
                # Guild might already exist, that's fine
                logger.trace(f"Guild {guild.id} ({guild.name}) already registered or error: {e}")

        logger.info(f"✅ Registered {registered_count} guilds in database")
        self._guilds_registered = True

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        await self.db.guild.insert_guild_by_id(guild.id)

        # Initialize onboarding for new guild
        onboarding = GuildOnboardingService(self.bot)
        await onboarding.initialize_new_guild(guild)

    # TODO: Define data expiration policy for guilds
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

        if message.author.bot and message.webhook_id not in CONFIG.IRC_CONFIG.BRIDGE_WEBHOOK_IDS:
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
        # Allow the IRC bridge to use the snippet command only
        if message.webhook_id in CONFIG.IRC_CONFIG.BRIDGE_WEBHOOK_IDS and (
            message.content.startswith(f"{CONFIG.get_prefix()}s ")
            or message.content.startswith(f"{CONFIG.get_prefix()}snippet ")
        ):
            ctx = await self.bot.get_context(message)
            await self.bot.invoke(ctx)

        await self.handle_harmful_message(message)


async def setup(bot: Tux) -> None:
    await bot.add_cog(EventHandler(bot))
