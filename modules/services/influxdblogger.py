from typing import Any

from bot import Tux
from database.controllers import DatabaseController
from discord.ext import commands, tasks
from influxdb_client.client.influxdb_client import InfluxDBClient
from influxdb_client.client.write.point import Point
from influxdb_client.client.write_api import SYNCHRONOUS
from loguru import logger
from utils.config import CONFIG


class InfluxLogger(commands.Cog):
    def __init__(self, bot: Tux):
        self.bot = bot
        self.db = DatabaseController()
        self.influx_write_api: Any | None = None
        self.influx_org: str = ""

        if self.init_influx():
            self.logger.start()
        else:
            logger.warning("InfluxDB logger failed to init. Check .env configuration if you want to use it.")

    def init_influx(self) -> bool:
        """Initialize InfluxDB client for metrics logging.

        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        influx_token: str = CONFIG.INFLUXDB_TOKEN
        influx_url: str = CONFIG.INFLUXDB_URL
        self.influx_org: str = CONFIG.INFLUXDB_ORG

        if (influx_token != "") and (influx_url != "") and (self.influx_org != ""):
            write_client = InfluxDBClient(url=influx_url, token=influx_token, org=self.influx_org)
            # Using Any type to avoid complex typing issues with InfluxDB client
            self.influx_write_api = write_client.write_api(write_options=SYNCHRONOUS)  # type: ignore
            return True
        return False

    @tasks.loop(seconds=60)
    async def logger(self) -> None:
        """Log statistics to InfluxDB at regular intervals.

        Collects data from various database models and writes metrics to InfluxDB.
        """
        if not self.influx_write_api:
            logger.warning("InfluxDB writer not initialized, skipping metrics collection")
            return

        influx_bucket = "tux stats"

        # Collect the guild list from the database
        try:
            guild_list = await self.db.guild.find_many(where={})

            # Iterate through each guild and collect metrics
            for guild in guild_list:
                if not guild.guild_id:
                    continue

                guild_id = int(guild.guild_id)

                # Collect data by querying controllers
                starboard_stats = await self.db.starboard_message.find_many(where={"message_guild_id": guild_id})

                snippet_stats = await self.db.snippet.find_many(where={"guild_id": guild_id})

                afk_stats = await self.db.afk.find_many(where={"guild_id": guild_id})

                case_stats = await self.db.case.find_many(where={"guild_id": guild_id})

                # Create data points with type ignores for InfluxDB methods
                # The InfluxDB client's type hints are incomplete
                points: list[Point] = [
                    Point("guild stats").tag("guild", guild_id).field("starboard count", len(starboard_stats)),  # type: ignore
                    Point("guild stats").tag("guild", guild_id).field("snippet count", len(snippet_stats)),  # type: ignore
                    Point("guild stats").tag("guild", guild_id).field("afk count", len(afk_stats)),  # type: ignore
                    Point("guild stats").tag("guild", guild_id).field("case count", len(case_stats)),  # type: ignore
                ]

                # Write to InfluxDB
                self.influx_write_api.write(bucket=influx_bucket, org=self.influx_org, record=points)

        except Exception as e:
            logger.error(f"Error collecting metrics for InfluxDB: {e}")


async def setup(bot: Tux) -> None:
    await bot.add_cog(InfluxLogger(bot))
