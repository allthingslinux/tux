import asyncio
import time
import traceback
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

import aiofiles
import aiofiles.os
import sentry_sdk
from discord.ext import commands
from loguru import logger

from core.config import CONFIG
from infra.sentry import safe_set_name, span, start_span, transaction


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
            "services": 90,
            "admin": 80,
            "levels": 70,
            "moderation": 60,
            "snippets": 50,
            "guild": 40,
            "utility": 30,
            "info": 20,
            "fun": 10,
            "tools": 5,
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

    @span("cog.load_single")
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

        # Setup for Sentry tracing
        cog_name = path.stem

        # Add span tags for the current cog
        if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
            current_span.set_tag("cog.name", cog_name)
            current_span.set_tag("cog.path", str(path))

        try:
            # Get the path relative to the project root
            project_root = Path(__file__).parent.parent
            relative_path = path.relative_to(project_root)

            # Convert path to module format (e.g., modules.admin.dev, infra.handlers.error)
            module = str(relative_path).replace("/", ".").replace("\\", ".")[:-3]

            if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
                current_span.set_tag("cog.module", module)

            # Check if this module or any parent module is already loaded
            # This prevents duplicate loading of the same module
            module_parts = module.split(".")

            for i in range(len(module_parts), 1, -1):
                check_module = ".".join(module_parts[:i])
                if check_module in self.bot.extensions:
                    logger.warning(f"Skipping {module} as {check_module} is already loaded")
                    if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
                        current_span.set_tag("cog.status", "skipped")
                        current_span.set_tag("cog.skip_reason", "already_loaded")
                        current_span.set_data("already_loaded_module", check_module)
                    return

            # Actually load the extension
            await self.bot.load_extension(name=module)
            load_time = time.perf_counter() - start_time
            self.load_times[module] = load_time

            # Add telemetry data to span
            if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
                current_span.set_tag("cog.status", "loaded")
                current_span.set_data("load_time_ms", load_time * 1000)
                current_span.set_data("load_time_s", load_time)

            logger.debug(f"Successfully loaded cog {module} in {load_time * 1000:.0f}ms")

        except Exception as e:
            if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
                current_span.set_status("internal_error")
                current_span.set_tag("cog.status", "failed")
                current_span.set_data("error", str(e))
                current_span.set_data("traceback", traceback.format_exc())

            module_name = str(path)
            error_msg = f"Failed to load cog {module_name}. Error: {e}\n{traceback.format_exc()}"
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

    @span("cog.load_group")
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

        # Add basic info for the group
        if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
            current_span.set_data("cog_count", len(cogs))

            if categories := {cog.parent.name for cog in cogs if cog.parent}:
                current_span.set_data("categories", list(categories))

        # Track cog group loading
        start_time = time.perf_counter()
        results = await asyncio.gather(*[self._load_single_cog(cog) for cog in cogs], return_exceptions=True)
        end_time = time.perf_counter()

        # Calculate success/failure rates
        success_count = len([r for r in results if not isinstance(r, Exception)])
        failure_count = len(results) - success_count

        if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
            current_span.set_data("load_time_s", end_time - start_time)
            current_span.set_data("success_count", success_count)
            current_span.set_data("failure_count", failure_count)

        # Log failures with proper context
        for result, cog in zip(results, cogs, strict=False):
            if isinstance(result, Exception):
                logger.error(f"Error loading {cog}: {result}")

    async def _process_single_file(self, path: Path) -> None:
        """Process a single file path."""
        if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
            current_span.set_tag("path.is_dir", False)
        if await self.is_cog_eligible(path):
            await self._load_single_cog(path)

    async def _process_directory(self, path: Path) -> None:
        """Process a directory of cogs."""
        if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
            current_span.set_tag("path.is_dir", True)

        # Collect and sort eligible cogs by priority
        cog_paths: list[tuple[int, Path]] = [
            (self._get_cog_priority(item), item) for item in path.rglob("*.py") if await self.is_cog_eligible(item)
        ]
        cog_paths.sort(key=lambda x: x[0], reverse=True)

        if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
            current_span.set_data("eligible_cog_count", len(cog_paths))

            # Priority groups info for observability
            priority_groups: dict[int, int] = {}
            for priority, _ in cog_paths:
                if priority in priority_groups:
                    priority_groups[priority] += 1
                else:
                    priority_groups[priority] = 1
            current_span.set_data("priority_groups", priority_groups)

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
        if current_group:
            await self._load_cog_group(current_group)

    @span("cog.load_path")
    async def load_cogs(self, path: Path) -> None:
        """
        Recursively loads eligible cogs from the specified directory with concurrent loading.

        Parameters
        ----------
        path : Path
            The path to the directory containing cogs.
        """
        # Add span context
        if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
            current_span.set_tag("cog.path", str(path))

        try:
            # Handle file vs directory paths differently
            if not await aiofiles.os.path.isdir(path):
                await self._process_single_file(path)
            else:
                await self._process_directory(path)

        except Exception as e:
            path_str = path.as_posix()
            logger.error(f"An error occurred while processing {path_str}: {e}")

            if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
                current_span.set_status("internal_error")
                current_span.set_data("error", str(e))
                current_span.set_data("traceback", traceback.format_exc())

            raise CogLoadError(CogLoadError.FAILED_TO_LOAD) from e

    @transaction("cog.load_folder", description="Loading all cogs from folder")
    async def load_cogs_from_folder(self, folder_name: str) -> None:
        """
        Loads cogs from the specified folder with timing.

        Parameters
        ----------
        folder_name : str
            The name of the folder containing the cogs.
        """
        # Add span info
        if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
            current_span.set_tag("cog.folder", folder_name)
            # Use safe_set_name instead of direct set_name call
            safe_set_name(current_span, f"Load Cogs: {folder_name}")

        start_time = time.perf_counter()
        cog_path: Path = Path(__file__).parent.parent / folder_name

        if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
            current_span.set_data("full_path", str(cog_path))

        try:
            await self.load_cogs(path=cog_path)
            load_time = time.perf_counter() - start_time

            if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
                current_span.set_data("load_time_s", load_time)
                current_span.set_data("load_time_ms", load_time * 1000)

            if load_time:
                logger.info(f"Loaded all cogs from {folder_name} in {load_time * 1000:.0f}ms")

                # Log individual cog load times for performance monitoring
                slow_threshold = 1.0  # seconds
                if slow_cogs := {k: v for k, v in self.load_times.items() if v > slow_threshold}:
                    if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
                        current_span.set_data("slow_cogs", slow_cogs)
                    logger.warning(f"Slow loading cogs (>{slow_threshold * 1000:.0f}ms): {slow_cogs}")

        except Exception as e:
            if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
                current_span.set_status("internal_error")
                current_span.set_data("error", str(e))
                current_span.set_data("traceback", traceback.format_exc())

            logger.error(f"Failed to load cogs from folder {folder_name}: {e}")
            raise CogLoadError(CogLoadError.FAILED_TO_LOAD_FOLDER) from e

    @classmethod
    @transaction("cog.setup", name="CogLoader Setup", description="Initialize CogLoader and load all cogs")
    async def setup(cls, bot: commands.Bot) -> None:
        """
        Set up the cog loader and load all cogs.

        Parameters
        ----------
        bot : commands.Bot
            The bot instance.
        """
        if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
            current_span.set_tag("bot.id", bot.user.id if bot.user else "unknown")

        start_time = time.perf_counter()
        cog_loader = cls(bot)

        try:
            # Load infrastructure handlers first (they have highest priority)
            with start_span("cog.load_handlers", "Load infrastructure handler cogs"):
                await cog_loader.load_cogs_from_folder(folder_name="infra/handlers")

            # Then load official modules
            with start_span("cog.load_modules", "Load official modules"):
                await cog_loader.load_cogs_from_folder(folder_name="modules")

            # Finally, load custom modules (if any)
            with start_span("cog.load_custom_modules", "Load custom modules"):
                await cog_loader.load_cogs_from_folder(folder_name="custom_modules")

            total_time = time.perf_counter() - start_time

            if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
                current_span.set_data("total_load_time_s", total_time)
                current_span.set_data("total_load_time_ms", total_time * 1000)

            # Add the CogLoader itself as a cog for bot maintenance
            with start_span("cog.register_loader", "Register CogLoader cog"):
                await bot.add_cog(cog_loader)

            logger.info(f"Total cog loading time: {total_time * 1000:.0f}ms")

        except Exception as e:
            if sentry_sdk.is_initialized() and (current_span := sentry_sdk.get_current_span()):
                current_span.set_status("internal_error")
                current_span.set_data("error", str(e))
                current_span.set_data("traceback", traceback.format_exc())

            logger.error(f"Failed to set up cog loader: {e}")
            raise CogLoadError(CogLoadError.FAILED_TO_INITIALIZE) from e
