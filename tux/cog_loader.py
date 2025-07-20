"""
CogLoader: A robust cog loader for the Tux bot.

This module provides the `CogLoader` class, which is responsible for discovering,
loading, and managing all cogs (Discord.py extensions) for the bot. It includes
features for priority-based loading, performance tracking, and detailed error
reporting with Sentry integration.
"""

from __future__ import annotations

import time
from collections import defaultdict
from itertools import groupby
from pathlib import Path

from discord.ext import commands
from loguru import logger

from tux.utils.config import CONFIG
from tux.utils.tracing import (
    capture_span_exception,
    enhanced_span,
    set_span_attributes,
    span,
    transaction,
)


class CogLoadError(Exception):
    """Raised when a cog fails to load."""


class CogLoadResult:
    """
    Encapsulates the result of a cog loading operation.

    Attributes
    ----------
    module : str
        The full import path of the cog.
    success : bool
        Whether the cog loaded successfully.
    load_time : float
        The time taken to load the cog, in seconds.
    error : Exception | None
        The exception raised during loading, if any.
    """

    def __init__(self, module: str, success: bool, load_time: float, error: Exception | None = None) -> None:
        self.module = module
        self.success = success
        self.load_time = load_time
        self.error = error

    @property
    def load_time_ms(self) -> float:
        """
        Return the cog load time in milliseconds.

        Returns
        -------
        float
            The load time in milliseconds.
        """
        return self.load_time * 1000


