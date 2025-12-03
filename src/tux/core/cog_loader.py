"""Dynamic cog loading system with priority-based ordering and telemetry.

This module provides the CogLoader class for discovery, validation, and loading
of bot cogs (extensions) from the filesystem. Supports priority-based loading
order for dependency management, concurrent loading within priority groups,
configuration error handling with graceful skipping, and performance monitoring
via Sentry. Follows discord.py's extension loading patterns.
"""

import ast
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

from tux.services.sentry import capture_exception_safe
from tux.services.sentry.metrics import record_cog_metric
from tux.services.sentry.tracing import (
    capture_span_exception,
    set_span_attributes,
    span,
)
from tux.shared.config import CONFIG
from tux.shared.constants import COG_PRIORITIES, MILLISECONDS_PER_SECOND
from tux.shared.exceptions import TuxCogLoadError, TuxConfigurationError

__all__ = ["CogLoader"]


class CogLoader(commands.Cog):
    """
    Dynamic cog loader with priority-based ordering and performance tracking.

    Manages the discovery, validation, and loading of bot cogs from the
    filesystem. Ensures proper load order based on priorities, handles
    configuration errors gracefully, and provides detailed telemetry.

    Attributes
    ----------
    bot : commands.Bot
        The bot instance cogs are loaded into.
    cog_ignore_list : set[str]
        Set of cog names to skip during loading (from configuration).
    load_times : defaultdict[str, float]
        Dictionary tracking load time for each cog (for performance monitoring).
    load_priorities : dict[str, int]
        Priority mapping for cog categories (higher = loads first).
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Initialize the cog loader with bot instance and configuration.

        Parameters
        ----------
        bot : commands.Bot
            The bot instance to load cogs into.
        """
        self.bot = bot

        # Load ignore list from configuration (cogs to skip)
        self.cog_ignore_list: set[str] = CONFIG.get_cog_ignore_list()

        # Track load times for performance monitoring and optimization
        self.load_times: defaultdict[str, float] = defaultdict(float)

        # Priority mapping determines load order (higher = loads first)
        self.load_priorities = COG_PRIORITIES

    async def is_cog_eligible(self, filepath: Path) -> bool:
        """
        Check if a file is eligible for loading as a cog.

        Validates that the file is not in the ignore list, is a Python file,
        doesn't start with underscore, and contains a valid extension setup function.

        Parameters
        ----------
        filepath : Path
            The path to the file to check.

        Returns
        -------
        bool
            True if the file passes basic eligibility checks, False otherwise.
        """
        cog_name: str = filepath.stem

        # Skip cogs explicitly ignored in configuration
        if cog_name in self.cog_ignore_list:
            logger.warning(f"Skipping {cog_name} as it is in the ignore list.")
            return False

        # Basic file validation: must be a .py file, not private (_), and exist
        if (
            filepath.suffix != ".py"
            or cog_name.startswith("_")
            or not await aiofiles.os.path.isfile(filepath)
        ):
            return False

        # Advanced validation: check if file contains a valid extension setup function
        return await self._contains_cog_or_extension(filepath)

    async def _contains_cog_or_extension(self, filepath: Path) -> bool:
        """
        Check if a Python file contains a valid extension setup function using AST.

        A valid extension file must contain an async setup(bot) function.

        Parameters
        ----------
        filepath : Path
            The path to the Python file to analyze.

        Returns
        -------
        bool
            True if the file contains a valid extension setup function, False otherwise.
        """
        try:
            async with aiofiles.open(filepath, encoding="utf-8") as f:
                content = await f.read()

            # Parse the AST
            tree = ast.parse(content, filename=str(filepath))

            # Check for extension setup function
            return any(
                isinstance(node, ast.AsyncFunctionDef)
                and node.name == "setup"
                and node.args.args
                for node in ast.walk(tree)
            )

        except (SyntaxError, UnicodeDecodeError, OSError) as e:
            logger.warning(f"Failed to parse {filepath} for cog validation: {e}")
            return False

    def _is_configuration_error(self, exception: Exception) -> bool:
        """
        Check if an exception is or contains a configuration error.

        Walks the exception chain to detect TuxConfigurationError anywhere in
        the cause/context chain. Handles both explicit (__cause__) and implicit
        (__context__) exception chaining.

        Parameters
        ----------
        exception : Exception
            The exception to check.

        Returns
        -------
        bool
            True if the exception chain contains a TuxConfigurationError.
        """
        current_exception = exception

        while current_exception:
            if isinstance(current_exception, TuxConfigurationError):
                return True
            # Follow both __cause__ (explicit) and __context__ (implicit) chains
            current_exception = (
                current_exception.__cause__ or current_exception.__context__
            )

        return False

    def _handle_configuration_skip(self, path: Path, error: Exception) -> None:
        """
        Log configuration error and mark cog as skipped in telemetry.

        Provides consistent logging for configuration errors, ensuring users
        receive clear guidance on how to enable the cog.

        Parameters
        ----------
        path : Path
            The path to the cog that was skipped.
        error : Exception
            The configuration error that caused the skip.
        """
        module_name = str(path)
        set_span_attributes(
            {"cog.status": "skipped", "cog.skip_reason": "configuration"},
        )
        logger.warning(
            f"Skipping cog {module_name} due to missing configuration: {error}",
        )
        logger.info(
            "To enable this cog, configure the required settings in your .env file",
        )

    def _resolve_module_path(self, path: Path) -> str:
        """
        Convert a file path to a Python module path.

        Strips the .py extension and converts path separators to dots.

        Parameters
        ----------
        path : Path
            The file path to convert.

        Returns
        -------
        str
            The Python module path (e.g., "tux.modules.admin.dev").

        Examples
        --------
        >>> loader._resolve_module_path(Path("tux/modules/admin/dev.py"))
        "tux.modules.admin.dev"
        """
        relative_path = path.relative_to(Path(__file__).parent.parent)
        return f"tux.{str(relative_path).replace('/', '.').replace('\\', '.')[:-3]}"

    def _is_duplicate_load(self, module: str) -> bool:
        """
        Check if a module or its parent is already loaded.

        Prevents duplicate loading of cogs and submodules. For example, if
        "tux.modules.admin" is loaded, this will return True for
        "tux.modules.admin.dev". Checks all parent modules in the path
        hierarchy to prevent conflicts with already-loaded extensions.

        Parameters
        ----------
        module : str
            The module path to check.

        Returns
        -------
        bool
            True if the module or any parent module is already loaded.
        """
        module_parts = module.split(".")

        # Check each parent module level (from full path down to root)
        for i in range(len(module_parts), 1, -1):
            check_module = ".".join(module_parts[:i])
            if check_module in self.bot.extensions:
                logger.warning(f"Skipping {module} as {check_module} is already loaded")
                set_span_attributes(
                    {
                        "cog.status": "skipped",
                        "cog.skip_reason": "already_loaded",
                        "already_loaded_module": check_module,
                    },
                )
                return True

        return False

    @span("cog.load_single")
    async def _load_single_cog(self, path: Path) -> None:
        """
        Load a single cog with timing, error tracking, and telemetry.

        Orchestrates the complete loading process: resolves module path, checks
        for duplicate loading, loads the extension via discord.py, records timing
        metrics, and handles configuration errors gracefully. Configuration errors
        are handled gracefully and logged as warnings rather than failures.

        Parameters
        ----------
        path : Path
            The path to the cog file to load.

        Raises
        ------
        TuxCogLoadError
            If the cog fails to load due to non-configuration errors.
        """
        start_time = time.perf_counter()

        # Tag Sentry span with cog metadata for debugging
        set_span_attributes({"cog.name": path.stem, "cog.path": str(path)})

        try:
            # Convert file path to Python module path (e.g., tux.modules.admin.dev)
            module = self._resolve_module_path(path)
            set_span_attributes({"cog.module": module})

            # Check if module or any parent module is already loaded
            if self._is_duplicate_load(module):
                return  # Skip silently (warning already logged)

            # Load the extension using discord.py's extension system
            await self.bot.load_extension(name=module)

            # Record load time for performance monitoring
            load_time = time.perf_counter() - start_time
            self.load_times[module] = load_time

            # Add telemetry data to Sentry span
            set_span_attributes(
                {
                    "cog.status": "loaded",
                    "load_time_ms": load_time * MILLISECONDS_PER_SECOND,
                    "load_time_s": load_time,
                },
            )

            logger.debug(f"Loaded {module} in {load_time * 1000:.1f}ms")

        except TuxConfigurationError as config_error:
            # Direct configuration error: Skip cog gracefully
            self._handle_configuration_skip(path, config_error)
            return

        except Exception as e:
            # Check if exception chain contains a configuration error
            if self._is_configuration_error(e):
                self._handle_configuration_skip(path, e)
                return

            # Real error: Capture for Sentry and raise
            set_span_attributes({"cog.status": "failed"})
            capture_span_exception(
                e,
                traceback=traceback.format_exc(),
                module=str(path),
            )
            error_msg = (
                f"Failed to load cog {path}. Error: {e}\n{traceback.format_exc()}"
            )
            logger.opt(exception=True).error(
                f"Failed to load cog {path}",
                module=str(path),
            )
            raise TuxCogLoadError(error_msg) from e

    def _get_cog_priority(self, path: Path) -> int:
        """
        Get the loading priority for a cog based on its parent directory category.

        Priority determines load order within the cog system. Cogs with higher
        priority values are loaded before cogs with lower priority values.
        Priority is determined by the parent directory name, not the cog name.
        Priorities are configured in COG_PRIORITIES constant.

        Parameters
        ----------
        path : Path
            The path to the cog file.

        Returns
        -------
        int
            The priority value (higher = loaded earlier), defaults to 0.
        """
        return self.load_priorities.get(path.parent.name, 0)

    @span("cog.load_group")
    async def _load_cog_group(self, cogs: Sequence[Path]) -> None:
        """
        Load a group of cogs concurrently with telemetry and error tracking.

        Cogs within the same priority group are loaded in parallel for faster
        startup times. Configuration errors are handled gracefully and don't
        count as failures. Uses asyncio.gather with return_exceptions=True to
        ensure one cog's failure doesn't prevent others from loading.

        Parameters
        ----------
        cogs : Sequence[Path]
            The sequence of cog paths to load concurrently.
        """
        if not cogs:
            return

        # Tag Sentry span with group metadata
        set_span_attributes({"cog_count": len(cogs)})
        if categories := {cog.parent.name for cog in cogs if cog.parent}:
            set_span_attributes({"categories": list(categories)})

        # Load all cogs in this group concurrently
        start_time = time.perf_counter()
        results = await asyncio.gather(
            *[self._load_single_cog(cog) for cog in cogs],
            return_exceptions=True,  # Don't fail entire group on single cog error
        )
        end_time = time.perf_counter()

        # Calculate success/failure rates
        # None = successful load or graceful config skip
        # Exception = real failure (config errors already filtered in _load_single_cog)
        success_count = len([r for r in results if r is None])
        failure_count = len([r for r in results if isinstance(r, BaseException)])

        # Record telemetry for this group's loading
        set_span_attributes(
            {
                "load_time_s": end_time - start_time,
                "success_count": success_count,
                "failure_count": failure_count,
            },
        )

        logger.info(
            f"Loaded {success_count} cogs from {cogs[0].parent.name} cog group in {end_time - start_time:.2f}s",
        )

        # Log any failures that occurred (excluding config errors)
        for result, cog in zip(results, cogs, strict=False):
            if isinstance(result, Exception):
                logger.error(f"Error loading {cog}: {result}")

    async def _discover_and_prioritize_cogs(
        self,
        directory: Path,
    ) -> list[tuple[int, Path]]:
        """
        Discover eligible cogs in a directory and assign priorities.

        Recursively searches the directory for Python files, validates each as
        an eligible cog, assigns priorities based on parent directory, and
        sorts by priority for sequential loading.

        Parameters
        ----------
        directory : Path
            The directory to search for cogs.

        Returns
        -------
        list[tuple[int, Path]]
            List of (priority, path) tuples sorted by priority (highest first).
        """
        # Recursively find all Python files in directory
        all_py_files = list(directory.rglob("*.py"))

        # Filter to eligible cogs and assign priorities
        cog_paths: list[tuple[int, Path]] = []
        for item in all_py_files:
            if await self.is_cog_eligible(item):
                priority = self._get_cog_priority(item)
                cog_paths.append((priority, item))

        # Sort by priority (highest first for sequential loading)
        cog_paths.sort(key=lambda x: x[0], reverse=True)

        return cog_paths

    def _record_priority_distribution(self, cog_paths: list[tuple[int, Path]]) -> None:
        """
        Record the priority distribution of cogs for telemetry.

        Counts how many cogs exist at each priority level and records this in
        Sentry for monitoring load order distribution.

        Parameters
        ----------
        cog_paths : list[tuple[int, Path]]
            List of (priority, path) tuples to analyze.
        """
        priority_groups: dict[int, int] = {}
        for priority, _ in cog_paths:
            priority_groups[priority] = priority_groups.get(priority, 0) + 1
        set_span_attributes({"priority_groups": priority_groups})

    async def _load_by_priority_groups(self, cog_paths: list[tuple[int, Path]]) -> None:
        """
        Load cogs sequentially by priority group.

        Cogs are grouped by priority and each group is loaded before moving to
        the next lower priority. Within each group, cogs load concurrently.
        Ensures that high-priority cogs (handlers, services) are fully loaded
        before lower-priority cogs (modules, plugins) start loading.

        Parameters
        ----------
        cog_paths : list[tuple[int, Path]]
            Sorted list of (priority, path) tuples (highest priority first).
        """
        current_group: list[Path] = []
        current_priority: int | None = None

        for priority, cog_path in cog_paths:
            # When priority changes, load accumulated group before starting new one
            if current_priority is not None and current_priority != priority:
                await self._load_cog_group(current_group)
                current_group = []

            current_priority = priority
            current_group.append(cog_path)

        # Load final accumulated group
        if current_group:
            await self._load_cog_group(current_group)

    async def _process_single_file(self, path: Path) -> None:
        """
        Process a single file for loading (non-directory path).

        Checks eligibility before attempting to load the file as a cog.

        Parameters
        ----------
        path : Path
            The file path to process.
        """
        set_span_attributes({"path.is_dir": False})
        if await self.is_cog_eligible(path):
            await self._load_single_cog(path)

    async def _process_directory(self, path: Path) -> None:
        """
        Process a directory of cogs with priority-based loading.

        Discovers all Python files recursively, validates each as an eligible cog,
        groups cogs by priority, and loads each priority group sequentially (higher
        priority first). Within each group, cogs load concurrently. This balances
        dependency order with performance.

        Parameters
        ----------
        path : Path
            The directory path to process recursively.
        """
        set_span_attributes({"path.is_dir": True})

        # Discover and prioritize eligible cogs
        cog_paths = await self._discover_and_prioritize_cogs(path)

        set_span_attributes({"eligible_cog_count": len(cog_paths)})

        # Record priority distribution for telemetry
        self._record_priority_distribution(cog_paths)

        # Load cogs sequentially by priority group
        await self._load_by_priority_groups(cog_paths)

    @span("cog.load_path")
    async def load_cogs(self, path: Path) -> None:
        """
        Load cogs from a file or directory path with priority-based ordering.

        Automatically handles both single files and directories. Directories are
        processed recursively with priority-based loading. This is the main entry
        point for loading cogs from a path. Delegates to _process_single_file or
        _process_directory based on path type.

        Parameters
        ----------
        path : Path
            The path to a cog file or directory containing cogs.

        Raises
        ------
        TuxCogLoadError
            If an error occurs during cog discovery or loading.
        """
        # Tag Sentry span with path for debugging
        set_span_attributes({"cog.path": str(path)})

        try:
            # Route to appropriate handler based on path type
            if not await aiofiles.os.path.isdir(path):
                await self._process_single_file(path)
            else:
                await self._process_directory(path)

        except Exception as e:
            # Log and capture any errors during loading
            path_str = path.as_posix()
            logger.error(f"An error occurred while processing {path_str}: {e}")
            capture_span_exception(e, path=path_str)
            msg = "Failed to load cogs"
            raise TuxCogLoadError(msg) from e

    async def load_cogs_from_folder(self, folder_name: str) -> None:
        """
        Load cogs from a named folder relative to the tux package with timing.

        Provides performance monitoring and slow cog detection for a specific
        folder. Used to load major cog categories like "services/handlers",
        "modules", or "plugins". Skips gracefully if the folder doesn't exist
        (useful for optional plugin directories). Logs warnings for cogs that
        take >1s to load.

        Parameters
        ----------
        folder_name : str
            The folder name relative to the tux package (e.g., "modules" or
            "services/handlers").

        Raises
        ------
        TuxCogLoadError
            If an error occurs during folder loading.
        """
        start_time = time.perf_counter()

        # Resolve folder path relative to tux package
        cog_path: Path = Path(__file__).parent.parent / folder_name

        # Skip if folder doesn't exist (e.g., optional plugins directory)
        if not await aiofiles.os.path.exists(cog_path):
            logger.info(f"Folder {folder_name} does not exist, skipping")
            return

        try:
            # Load all cogs from this folder
            # Note: Errors in cog initialization are captured separately,
            # not attributed to the loader
            await self.load_cogs(path=cog_path)
            load_time = time.perf_counter() - start_time

            # Record metrics for folder loading
            record_cog_metric(
                cog_name=f"folder:{folder_name}",
                operation="load_folder",
                duration_ms=load_time * 1000,
                success=True,
            )

            if load_time:
                # Count cogs that were successfully loaded from this folder
                folder_module_prefix = folder_name.replace("/", ".")
                folder_cogs = [k for k in self.load_times if folder_module_prefix in k]
                logger.info(
                    f"Loaded {len(folder_cogs)} cogs from {folder_name} in {load_time * 1000:.0f}ms",
                )

                # Detect and warn about slow-loading cogs (performance monitoring)
                slow_threshold = 1.0  # seconds
                if slow_cogs := {
                    k: v for k, v in self.load_times.items() if v > slow_threshold
                }:
                    logger.warning(
                        f"Slow loading cogs (>{slow_threshold * 1000:.0f}ms): {slow_cogs}",
                    )

        except Exception as e:
            # Record failure metric
            load_time = time.perf_counter() - start_time

            record_cog_metric(
                cog_name=f"folder:{folder_name}",
                operation="load_folder",
                duration_ms=load_time * 1000,
                success=False,
                error_type=type(e).__name__,
            )

            # Capture exception separately (not as part of a transaction)
            capture_exception_safe(
                e,
                extra_context={
                    "cog_loader": {
                        "folder": folder_name,
                        "operation": "load_folder",
                        "path": str(cog_path),
                    },
                },
            )

            logger.error(f"Failed to load cogs from folder {folder_name}: {e}")
            msg = "Failed to load cogs from folder"
            raise TuxCogLoadError(msg) from e

    @classmethod
    async def setup(cls, bot: commands.Bot) -> None:
        """
        Initialize the cog loader and load all bot cogs in priority order.

        Main entrypoint for the cog loading system, called during bot startup.
        Loads cogs in this order: services/handlers (highest priority), modules
        (normal priority), then plugins (lowest priority). Creates a CogLoader
        instance, loads all cog folders sequentially, registers the CogLoader
        itself as a cog, and provides comprehensive telemetry via Sentry.

        Parameters
        ----------
        bot : commands.Bot
            The bot instance to load cogs into.

        Raises
        ------
        TuxCogLoadError
            If critical errors occur during cog loading.
        """
        start_time = time.perf_counter()
        cog_loader = cls(bot)

        try:
            # Load handlers first (highest priority - event handlers, error handlers)
            # These need to be ready before any commands are registered
            await cog_loader.load_cogs_from_folder(folder_name="services/handlers")

            # Load modules (normal priority - bot commands and features)
            # These are the main bot functionality
            await cog_loader.load_cogs_from_folder(folder_name="modules")

            # Load plugins (lowest priority - user extensions)
            # Optional folder for self-hosters to add custom cogs
            await cog_loader.load_cogs_from_folder(folder_name="plugins")

            total_time = time.perf_counter() - start_time

            # Record metrics for setup (not a transaction - this is background setup)
            record_cog_metric(
                cog_name="CogLoader",
                operation="setup",
                duration_ms=total_time * 1000,
                success=True,
            )

            # Register the CogLoader itself as a cog (for maintenance commands)
            await bot.add_cog(cog_loader)

            logger.info(f"Total cog loading time: {total_time * 1000:.0f}ms")

        except Exception as e:
            # Critical error during cog loading - record metric and capture exception
            total_time = time.perf_counter() - start_time

            record_cog_metric(
                cog_name="CogLoader",
                operation="setup",
                duration_ms=total_time * 1000,
                success=False,
                error_type=type(e).__name__,
            )

            # Capture exception separately (not as part of a transaction)
            capture_exception_safe(
                e,
                extra_context={
                    "cog_loader": {
                        "operation": "setup",
                        "bot_id": bot.user.id if bot.user else "unknown",
                    },
                },
            )

            logger.error(f"Failed to set up cog loader: {e}")
            msg = "Failed to initialize cog loader"
            raise TuxCogLoadError(msg) from e
