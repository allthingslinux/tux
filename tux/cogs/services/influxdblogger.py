from discord.ext import commands, tasks
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client.client.write.point import Point
from loguru import logger

from tux.bot import Tux
from tux.database.client import db
from tux.utils.config import CONFIG


class InfluxLogger(commands.Cog):
    """A cog that logs various bot statistics to InfluxDB."""

    def __init__(self, bot: Tux) -> None:
        self.bot: Tux = bot
        self.influx_client: InfluxDBClientAsync | None = None
        self.influx_org: str = CONFIG.INFLUXDB_ORG
        self.influx_bucket: str = "tux stats"

        if self._init_influx():
            self.logger.start()
            logger.info("InfluxDB logger initialized successfully.")
        else:
            logger.error("InfluxDB logger failed to initialize. Check .env configuration.")

    def _init_influx(self) -> bool:
        """Initialize the InfluxDB client connection.

        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        influx_token: str = CONFIG.INFLUXDB_TOKEN
        influx_url: str = CONFIG.INFLUXDB_URL

        if not all([influx_token, influx_url, self.influx_org]):
            return False

        try:
            self.influx_client = InfluxDBClientAsync(url=influx_url, token=influx_token, org=self.influx_org)
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB client: {e}")
            return False
        else:
            return True

    def _create_stat_point(self, guild_id: int, stat_name: str, value: int) -> Point:
        """Create a Point object for InfluxDB with the given statistics.

        Args:
            guild_id: The ID of the guild
            stat_name: The name of the statistic being recorded
            value: The value of the statistic

        Returns:
            Point: The constructed InfluxDB Point object
        """

        return (
            Point("guild stats")  # type: ignore
            .tag("guild", str(guild_id))  # type: ignore
            .field(stat_name, value)
        )  # type: ignore

    @tasks.loop(seconds=60)
    async def logger(self) -> None:
        """Task that logs guild statistics to InfluxDB every 60 seconds."""
        if not self.influx_client:
            return

        try:
            guild_list = await db.guild.find_many()

            async with self.influx_client as client:
                write_api = client.write_api()

                for guild in guild_list:
                    # Collect statistics for the current guild
                    stats = {
                        "starboard count": len(
                            await db.starboardmessage.find_many(where={"message_guild_id": guild.guild_id}),
                        ),
                        "snippet count": len(await db.snippet.find_many(where={"guild_id": guild.guild_id})),
                        "afk count": len(await db.afkmodel.find_many(where={"guild_id": guild.guild_id})),
                        "case count": len(await db.case.find_many(where={"guild_id": guild.guild_id})),
                    }

                    # Create points for each statistic
                    points = [
                        self._create_stat_point(guild.guild_id, stat_name, value) for stat_name, value in stats.items()
                    ]

                    # Write points to InfluxDB
                    await write_api.write(  # type: ignore
                        bucket=self.influx_bucket,
                        record=points,
                    )

        except Exception as e:
            logger.error(f"Failed to log guild statistics: {e}")

    async def cog_unload(self) -> None:
        """Cleanup when the cog is unloaded."""
        if self.influx_client:
            await self.influx_client.close()


async def setup(bot: Tux) -> None:
    """Setup function to add the cog to the bot."""
    await bot.add_cog(InfluxLogger(bot))
