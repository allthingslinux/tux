import logging
import os

import colorlog
from discord.ext import commands


class TuxLogger(logging.Logger):
    def __init__(self, name, project_logging_level=logging.INFO):
        super().__init__(name, level=project_logging_level)
        self._setup_logging()

    def _setup_logging(self):
        log_format = (
            "%(asctime)s [%(log_color)s%(levelname)s%(reset)s] [%(name)s]: %(message)s"
        )
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        handler = colorlog.StreamHandler()
        handler.setFormatter(colorlog.ColoredFormatter(log_format))
        self.addHandler(handler)

        file_handler = logging.FileHandler(os.path.join(log_dir, "bot.log"), mode="a")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"),
        )
        self.addHandler(file_handler)

    def _log_to_file(self, level, message, caller_module):
        file_handler = logging.FileHandler(
            os.path.join("logs", f"{caller_module}.log"),
            mode="a",
        )
        file_handler.setFormatter(
            logging.Formatter(
                f"%(asctime)s [%(levelname)s] [{caller_module}]: %(message)s",
            ),
        )
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


class LoggingCog(commands.Cog):
    def __init__(self, bot, discord_logging_level=logging.WARNING):
        self.bot = bot
        self.discord_logging_level = discord_logging_level

        discord_logger = logging.getLogger("discord")
        discord_logger.setLevel(self.discord_logging_level)


logger = TuxLogger(__name__)


async def setup(
    bot,
    project_logging_level=logging.DEBUG,
    discord_logging_level=logging.WARNING,
):
    global logger
    log_cog = LoggingCog(bot, discord_logging_level)
    logger.setLevel(project_logging_level)
    await bot.add_cog(log_cog)
