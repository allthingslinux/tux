import asyncio
import os
from typing import Any

import discord
import sentry_sdk
from discord.ext import commands
from dotenv import load_dotenv
from loguru import logger
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.loguru import LoguruIntegration

from tux.cog_loader import CogLoader
from tux.database.client import db

load_dotenv()


class TuxBot(commands.Bot):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        asyncio.create_task(self.setup())

    async def setup(self) -> None:
        await self.load_cogs()

    async def load_cogs(self) -> None:
        await CogLoader.setup(self)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        logger.info(f"{self.user} has connected to Discord!")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="All Things Linux",
            )
        )

        await db.connect()

    @commands.Cog.listener()
    async def on_disconnect(self) -> None:
        logger.warning("Bot has disconnected from Discord.")

        await db.disconnect()


async def main() -> None:
    try:
        sentry_sdk.init(
            dsn="https://b7ef0082e50eff6e166e78807498914d@o4506955434885120.ingest.us.sentry.io/4506955438227457",
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            enable_tracing=True,
            integrations=[
                AsyncioIntegration(),
                AioHttpIntegration(),
                LoguruIntegration(),
            ],
        )

        bot = TuxBot(command_prefix=">", intents=discord.Intents.all())

        await bot.start(token=os.getenv("TOKEN") or "", reconnect=True)

    except Exception as e:
        logger.error(f"An error occurred while running the bot: {e}")


if __name__ == "__main__":
    asyncio.run(main())
