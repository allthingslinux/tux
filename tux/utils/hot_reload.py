import asyncio
import importlib
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar, cast

import watchdog.events
import watchdog.observers
from discord.ext import commands
from loguru import logger

# Define type variables for the decorator
F = TypeVar("F", bound=Callable[..., Any])


def path_from_extension(extension: str) -> Path:
    """Convert an extension notation to a file path."""

    base_dir = Path(__file__).parent.parent
    extension = extension.replace("tux.", "", 1)

    # Check if this might be a module with __init__.py
    if "." in extension:
        module_path = extension.replace(".", os.sep)
        init_path = base_dir / module_path / "__init__.py"
        if init_path.exists():
            return init_path

    # Otherwise, standard module file
    relative_path = extension.replace(".", os.sep) + ".py"
    return (base_dir / relative_path).resolve()


def get_extension_from_path(file_path: Path, base_dir: Path) -> str | None:
    """Attempt to get extension name from a file path."""

    try:
        # Make path relative to base directory
        rel_path = file_path.relative_to(base_dir)

        # Handle __init__.py files
        if file_path.name == "__init__.py":
            # Get the parent directory
            parent_path = rel_path.parent

            # Convert to extension format
            return f"tux.{str(parent_path).replace(os.sep, '.')}"

        # Regular .py file - remove .py extension
        module_path = rel_path.with_suffix("")

        # Convert to extension format
        return f"tux.{str(module_path).replace(os.sep, '.')}"

    except Exception as e:
        logger.error(f"Error getting extension from path {file_path}: {e}")
        return None


def reload_module_by_name(module_name: str) -> bool:
    """Reload a module by name if it exists in sys.modules."""

    if module_name not in sys.modules:
        return False

    try:
        importlib.reload(sys.modules[module_name])
        logger.info(f"Reloaded module {module_name}")
        return True  # noqa: TRY300

    except Exception as e:
        logger.error(f"Failed to reload module {module_name}: {e}")
        return False


