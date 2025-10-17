import discord
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.shared.config import CONFIG


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

        # Initialize basic guild data (permissions only)
        await self.bot.db.guild_config.update_onboarding_stage(guild.id, "not_started")

    # TODO: Define data expiration policy for guilds
    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        await self.db.guild.delete_guild_by_id(guild.id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # Allow the IRC bridge to use the snippet command only
        if message.webhook_id in CONFIG.IRC_CONFIG.BRIDGE_WEBHOOK_IDS and (
            message.content.startswith(f"{CONFIG.get_prefix()}s ")
            or message.content.startswith(f"{CONFIG.get_prefix()}snippet ")
        ):
            ctx = await self.bot.get_context(message)
            await self.bot.invoke(ctx)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        """Automatically deny view permissions for jail role on new channels."""
        if not channel.guild:
            return

        # Get jail role for this guild
        jail_role_id = await self.db.guild_config.get_jail_role_id(channel.guild.id)
        if not jail_role_id:
            logger.debug(f"No jail role configured for guild {channel.guild.id}, skipping channel setup")
            return

        jail_role = channel.guild.get_role(jail_role_id)
        if not jail_role:
            logger.warning(f"Jail role {jail_role_id} not found in guild {channel.guild.id}")
            return

        # Set permissions to deny view for jail role
        try:
            await channel.set_permissions(
                jail_role,
                view_channel=False,
                read_messages=False,
                send_messages=False,
                reason="Auto-deny jail role on new channel",
            )
            logger.info(f"✅ Blocked jail role from new channel: {channel.name} in {channel.guild.name}")
        except discord.Forbidden:
            logger.warning(f"Missing permissions to set jail role permissions in {channel.name}")
        except Exception as e:
            logger.error(f"Failed to set jail role permissions on {channel.name}: {e}")


async def setup(bot: Tux) -> None:
    await bot.add_cog(EventHandler(bot))
