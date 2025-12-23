"""Event handlers for Tux Bot such as on ready, on guild join, on guild remove, on message and on guild channel create."""

import discord
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.shared.config import CONFIG


class EventHandler(BaseCog):
    """Event handlers for Tux Bot such as on ready, on guild join, on guild remove, on message and on guild channel create."""

    def __init__(self, bot: Tux) -> None:
        """
        Initialize the EventHandler cog.

        Parameters
        ----------
        bot : Tux
            The bot instance.
        """
        super().__init__(bot)
        self._guilds_registered = False

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Register all guilds the bot is in on startup and reconnections."""
        # Check if bot setup has completed
        if not self.bot.setup_complete:
            logger.warning("on_ready fired before setup_complete")
            return

        logger.info("Bot ready, registering guilds...")

        # Always register guilds on ready - Discord.py can reconnect and guilds may change
        logger.info("Registering all guilds in database...")
        registered_count = 0
        skipped_count = 0

        for guild in self.bot.guilds:
            try:
                logger.debug(f"Attempting to register guild {guild.id} ({guild.name})")
                result, created = await self.db.guild.get_or_create(id=guild.id)
                if created:
                    registered_count += 1
                    logger.info(
                        f"Successfully registered guild {guild.id} ({guild.name}) - id {result.id}",
                    )
                else:
                    skipped_count += 1
                    logger.debug(
                        f"Guild {guild.id} ({guild.name}) already exists - skipped",
                    )
            except Exception as e:
                # This shouldn't happen with get_or_create, but log if it does
                skipped_count += 1
                logger.error(
                    f"Unexpected error registering guild {guild.id} ({guild.name}): {e}",
                )
                logger.debug(f"Guild registration error details: {e}", exc_info=True)

        logger.info(
            f"Registered {registered_count} guilds, skipped {skipped_count} existing guilds in database",
        )
        self._guilds_registered = True

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """On guild join event handler."""
        _, created = await self.db.guild.get_or_create(id=guild.id)
        if created:
            logger.info(f"New guild joined: {guild.id} ({guild.name})")
        else:
            logger.warning(
                f"Guild join event fired for existing guild: {guild.id} ({guild.name})",
            )

        # Initialize basic guild data (permissions only)
        await self.bot.db.guild_config.update_onboarding_stage(guild.id, "not_started")

    # TODO: Define data expiration policy for guilds
    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """On guild remove event handler."""
        await self.db.guild.delete_guild_by_id(guild.id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """On message event handler."""
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
            logger.debug(
                f"No jail role configured for guild {channel.guild.id}, skipping channel setup",
            )
            return

        jail_role = channel.guild.get_role(jail_role_id)
        if not jail_role:
            logger.warning(
                f"Jail role {jail_role_id} not found in guild {channel.guild.id}",
            )
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
            logger.info(
                f"Blocked jail role from new channel: {channel.name} in {channel.guild.name}",
            )
        except discord.Forbidden:
            logger.warning(
                f"Missing permissions to set jail role permissions in {channel.name}",
            )
        except Exception as e:
            logger.error(f"Failed to set jail role permissions on {channel.name}: {e}")


async def setup(bot: Tux) -> None:
    """Cog setup for event handler.

    Parameters
    ----------
    bot : Tux
        The bot instance.
    """
    await bot.add_cog(EventHandler(bot))
