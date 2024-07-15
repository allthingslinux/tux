# utils/tux_logger.py

"""
# TuxLogger Documentation

## Usage Instructions

Hey contributor, Ty here! To use the logger in your cog files, please follow these steps:

1. Import the logger by adding the following line at the top of your main bot file:

    ```python
    from your_module_name import logger
    ```

2. Once imported, you can use the logger to log messages in your code. For example:

    ```python
    logger.info("This is an information message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.debug("This is a debug message.")
    ```

### Logger setup

```python
    async def setup(bot,
        project_logging_level=logging.DEBUG,
        discord_logging_level=logging.WARNING):
```

1. bot: The Discord bot instance.
1. project_logging_level: The logging level for the project (default is DEBUG).
1. discord_logging_level: The logging level for the Discord library (default is WARNING).

I love you all and thank you for contributing <3
"""  # noqa E501

import logging
import os

import colorlog
import discord
from discord.ext import commands


class TuxLogger(logging.Logger):
    LOG_DIR = "logs"

    def __init__(self, name: str, project_logging_level: int = logging.INFO):
        super().__init__(name, level=project_logging_level)
        self.setup_logging()

    def setup_logging(self):
        """
        Setup logging configuration.
        """
        log_format = "%(asctime)s [%(log_color)s%(levelname)s%(reset)s] [%(name)s]: %(" "message)s"

        os.makedirs(self.LOG_DIR, exist_ok=True)

        # Stream handler with color formatting
        handler = colorlog.StreamHandler()
        handler.setFormatter(colorlog.ColoredFormatter(log_format))

        # File handler for general logs
        file_name = os.path.join(self.LOG_DIR, "bot.log")
        file_handler = self._create_file_handler(file_name)

        self.addHandler(handler)
        self.addHandler(file_handler)

    def _create_file_handler(self, filename: str) -> logging.FileHandler:
        """
        Create a file handler.

        Args:
            filename (str): Filename for the log file.

        Returns
            logging.FileHandler: A file handler object.
        """
        file_handler = logging.FileHandler(filename, mode="a")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s]: %(message)s")
        )
        return file_handler

    def _log_to_file(self, level: int, message: str, caller_module: str):
        """
        Log to a file.

        Args:
            level (int): Level of the log.
            message (str): Log message.
            caller_module (str): Module where the log was triggered.
        """
        file_name = os.path.join(self.LOG_DIR, f"{caller_module}.log")
        file_handler = self._create_file_handler(file_name)

        self.addHandler(file_handler)
        self.log(level, message)
        self.removeHandler(file_handler)

    def debug(self, message, filename="unknown"):
        self._log_to_file(logging.DEBUG, message, filename)

    def info(self, message, filename="unknown"):
        self._log_to_file(logging.INFO, message, filename)

    def warning(self, message, filename="unknown"):
        self._log_to_file(logging.WARNING, message, filename)

    def error(self, message, filename="unknown"):
        self._log_to_file(logging.ERROR, message, filename)

    def critical(self, message, filename="unknown"):
        self._log_to_file(logging.CRITICAL, message, filename)

    def audit(
        self,
        bot: commands.Bot,
        title: str,
        description: str,
        color: int | discord.Colour = 0x7289DA,
        fields: list[tuple[str, str, bool]] | None = None,
        thumbnail_url: str | None = None,
        image_url: str | None = None,
        author_name: str | None = None,
        author_url: str | None = None,
        author_icon_url: str | None = None,
        footer_text: str | None = None,
        footer_icon_url: str | None = None,
    ):
        audit_log_channel_id = 1191472088695980083
        channel = bot.get_channel(audit_log_channel_id)
        if not isinstance(channel, discord.TextChannel):
            self.error(f"Failed to send audit message: Channel '{channel}' is not a text channel.")
            return
        embed = discord.Embed(title=title, description=description, color=color)

        # Add fields to embed
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

        # Set thumbnail and image
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
        if image_url:
            embed.set_image(url=image_url)

        # Set author details
        if author_name:
            embed.set_author(name=author_name, url=author_url, icon_url=author_icon_url)

        # Set footer details
        if footer_text:
            embed.set_footer(text=footer_text, icon_url=footer_icon_url)

        bot.loop.create_task(channel.send(embed=embed))


class LoggingCog(commands.Cog):
    def __init__(self, bot, discord_logging_level=logging.WARNING):
        self.bot = bot
        discord_logger = logging.getLogger("discord")
        discord_logger.setLevel(discord_logging_level)


logger = TuxLogger(__name__)


async def setup(bot, project_logging_level=logging.DEBUG, discord_logging_level=logging.WARNING):
    global logger
    log_cog = LoggingCog(bot, discord_logging_level)
    logger.setLevel(project_logging_level)
    await bot.add_cog(log_cog)