class CogLoader(commands.Cog):
    """
    A robust cog loader with priority-based loading, performance tracking,
    and detailed Sentry integration.
    """

    # --- Initialization ---

    def __init__(self, bot: commands.Bot) -> None:
        """
        Initializes the CogLoader.

        Parameters
        ----------
        bot : commands.Bot
            The bot instance.
        """
        self.bot = bot
        self.cog_ignore_list: set[str] = set(CONFIG.COG_IGNORE_LIST)
        self.load_times: defaultdict[str, float] = defaultdict(float)
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

    # --- Cog Discovery & Metadata ---

    @staticmethod
    def _path_to_module(path: Path) -> str:
        """
        Converts a Path object to a Python module path.

        Example:
            tux/cogs/admin.py -> tux.cogs.admin

        Parameters
        ----------
        path : Path
            The file path to convert.

        Returns
        -------
        str
            The Python module import path.
        """
        return ".".join(path.parts).removesuffix(".py")

    def _is_eligible_cog_file(self, filepath: Path) -> bool:
        """
        Checks if a file is an eligible cog for loading.

        Parameters
        ----------
        filepath : Path
            The path to the file to check.

        Returns
        -------
        bool
            True if the file is an eligible cog, False otherwise.
        """
        if filepath.suffix != ".py" or not filepath.is_file() or filepath.stem.startswith("_"):
            return False

        cog_name = filepath.stem
        if cog_name in self.cog_ignore_list:
            logger.trace(f"Skipping {cog_name} as it is in the ignore list.")
            return False

        return True

    def _get_cog_priority(self, path: Path) -> int:
        """
        Gets the loading priority for a cog based on its parent directory.

        Parameters
        ----------
        path : Path
            The path to the cog file.

        Returns
        -------
        int
            The priority value, or 0 if not specified.
        """
        return self.load_priorities.get(path.parent.name, 0)

    def _discover_and_sort_cogs(self, path: Path) -> list[Path]:
        """
        Discovers all eligible cogs in a directory and sorts them by priority.

        Parameters
        ----------
        path : Path
            The directory to search for cogs.

        Returns
        -------
        list[Path]
            A list of cog file paths, sorted by priority (descending).
        """
        if not path.is_dir():
            return []

        eligible_cogs = [f for f in path.rglob("*.py") if self._is_eligible_cog_file(f)]
        return sorted(eligible_cogs, key=lambda p: (self._get_cog_priority(p), p.name), reverse=True)

    def _create_load_result(
        self,
        path: Path,
        start_time: float,
        success: bool = True,
        error: Exception | None = None,
    ) -> CogLoadResult:
        """
        Creates a standardized CogLoadResult object.

        Parameters
        ----------
        path : Path
            The path to the cog file.
        start_time : float
            The time when the loading process started.
        success : bool, optional
            Whether the load was successful, by default True.
        error : Exception | None, optional
            The error that occurred, if any, by default None.

        Returns
        -------
        CogLoadResult
            The result object.
        """
        module = self._path_to_module(path)
        load_time = time.perf_counter() - start_time
        return CogLoadResult(module, success, load_time, error)

    # --- Cog Operations ---

    @span("cog.load_single")
    async def _load_single_cog(self, path: Path) -> CogLoadResult:
        """
        Loads a single cog with comprehensive error handling and timing.

        Parameters
        ----------
        path : Path
            The path to the cog file to load.

        Returns
        -------
        CogLoadResult
            The result of the loading operation.

        Raises
        ------
        CogLoadError
            If the cog fails to load.
        """
        start_time = time.perf_counter()
        module = self._path_to_module(path)
        cog_name = path.stem

        set_span_attributes({"cog.name": cog_name, "cog.path": str(path), "cog.module": module})

        try:
            await self.bot.load_extension(module)
        except Exception as e:
            result = self._create_load_result(path, start_time, success=False, error=e)
            capture_span_exception(e, cog_status="failed", cog_name=cog_name, cog_module=module)
            error_msg = f"Failed to load cog {module}."
            logger.error(f"{error_msg} Error: {e}")
            raise CogLoadError(error_msg) from e
        else:
            result = self._create_load_result(path, start_time)
            self.load_times[module] = result.load_time
            set_span_attributes({"cog.status": "loaded", "load_time_ms": result.load_time_ms})
            logger.debug(f"Successfully loaded cog {module} in {result.load_time_ms:.2f}ms")
            return result

    @span("cog.unload_single")
    async def _unload_single_cog(self, path: Path) -> bool:
        """
        Unloads a single cog with enhanced tracing.

        Parameters
        ----------
        path : Path
            The path to the cog file to unload.

        Returns
        -------
        bool
            True if the cog was unloaded successfully, False otherwise.
        """
        module = self._path_to_module(path)
        set_span_attributes({"cog.module": module})

        try:
            await self.bot.unload_extension(module)
        except commands.ExtensionNotLoaded:
            logger.warning(f"Cog {module} is not loaded, cannot unload.")
            return False
        except Exception as e:
            capture_span_exception(e, operation="unload", cog_module=module)
            logger.error(f"Failed to unload cog {module}: {e}")
            return False
        else:
            logger.info(f"Successfully unloaded cog: {module}")
            return True

    @span("cog.reload_single")
    async def reload_cog(self, path: Path) -> bool:
        """
        Reloads a single cog with comprehensive error handling.

        Parameters
        ----------
        path : Path
            The path to the cog file to reload.

        Returns
        -------
        bool
            True if the cog was reloaded successfully, False otherwise.
        """
        module = self._path_to_module(path)
        set_span_attributes({"cog.module": module})

        await self._unload_single_cog(path)

        try:
            await self._load_single_cog(path)
        except CogLoadError:
            return False
        else:
            logger.info(f"Successfully reloaded cog: {module}")
            return True

    # --- Loading Workflow ---

    @span("cog.load_directory")
    async def _load_cogs_from_directory(self, path: Path) -> list[CogLoadResult]:
        """
        Discovers, groups, and loads all eligible cogs from a directory.

        Cogs are loaded by priority groups in descending order. Within each priority
        group, cogs are loaded sequentially to prevent race conditions and dependency
        issues. If a cog fails to load within a priority group, the remaining cogs
        in that group are skipped to prevent cascading failures.

        Parameters
        ----------
        path : Path
            The directory to load cogs from.

        Returns
        -------
        list[CogLoadResult]
            A list of results for each cog loaded.
        """
        eligible_cogs = self._discover_and_sort_cogs(path)
        if not eligible_cogs:
            return []

        set_span_attributes({"eligible_cog_count": len(eligible_cogs)})

        all_results: list[CogLoadResult] = []
        cogs_by_priority = groupby(eligible_cogs, key=self._get_cog_priority)

        for priority, cogs in cogs_by_priority:
            cogs_to_load = list(cogs)
            with enhanced_span("cog.load_priority_group", f"Loading priority {priority} cogs", priority=priority):
                categories = {cog.parent.name for cog in cogs_to_load}
                set_span_attributes({"cog_count": len(cogs_to_load), "categories": list(categories)})

                start_time = time.perf_counter()
                # Load cogs sequentially within priority group to avoid dependency issues
                # This prevents race conditions that could occur if cogs within the same
                # priority group depend on each other during import/initialization
                group_results: list[CogLoadResult] = []
                for cog in cogs_to_load:
                    try:
                        result = await self._load_single_cog(cog)
                        group_results.append(result)
                    except CogLoadError as e:
                        # Create a failed result for tracking
                        failed_result = self._create_load_result(cog, start_time, success=False, error=e)
                        group_results.append(failed_result)
                        # Stop loading remaining cogs in this priority group to prevent
                        # cascading failures from dependency issues
                        logger.warning(f"Skipping remaining cogs in priority {priority} due to failure: {e}")
                        break

                all_results.extend(group_results)

                set_span_attributes(
                    {
                        "load_time_s": time.perf_counter() - start_time,
                        "success_count": len([r for r in group_results if r.success]),
                        "failure_count": len([r for r in group_results if not r.success]),
                    },
                )
        return all_results

    @span("cog.load_path")
    async def load_cogs(self, path: Path) -> list[CogLoadResult]:
        """
        Recursively loads eligible cogs from a directory or a single file.

        Parameters
        ----------
        path : Path
            The path to the file or directory to load cogs from.

        Returns
        -------
        list[CogLoadResult]
            A list of results for each cog loaded.

        Raises
        ------
        FileNotFoundError
            If the specified path does not exist.
        CogLoadError
            If a fatal error occurs during the loading process.
        """
        set_span_attributes({"cog.path": str(path)})

        if not path.exists():
            logger.error(f"Cog path not found: {path}")
            msg = f"Cog path not found: {path}"
            raise FileNotFoundError(msg)

        try:
            if path.is_dir():
                return await self._load_cogs_from_directory(path)
            if self._is_eligible_cog_file(path):
                return [await self._load_single_cog(path)]
        except Exception as e:
            capture_span_exception(e, path=str(path), operation="load_cogs")
            logger.error(f"An error occurred while processing {path.as_posix()}: {e}")
            msg = f"Failed to load from {path.as_posix()}"
            raise CogLoadError(msg) from e

        logger.debug(f"Path {path} is not an eligible cog file or directory.")
        return []

    @transaction("cog.load_folder", description="Loading all cogs from a folder")
    async def load_cogs_from_folder(self, folder_name: str) -> list[CogLoadResult]:
        """
        Loads all cogs from a specified top-level folder.

        Parameters
        ----------
        folder_name : str
            The name of the folder to load cogs from (e.g., "tux/cogs").

        Returns
        -------
        list[CogLoadResult]
            A list of results for each cog loaded.

        Raises
        ------
        CogLoadError
            Propagates errors from the underlying `load_cogs` call.
        """
        cog_path = Path(folder_name)
        with enhanced_span("cog.folder_processing", f"Processing {folder_name}", folder=folder_name):
            start_time = time.perf_counter()
            try:
                results = await self.load_cogs(path=cog_path)
            except FileNotFoundError as e:
                # Handle missing folders gracefully but log as error for visibility
                capture_span_exception(e, folder=folder_name, operation="load_folder")
                logger.error(f"Cog folder not found: {folder_name} - {e}")
                return []
            except CogLoadError as e:
                capture_span_exception(e, folder=folder_name, operation="load_folder")
                logger.error(f"Failed to load cogs from folder {folder_name}: {e}")
                raise
            else:
                load_time = time.perf_counter() - start_time
                success_count = sum(r.success for r in results)
                logger.info(
                    f"Loaded {success_count}/{len(results)} cogs from {folder_name} in {load_time * 1000:.2f}ms",
                )
                return results

    # --- Setup ---

    @classmethod
    @transaction("cog.setup", name="CogLoader Setup", description="Initialize and load all cogs")
    async def setup(cls, bot: commands.Bot) -> CogLoader:
        """
        Sets up the cog loader and loads all initial cogs for the bot.

        Parameters
        ----------
        bot : commands.Bot
            The bot instance to set up.

        Returns
        -------
        CogLoader
            The initialized CogLoader instance.

        Raises
        ------
        CogLoadError
            If a fatal error occurs during the setup process.
        """
        with enhanced_span("cog.loader_init", "Initializing CogLoader", bot_id=bot.user.id if bot.user else "unknown"):
            start_time = time.perf_counter()
            cog_loader = cls(bot)
            cog_folders = ["tux/handlers", "tux/cogs", "tux/extensions"]
            try:
                all_results: list[CogLoadResult] = []
                for folder in cog_folders:
                    folder_results = await cog_loader.load_cogs_from_folder(folder_name=folder)
                    all_results.extend(folder_results)
                total_time = time.perf_counter() - start_time
                total_cogs = len(all_results)
                successful_cogs = sum(r.success for r in all_results)
                logger.info(
                    f"Cog loading complete: {successful_cogs}/{total_cogs} cogs loaded in {total_time * 1000:.2f}ms",
                )
            except Exception as e:
                capture_span_exception(e, operation="cog_setup")
                logger.opt(exception=e).critical("Failed to set up cog loader.")
                msg = "Failed to initialize CogLoader"
                raise CogLoadError(msg) from e
            else:
                await bot.add_cog(cog_loader)
                return cog_loader
