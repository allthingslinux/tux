"""
InfluxDB metrics logging service.

This module provides time-series metrics collection and logging to InfluxDB
for monitoring bot performance, usage statistics, and system metrics.
"""

from typing import Any

import discord
from discord.ext import tasks
from influxdb_client.client.influxdb_client import InfluxDBClient
from influxdb_client.client.write.point import Point
from influxdb_client.client.write_api import SYNCHRONOUS
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.shared.config import CONFIG


class InfluxLogger(BaseCog):
    """Discord cog for logging metrics to InfluxDB."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the InfluxDB logger service.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this service to.
        """
        super().__init__(bot)
        self.influx_write_api: Any | None = None
        # avoid name collision with method names
        self.influx_org: str = ""

        if self.init_influx():
            self._log_guild_stats.start()
            self.logger.start()
        else:
            logger.warning(
                "InfluxDB logger failed to init. Check .env configuration if you want to use it.",
            )

    def init_influx(self) -> bool:
        """Initialize InfluxDB client for metrics logging.

        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        influx_token: str = CONFIG.EXTERNAL_SERVICES.INFLUXDB_TOKEN
        influx_url: str = CONFIG.EXTERNAL_SERVICES.INFLUXDB_URL
        self.influx_org = CONFIG.EXTERNAL_SERVICES.INFLUXDB_ORG

        if influx_token and influx_url and self.influx_org:
            write_client = InfluxDBClient(
                url=influx_url,
                token=influx_token,
                org=self.influx_org,
            )
            # Using Any type to avoid complex typing issues with InfluxDB client
            self.influx_write_api = write_client.write_api(write_options=SYNCHRONOUS)  # type: ignore
            return True
        return False

    @tasks.loop(seconds=60, name="influx_guild_stats")
    async def _log_guild_stats(self) -> None:
        """Log guild statistics to InfluxDB."""
        if not self.bot.is_ready() or not self.influx_write_api:
            logger.debug(
                "Bot not ready or InfluxDB writer not initialized, skipping InfluxDB logging.",
            )
            return

        for guild in self.bot.guilds:
            online_members = sum(
                m.status != discord.Status.offline for m in guild.members
            )

            tags = {"guild": guild.name}
            fields = {
                "members": guild.member_count,
                "online": online_members,
            }

            point = {"measurement": "guild_stats", "tags": tags, "fields": fields}

            self.influx_write_api.write(
                bucket="tux_stats",
                org=self.influx_org,
                record=point,
            )

    @_log_guild_stats.before_loop
    async def before_log_guild_stats(self) -> None:
        """Wait until the bot is ready."""
        await self.bot.wait_until_ready()

    async def cog_unload(self) -> None:
        """Cancel background tasks when the cog is unloaded."""
        if self.influx_write_api:
            self._log_guild_stats.cancel()
            self.logger.cancel()

    @tasks.loop(seconds=60, name="influx_db_logger")
    async def logger(self) -> None:
        """Log statistics to InfluxDB at regular intervals.

        Collects data from various database models and writes metrics to InfluxDB.
        """
        if not self.influx_write_api:
            logger.warning(
                "InfluxDB writer not initialized, skipping metrics collection",
            )
            return

        influx_bucket = "tux stats"

        # Collect the guild list from the database
        guild_list = await self.db.guild.find_many(where={})

        # Iterate through each guild and collect metrics
        for guild in guild_list:
            if not guild.id:
                continue

            guild_id = int(guild.id)

            # Collect data by querying controllers
            # Count starboard messages for this guild
            # Fallback to retrieving and counting (no dedicated count method yet)
            starboard_messages = []
            try:
                # Not all controllers implement find_many; do a safe query via guild id when available
                # StarboardMessageController currently lacks find_many; skip if not present
                get_msg = getattr(
                    self.db.starboard_message,
                    "get_starboard_message_by_id",
                    None,
                )
                if callable(get_msg):
                    # Cannot list all without an index; set to empty for now
                    starboard_messages = []
            except Exception:
                starboard_messages = []

            snippet_stats = await self.db.snippet.get_snippets_by_guild(guild_id)

            afk_stats = await self.db.afk.find_many(where={"guild_id": guild_id})

            # CaseController has no find_many; use get_all_cases
            case_stats = await self.db.case.get_all_cases(guild_id)

            # Create data points with type ignores for InfluxDB methods
            # The InfluxDB client's type hints are incomplete
            points: list[Point] = [
                Point("guild stats")
                .tag("guild", guild_id)
                .field("starboard count", len(starboard_messages)),  # type: ignore
                Point("guild stats")
                .tag("guild", guild_id)
                .field("snippet count", len(snippet_stats)),
                Point("guild stats")
                .tag("guild", guild_id)
                .field("afk count", len(afk_stats)),
                Point("guild stats")
                .tag("guild", guild_id)
                .field("case count", len(case_stats)),
            ]

            # Write to InfluxDB
            self.influx_write_api.write(
                bucket=influx_bucket,
                org=self.influx_org,
                record=points,
            )

    @logger.before_loop
    async def before_logger(self) -> None:
        """Wait until the bot is ready."""
        await self.bot.wait_until_ready()


async def setup(bot: Tux) -> None:
    """Set up the InfluxLogger cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    # Only load the cog if InfluxDB configuration is available
    if all(
        [
            CONFIG.EXTERNAL_SERVICES.INFLUXDB_TOKEN,
            CONFIG.EXTERNAL_SERVICES.INFLUXDB_URL,
            CONFIG.EXTERNAL_SERVICES.INFLUXDB_ORG,
        ],
    ):
        await bot.add_cog(InfluxLogger(bot))
    else:
        logger.warning(
            "InfluxDB configuration incomplete, skipping InfluxLogger cog",
        )
