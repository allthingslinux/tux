import asyncio
import time
import traceback
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

import aiofiles
import aiofiles.os
from discord.ext import commands
from loguru import logger

from tux.utils.config import CONFIG


class CogLoadError(Exception):
    """Raised when a cog fails to load."""

    FAILED_TO_LOAD = "Failed to load cogs"
    FAILED_TO_LOAD_FOLDER = "Failed to load cogs from folder"
    FAILED_TO_INITIALIZE = "Failed to initialize cog loader"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class CogLoader(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.cog_ignore_list: set[str] = CONFIG.COG_IGNORE_LIST
        # Track load times for performance monitoring
        self.load_times: defaultdict[str, float] = defaultdict(float)
        # Define load order priorities (higher number = higher priority)
        self.load_priorities = {
            "handlers": 100,
            "admin": 90,
            "services": 80,
            "levels": 70,
            "moderation": 60,
            "guild": 50,
            "utility": 40,
            "info": 30,
            "fun": 20,
        }

    async def is_cog_eligible(self, filepath: Path) -> bool:
        """
        Checks if the specified file is an eligible cog.

        Parameters
        ----------
        filepath : Path
            The path to the file to check.

        Returns
        -------
        bool
            True if the file is an eligible cog, False otherwise.
        """
        cog_name: str = filepath.stem

        if cog_name in self.cog_ignore_list:
            logger.warning(f"Skipping {cog_name} as it is in the ignore list.")
            return False

        return filepath.suffix == ".py" and not cog_name.startswith("_") and await aiofiles.os.path.isfile(filepath)

    async def _load_single_cog(self, path: Path) -> None:
        """
        Load a single cog with timing and error tracking.

        Parameters
        ----------
        path : Path
            The path to the cog to load.

        Raises
        ------
        CogLoadError
            If the cog fails to load.
        """
        start_time = time.perf_counter()
        relative_path: Path = path.relative_to(Path(__file__).parent)
        module: str = str(relative_path).replace("/", ".").replace("\\", ".")[:-3]

        try:
            await self.bot.load_extension(name=module)
            load_time = time.perf_counter() - start_time
            self.load_times[module] = load_time
            logger.debug(f"Successfully loaded cog {module} in {load_time * 1000:.0f}ms")

        except Exception as e:
            error_msg = f"Failed to load cog {module}. Error: {e}\n{traceback.format_exc()}"
            logger.error(error_msg)
            raise CogLoadError(error_msg) from e

    def _get_cog_priority(self, path: Path) -> int:
        """
        Get the loading priority for a cog based on its category.

        Parameters
        ----------
        path : Path
            The path to the cog.

        Returns
        -------
        int
            The priority value (higher = loaded earlier)
        """
        return self.load_priorities.get(path.parent.name, 0)

    async def _load_cog_group(self, cogs: Sequence[Path]) -> None:
        """
        Load a group of cogs concurrently.

        Parameters
        ----------
        cogs : Sequence[Path]
            The cogs to load.
        """
        if not cogs:
            return

        results = await asyncio.gather(*[self._load_single_cog(cog) for cog in cogs], return_exceptions=True)
        for result, cog in zip(results, cogs, strict=False):
            if isinstance(result, Exception):
                logger.error(f"Error loading {cog}: {result}")

    async def load_cogs(self, path: Path) -> None:
        """
        Recursively loads eligible cogs from the specified directory with concurrent loading.

        Parameters
        ----------
        path : Path
            The path to the directory containing cogs.
        """
        try:
            if not await aiofiles.os.path.isdir(path):
                if await self.is_cog_eligible(path):
                    await self._load_single_cog(path)
                return

            # Collect and sort eligible cogs by priority
            cog_paths: list[tuple[int, Path]] = [
                (self._get_cog_priority(item), item) for item in path.rglob("*.py") if await self.is_cog_eligible(item)
            ]
            cog_paths.sort(key=lambda x: x[0], reverse=True)

            # Group and load cogs by priority
            current_group: list[Path] = []
            current_priority: int | None = None

            for priority, cog_path in cog_paths:
                if current_priority != priority and current_group:
                    await self._load_cog_group(current_group)
                    current_group = []
                current_priority = priority
                current_group.append(cog_path)

            # Load final group
            await self._load_cog_group(current_group)

        except Exception as e:
            path_str = path.as_posix()
            logger.error(f"An error occurred while processing {path_str}: {e}")
            raise CogLoadError(CogLoadError.FAILED_TO_LOAD) from e

    async def load_cogs_from_folder(self, folder_name: str) -> None:
        """
        Loads cogs from the specified folder with timing.

        Parameters
        ----------
        folder_name : str
            The name of the folder containing the cogs.
        """
        start_time = time.perf_counter()
        cog_path: Path = Path(__file__).parent / folder_name

        try:
            await self.load_cogs(path=cog_path)
            if load_time := time.perf_counter() - start_time:
                logger.info(f"Loaded all cogs from {folder_name} in {load_time * 1000:.0f}ms")

                # Log individual cog load times for performance monitoring
                slow_threshold = 1.0  # seconds
                if slow_cogs := {k: v for k, v in self.load_times.items() if v > slow_threshold}:
                    logger.warning(f"Slow loading cogs (>{slow_threshold * 1000:.0f}ms): {slow_cogs}")

        except Exception as e:
            logger.error(f"Failed to load cogs from folder {folder_name}: {e}")
            raise CogLoadError(CogLoadError.FAILED_TO_LOAD_FOLDER) from e

    @classmethod
    async def setup(cls, bot: commands.Bot) -> None:
        """
        Set up the cog loader and load all cogs.

        Parameters
        ----------
        bot : commands.Bot
            The bot instance.
        """
        start_time = time.perf_counter()
        cog_loader = cls(bot)

        try:
            # Load handlers first (they have highest priority)
            await cog_loader.load_cogs_from_folder(folder_name="handlers")
            # Then load regular cogs
            await cog_loader.load_cogs_from_folder(folder_name="cogs")

            total_time = time.perf_counter() - start_time
            logger.info(f"Total cog loading time: {total_time * 1000:.0f}ms")

            await bot.add_cog(cog_loader)

        except Exception as e:
            logger.error(f"Failed to set up cog loader: {e}")
            raise CogLoadError(CogLoadError.FAILED_TO_INITIALIZE) from e
