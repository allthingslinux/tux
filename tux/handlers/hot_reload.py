import importlib
import os
import sys
from pathlib import Path

from discord.ext import commands, tasks
from loguru import logger

from tux.bot import Tux


def path_from_extension(extension: str) -> Path:
    """Convert an extension notation to a file path."""
    base_dir = Path(__file__).parent.parent
    extension = extension.replace("tux.", "", 1)
    relative_path = extension.replace(".", os.sep) + ".py"

    return (base_dir / relative_path).resolve()


class HotReload(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.last_modified_time: dict[str, float] = {}

        # Track help.py separately
        self.help_file_path = Path(__file__).parent.parent / "help.py"
        self.last_help_modified_time = self.help_file_path.stat().st_mtime if self.help_file_path.exists() else 0

        self.hot_reload_loop.start()

    async def cog_unload(self) -> None:
        self.hot_reload_loop.stop()

    @tasks.loop(seconds=1.5)
    async def hot_reload_loop(self) -> None:
        """
        Loop to check for changes in extension files and reload them if modified.

        Parameters
        ----------
        self : HotReload
            The HotReload instance.
        """
        # First check help.py for changes
        await self._check_help_file()

        # Then check cog extensions
        for extension in list(self.bot.extensions.keys()):
            if extension == "jishaku":
                continue

            path: Path = path_from_extension(extension)

            try:
                modification_time: float = path.stat().st_mtime

            except FileNotFoundError:
                logger.error(f"File not found for extension {extension} at {path}")
                continue

            last_time = self.last_modified_time.get(extension)

            # Skip if we haven't seen this extension before or if it hasn't changed
            if last_time is None:
                self.last_modified_time[extension] = modification_time
                continue

            if last_time == modification_time:
                continue

            # Only update the time if we successfully reload
            try:
                await self.bot.reload_extension(extension)
                self.last_modified_time[extension] = modification_time
                logger.info(f"Reloaded {extension}")

            except commands.ExtensionNotLoaded:
                pass

            except commands.ExtensionError as e:
                logger.error(f"Failed to reload extension {extension}: {e}")

    async def _check_help_file(self) -> None:
        """Check if help.py has changed and reload the help command if needed."""
        try:
            if not self.help_file_path.exists():
                logger.warning(f"Help file does not exist at {self.help_file_path}")
                return

            # If the file hasn't changed, skip
            current_mod_time = self.help_file_path.stat().st_mtime
            if current_mod_time <= self.last_help_modified_time:
                return

            # File has changed, reload the module and update the help command
            try:
                # Force reload of the help module
                if "tux.help" in sys.modules:
                    logger.debug("Reloading tux.help module")
                    importlib.reload(sys.modules["tux.help"])

                else:
                    logger.debug("Importing tux.help module for the first time")
                    importlib.import_module("tux.help")

                # Import the freshly reloaded module
                from tux.help import TuxHelp

                # Reset the help command with a new instance from the reloaded module
                self.bot.help_command = TuxHelp()
                self.last_help_modified_time = current_mod_time
                logger.info("Reloaded help command")

            except Exception as e:
                logger.error(f"Failed to reload help command: {e}")
                import traceback

                logger.error(traceback.format_exc())

        except Exception as e:
            logger.error(f"Error checking help file: {e}")

    @hot_reload_loop.before_loop
    async def cache_last_modified_time(self) -> None:
        """
        Cache the last modified time of all extensions before the loop starts.

        Parameters
        ----------
        self : HotReload
            The HotReload instance.
        """

        for extension in self.bot.extensions:
            if extension == "jishaku":
                continue

            path: Path = path_from_extension(extension)

            try:
                modification_time: float = path.stat().st_mtime
                self.last_modified_time[extension] = modification_time

            except FileNotFoundError:
                logger.error(f"File not found for extension {extension} at {path}")


async def setup(bot: Tux) -> None:
    await bot.add_cog(HotReload(bot))