class CogWatcher(watchdog.events.FileSystemEventHandler):
    """Watches for file changes and reloads corresponding cogs."""

    def __init__(self, bot: commands.Bot, path: str, recursive: bool = True):
        """
        Initialize the cog watcher.

        Parameters
        ----------
        bot : commands.Bot
            The bot instance.
        path : str
            The path to watch for changes.
        recursive : bool, optional
            Whether to watch recursively, by default True
        """

        self.bot = bot
        self.path = path
        self.recursive = recursive
        self.observer = watchdog.observers.Observer()
        self.observer.schedule(self, path, recursive=recursive)
        self.base_dir = Path(__file__).parent.parent

        # Store a relative path for logging
        self.display_path = str(Path(path).relative_to(self.base_dir.parent))

        # Store the main event loop from the calling thread
        self.loop = asyncio.get_running_loop()

        # Track help.py separately
        self.help_file_path = self.base_dir / "help.py"

        # Map of file paths to extension names
        self.path_to_extension: dict[str, str] = {}

        # For tracking tasks to prevent dangling
        self.pending_tasks: list[asyncio.Task[None]] = []

        # Build the extension map
        self._build_extension_map()

    def _build_extension_map(self) -> None:
        """Build a map of file paths to extension names."""

        for extension in list(self.bot.extensions.keys()):
            if extension == "jishaku":
                continue

            path = path_from_extension(extension)

            if path.exists():
                self.path_to_extension[str(path)] = extension
            else:
                logger.warning(f"Could not find file for extension {extension}, expected at {path}")

    def start(self) -> None:
        """Start watching for file changes."""

        self.observer.start()
        logger.info(f"Started watching {self.display_path} for changes (recursive={self.recursive})")

    def stop(self) -> None:
        """Stop watching for file changes."""

        self.observer.stop()
        self.observer.join()

        # Cancel any pending tasks
        for task in self.pending_tasks:
            if not task.done():
                task.cancel()
        logger.info("Stopped watching for changes")

    def on_modified(self, event: watchdog.events.FileSystemEvent) -> None:
        """
        Handle file modification events.

        Parameters
        ----------
        event : watchdog.events.FileSystemEvent
            The file system event.
        """

        # Skip non-Python files and directories
        if event.is_directory or not str(event.src_path).endswith(".py"):
            return

        file_path = Path(str(event.src_path))

        # Handle special cases first
        if self._handle_special_files(file_path):
            return

        # Handle regular extension files
        self._handle_extension_file(file_path)

    def _handle_special_files(self, file_path: Path) -> bool:
        """
        Handle special files like help.py and __init__.py.

        Returns True if handled, False otherwise.
        """

        # Check if it's the help file
        if file_path == self.help_file_path:
            self._reload_help()
            return True

        # Special handling for __init__.py files
        if file_path.name == "__init__.py":
            self._handle_init_file_change(file_path)
            return True

        return False

    def _handle_extension_file(self, file_path: Path) -> None:
        """Handle changes to regular extension files."""

        # Check direct mapping first
        if extension := self.path_to_extension.get(str(file_path)):
            self._reload_extension(extension)
            return

        # Try to infer extension name from path
        if possible_extension := get_extension_from_path(file_path, self.base_dir):
            # Try different variations of the extension name
            if self._try_reload_extension_variations(possible_extension, file_path):
                return

        else:
            logger.debug(f"Changed file {file_path} not mapped to any extension")

    def _process_extension_reload(self, extension: str, file_path: Path | None = None) -> None:
        """
        Process extension reload with logging and path mapping.

        Parameters
        ----------
        extension : str
            The extension to reload
        file_path : Path, optional
            If provided, updates path mapping after reload
        """

        self._reload_extension(extension)

        if file_path:
            self.path_to_extension[str(file_path)] = extension

    def _try_reload_extension_variations(self, extension: str, file_path: Path) -> bool:
        """
        Try to reload an extension with different name variations.

        Returns True if successful, False otherwise.
        """

        # Check exact match
        if extension in self.bot.extensions:
            self._process_extension_reload(extension, file_path)
            return True

        # Check parent modules
        parent_ext = extension

        while "." in parent_ext:
            parent_ext = parent_ext.rsplit(".", 1)[0]
            if parent_ext in self.bot.extensions:
                self._process_extension_reload(parent_ext, file_path)
                return True

        # Try without tux prefix
        if extension.startswith("tux."):
            no_prefix = extension[4:]  # Remove "tux."
            if no_prefix in self.bot.extensions:
                self._process_extension_reload(no_prefix, file_path)
                return True

        return False

    def _handle_init_file_change(self, init_file_path: Path) -> None:
        """
        Handle changes to __init__.py files that may be used by multiple cogs.

        Parameters
        ----------
        init_file_path : Path
            Path to the __init__.py file that changed
        """

        # Get the directory containing this __init__.py file
        directory = init_file_path.parent
        package_path = directory.relative_to(self.base_dir)

        # Convert path to potential extension prefix
        package_name = str(package_path).replace(os.sep, ".")
        if not package_name.startswith("cogs."):
            return

        # Find all extensions that start with this package name
        full_package = f"tux.{package_name}"

        # Reload the modules themselves first
        reload_module_by_name(full_package)
        reload_module_by_name(package_name)  # Try the short version too

        if extensions_to_reload := self._collect_extensions_to_reload(full_package, package_name):
            logger.info(f"Reloading {len(extensions_to_reload)} extensions after __init__.py change")
            for ext in extensions_to_reload:
                self._process_extension_reload(ext)

    def _collect_extensions_to_reload(self, full_package: str, short_package: str) -> list[str]:
        """Collect extensions that need to be reloaded based on package names."""

        extensions_to_reload: list[str] = [
            ext for ext in self.bot.extensions if ext.startswith(f"{full_package}.") or ext == full_package
        ]

        # Check for extensions with short package prefix (cogs.moderation)
        extensions_to_reload.extend(
            [ext for ext in self.bot.extensions if ext.startswith(f"{short_package}.") or ext == short_package],
        )

        return extensions_to_reload

    def _reload_extension(self, extension: str) -> None:
        """
        Reload an extension.

        Parameters
        ----------
        extension : str
            The extension to reload.
        """

        try:
            # Add a small delay to ensure file write is complete
            time.sleep(0.1)

            # Use the stored main event loop instead of trying to get the current one
            # which doesn't exist in the watchdog thread
            asyncio.run_coroutine_threadsafe(self._async_reload_extension(extension), self.loop)

        except Exception as e:
            logger.error(f"Failed to schedule reload of extension {extension}: {e}")

    def _reload_help(self) -> None:
        """Reload the help command."""

        try:
            # Add a small delay to ensure file write is complete
            time.sleep(0.1)

            # Use the stored main event loop
            asyncio.run_coroutine_threadsafe(self._async_reload_help(), self.loop)

        except Exception as e:
            logger.error(f"Failed to schedule reload of help command: {e}")
            import traceback

            logger.error(traceback.format_exc())

    async def _async_reload_extension(self, extension: str) -> None:
        """
        Asynchronously reload an extension.

        Parameters
        ----------
        extension : str
            The extension to reload.
        """

        try:
            await self.bot.reload_extension(extension)
            logger.info(f"Reloaded extension {extension}")

        except commands.ExtensionNotLoaded:
            try:
                # Try to load it if it wasn't loaded before
                await self.bot.load_extension(extension)
                logger.info(f"Loaded new extension {extension}")

                # Update our map
                path = path_from_extension(extension)
                self.path_to_extension[str(path)] = extension

            except commands.ExtensionError as e:
                logger.error(f"Failed to load new extension {extension}: {e}")

        except commands.ExtensionError as e:
            logger.error(f"Failed to reload extension {extension}: {e}")

    async def _async_reload_help(self) -> None:
        """Asynchronously reload the help command."""

        try:
            # Force reload of the help module
            if "tux.help" in sys.modules:
                importlib.reload(sys.modules["tux.help"])
            else:
                importlib.import_module("tux.help")

            try:
                # Create a dynamic import that doesn't happen at module load time
                # This breaks the circular import chain
                help_module = importlib.import_module("tux.help")
                TuxHelp = help_module.TuxHelp  # noqa: N806

                # Reset the help command with a new instance from the reloaded module
                self.bot.help_command = TuxHelp()
                logger.info("Reloaded help command")

            except (AttributeError, ImportError) as e:
                logger.error(f"Error accessing TuxHelp class: {e}")

        except Exception as e:
            logger.error(f"Failed to reload help command: {e}")
            import traceback

            logger.error(traceback.format_exc())


