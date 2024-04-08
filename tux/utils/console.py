import asyncio
import concurrent.futures
import os
import sys

import discord
from discord.ext.commands import Bot  # type: ignore
from loguru import logger

# TODO: Refactor this into a new CLI library


class Console:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.pool = concurrent.futures.ThreadPoolExecutor()

    def print_commands(self):
        logger.info("Available commands:")
        logger.info("help - Display this message")
        logger.info("send [channel_id] [message] - Send a message to a channel")
        logger.info("embedbuild - Build an embed to send to a channel")
        logger.info("setstatus - Set the bot's status")
        logger.info("exit - Stop the bot")

    async def get_input(self, message: str):
        return await asyncio.get_event_loop().run_in_executor(self.pool, input, message)

    async def send_message(self, command: str) -> None:
        command = command.split(" ")  # type: ignore

        if len(command) < 3:
            logger.error("Usage: send [channel_id] [message]")
            return

        channel_id, message = command[1], " ".join(command[2:])
        channel = self.bot.get_channel(int(channel_id))

        if channel is None or not isinstance(channel, discord.TextChannel):
            logger.error("Channel not found or is not a text channel.")
            return

        await channel.send(message)

    async def build_embed(self) -> None:
        title = await self.get_input("Title: ")
        description = ""
        while True:
            line = await self.get_input("Description (type 'DONE' when finish): ")
            if line == "DONE":
                break
            description += line + "\n"
        color = await self.get_input("Color (hex): ")
        channel_id = await self.get_input("Channel ID: ")

        if not color.startswith("#") or len(color) != 7:
            logger.error("Invalid color. Must be a valid hex color. Example: #ff0000")
            return

        embed = discord.Embed(title=title, description=description, color=int(color[1:], 16))

        channel = self.bot.get_channel(int(channel_id))
        if channel is None or not isinstance(channel, discord.TextChannel):
            logger.error("Channel not found or is not a text channel.")
            return

        await channel.send(embed=embed)

    async def set_status(self) -> None:
        status_type = await self.get_input(
            "Status type (watching, listening, playing, streaming): "
        )
        status_message = await self.get_input("Status message: ")

        if status_type == "streaming":
            stream_url = await self.get_input("Stream URL: ")
            await self.bot.change_presence(
                activity=discord.Streaming(name=status_message, url=stream_url)
            )
            return

        await self.bot.change_presence(
            activity=discord.Activity(
                type=getattr(discord.ActivityType, status_type),
                name=status_message,
            )
        )

    async def run_console(self) -> None:
        if not os.isatty(sys.stdin.fileno()):
            logger.info("Running in a non-interactive mode. Skipping console input.")
            return

        logger.info("Console is ready. Type 'help' for a list of commands.")

        commands = {
            "help": self.print_commands,
            "exit": self.bot.close,
            "send": self.send_message,
            "embedbuild": self.build_embed,
            "setstatus": self.set_status,
        }

        while True:
            command = await self.get_input(">>> ")

            try:
                command_func = commands[command.split(" ")[0]]
            except KeyError:
                logger.info(f"Command '{command}' not found. Type 'help' for a list of commands.")
                continue

            if command_func == self.bot.close:
                logger.info("Goodbye!")
                await command_func()  # type: ignore
                continue

            if asyncio.iscoroutinefunction(command_func):
                await command_func(command)
            else:
                command_func()  # type: ignore