import asyncio
import concurrent.futures
import os
import sys
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

    # sets a random status message for the bot and waits 30 minutes
    async def change_activity(self) -> None:
        """
        Asynchronous function to change the bot's activity in a loop.

        This function will cycle through a list of activities every 5 minutes.
        """
        while True:
            activities = [
                discord.Activity(type=discord.ActivityType.watching, name="All Things Linux"),
                discord.Streaming(name="fortnite gamer hourz", url="https://twitch.tv/urmom"),
                discord.Activity(type=discord.ActivityType.playing, name="with fire"),
                discord.Activity(
                    type=discord.ActivityType.watching, name=f"{len(self.users)} members"
                ),
                discord.Activity(type=discord.ActivityType.watching, name="linux tech tips"),
                discord.Activity(type=discord.ActivityType.listening, name="mpd"),
                discord.Activity(type=discord.ActivityType.watching, name="a vast field of grain"),
                discord.Activity(
                    type=discord.ActivityType.playing,
                    name="i am calling about your car's extended warranty",
                ),
            ]

            for activity in activities:
                await self.change_presence(activity=activity)
                await asyncio.sleep(5 * 60)

    # coroutine for console commands
    # loops user input and executes commands
    async def console(self) -> None:
        if not os.isatty(sys.stdin.fileno()):
            logger.info("Running in a non-interactive mode. Skipping console input.")
            return
        logger.info("Console is ready. Type 'help' for a list of commands.")
        while True:
            # Use asyncio.run_in_executor to run input in a separate thread
            with concurrent.futures.ThreadPoolExecutor() as pool:
                command = await asyncio.get_event_loop().run_in_executor(pool, input, ">>> ")

                if command == "help":
                    logger.info("Available commands:")
                    logger.info("help - Display this message")
                    logger.info("send [channel_id] [message] - Send a message to a channel")
                    logger.info("embedbuild - Build an embed to send to a channel")
                    logger.info("setstatus - Set the bot's status")
                    logger.info("exit - Stop the bot")
                    continue
                if command == "exit":
                    logger.info("Goodbye!")
                    logger.info(
                        "Any warnings or errors after this message are expected and can (probably) be ignored safely."
                    )
                    # stop the bot
                    await self.close()
                    continue
                if command.startswith("send"):
                    command = command.split(" ")

                    # check if the command has the correct amount of arguments
                    if len(command) < 3:
                        logger.error("Usage: send [channel_id] [message]")
                        continue

                    # get the channel id and message from the command
                    channel_id = command[1]
                    message = " ".join(command[2:])

                    # get the channel object from the channel id
                    channel = self.get_channel(int(channel_id))

                    # check if the channel object is not None and is a text channel
                    if channel is None or not isinstance(channel, discord.TextChannel):
                        logger.error("Channel not found or is not a text channel.")
                        continue

                    await channel.send(message)
                    continue
                if command == "embedbuild":
                    # query the user for the title, description, and color of the embed
                    title = await asyncio.get_event_loop().run_in_executor(pool, input, "Title: ")
                    # ask the user to say DONE when they are finished writing the description
                    description = ""
                    while True:
                        line = await asyncio.get_event_loop().run_in_executor(
                            pool, input, "Description (type 'DONE' to finish): "
                        )
                        if line == "DONE":
                            break
                        description += line + "\n"
                    color = await asyncio.get_event_loop().run_in_executor(
                        pool, input, "Color (hex): "
                    )
                    channel_id = await asyncio.get_event_loop().run_in_executor(
                        pool, input, "Channel ID: "
                    )

                    # check if the color is a valid hex color
                    if not color.startswith("#") or len(color) != 7:
                        logger.error("Invalid color. Must be a valid hex color. Example: #ff0000")
                        continue

                    # create the embed
                    embed = discord.Embed(
                        title=title, description=description, color=int(color[1:], 16)
                    )

                    # send the embed to the channel
                    channel = self.get_channel(int(channel_id))
                    if channel is None or not isinstance(channel, discord.TextChannel):
                        logger.error("Channel not found or is not a text channel.")
                        continue

                    await channel.send(embed=embed)
                    continue
                if command == "setstatus":
                    # query the user for the status type and status message
                    status_type = await asyncio.get_event_loop().run_in_executor(
                        pool, input, "Status type (watching, listening, playing, streaming): "
                    )

                    status_message = await asyncio.get_event_loop().run_in_executor(
                        pool, input, "Status message: "
                    )

                    if status_type == "streaming":
                        stream_url = await asyncio.get_event_loop().run_in_executor(
                            pool, input, "Stream URL: "
                        )
                        await self.change_presence(
                            activity=discord.Streaming(name=status_message, url=stream_url)
                        )
                        continue

                    # set the bot's status
                    await self.change_presence(
                        activity=discord.Activity(
                            type=getattr(discord.ActivityType, status_type),
                            name=status_message,
                        )
                    )
                    continue
                if not command:
                    continue
                logger.info(f"Command '{command}' not found. Type 'help' for a list of commands.")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.playing, name="Loading...")
        )

        logger.info(f"{self.user} has connected to Discord!")

        # start the change_activity coroutine
        asyncio.create_task(self.change_activity())  # noqa: RUF006

        # start console coroutine
        asyncio.create_task(self.console())  # noqa: RUF006

        # connect to the database
        await db.connect()

    @commands.Cog.listener()
    async def on_disconnect(self) -> None:
        logger.warning("Bot has disconnected from Discord.")
        await db.disconnect()
        logger.warning("Database connection closed.")


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