def watch(path: str = "cogs", preload: bool = False, recursive: bool = True) -> Callable[[F], F]:
    """
    Decorator to watch for file changes and reload cogs.

    Parameters
    ----------
    path : str, optional
        The path to watch for changes, by default "cogs"
    preload : bool, optional
        Whether to preload all cogs in the directory, by default False
    recursive : bool, optional
        Whether to watch recursively, by default True

    Returns
    -------
    Callable
        The decorated function.
    """

    def decorator(func: F) -> F:
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Run the original function first
            result = await func(self, *args, **kwargs)

            # Start watching for file changes
            watch_path = Path(__file__).parent.parent / path
            watcher = CogWatcher(self, str(watch_path), recursive)
            watcher.start()

            # Store the watcher reference so it doesn't get garbage collected
            self.cog_watcher = watcher

            return result

        # Cast to maintain the type signature
        return cast(F, wrapper)

    return decorator


# Backward compatibility for direct use as a Cog
class HotReload(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        logger.debug(f"Initializing HotReload cog with {len(bot.extensions)} loaded extensions")

        watch_path = Path(__file__).parent.parent / "cogs"

        self.watcher = CogWatcher(bot, str(watch_path), True)
        self.watcher.start()

    async def cog_unload(self) -> None:
        logger.debug("Unloading HotReload cog")
        self.watcher.stop()


async def setup(bot: commands.Bot) -> None:
    logger.info("Setting up hot reloader")
    logger.debug(f"Bot has {len(bot.extensions)} extensions loaded")

    await bot.add_cog(HotReload(bot))
