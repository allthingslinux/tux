import asyncio
import os
from typing import Any

import discord
import sentry_sdk
from discord.ext import commands
from loguru import logger
from opentelemetry import trace
from opentelemetry.propagate import set_global_textmap  # type: ignore
from opentelemetry.sdk.trace import TracerProvider
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.loguru import LoguruIntegration
from sentry_sdk.integrations.opentelemetry import (
    SentryPropagator,  # type: ignore
    SentrySpanProcessor,  # type: ignore
)

from tux.cog_loader import CogLoader
from tux.database.client import db
from tux.utils.constants import Constants as CONST

provider = TracerProvider()
provider.add_span_processor(SentrySpanProcessor())
trace.set_tracer_provider(provider)
set_global_textmap(SentryPropagator())


class TuxBot(commands.Bot):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        asyncio.create_task(self.setup())  # noqa: RUF006

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
            dsn=os.getenv("SENTRY_URL"),
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            enable_tracing=True,
            instrumenter="otel",
            integrations=[
                AsyncioIntegration(),
                AioHttpIntegration(),
                LoguruIntegration(),
            ],
            environment="staging" if CONST.STAGING == "True" else "production",
        )

        intents = discord.Intents.all()

        prefix = CONST.STAGING_PREFIX if CONST.STAGING == "True" else CONST.PROD_PREFIX
        token = CONST.STAGING_TOKEN if CONST.STAGING == "True" else CONST.PROD_TOKEN

        bot = TuxBot(command_prefix=prefix, intents=intents)

        await bot.start(token=token, reconnect=True)

    except Exception as e:
        logger.error(f"An error occurred while running the bot: {e}")


if __name__ == "__main__":
    asyncio.run(main())
