import os
from pathlib import Path

from discord.ext import commands, tasks
from loguru import logger

from tux.bot import Tux


def path_from_extension(extension: str) -> Path:
    """Convert an extension notation to a file path."""
    base_dir = Path(__file__).parent.parent
    relative_path = extension.replace(".", os.sep) + ".py"
    return (base_dir / relative_path).resolve()


class HotReload(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.last_modified_time: dict[str, float] = {}
        self.hot_reload_loop.start()

    async def cog_unload(self) -> None:
        self.hot_reload_loop.stop()

    @tasks.loop(seconds=3)
    async def hot_reload_loop(self) -> None:
        """Loop to check for changes in extension files and reload them if modified."""
        for extension in list(self.bot.extensions.keys()):
            if extension == "jishaku":
                continue

            path: Path = path_from_extension(extension)

            try:
                modification_time: float = path.stat().st_mtime
            except FileNotFoundError:
                logger.error(f"File not found for extension {extension} at {path}")
                continue

            if self.last_modified_time.get(extension) == modification_time:
                continue

            # Reload the extension if it has been modified
            self.last_modified_time[extension] = modification_time

            try:
                await self.bot.reload_extension(extension)
            except commands.ExtensionNotLoaded:
                pass
            except commands.ExtensionError as e:
                logger.error(f"Failed to reload extension {extension}: {e}")
            else:
                logger.info(f"Reloaded {extension}")

    @hot_reload_loop.before_loop
    async def cache_last_modified_time(self) -> None:
        """Cache the last modified time of all extensions before the loop starts."""
        for extension in self.bot.extensions:
            if extension == "jishaku":
                continue

            path: Path = path_from_extension(extension)

            try:
                modification_time: float = path.stat().st_mtime
            except FileNotFoundError:
                logger.error(f"File not found for extension {extension} at {path}")
                continue

            self.last_modified_time[extension] = modification_time


async def setup(bot: Tux) -> None:
    await bot.add_cog(HotReload(bot))
