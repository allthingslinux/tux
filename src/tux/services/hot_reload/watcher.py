"""File system watcher for hot reload system."""

import asyncio
import fnmatch
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

import watchdog.events
import watchdog.observers
from loguru import logger

from .config import FileWatchError, HotReloadConfig
from .file_utils import FileHashTracker, get_extension_from_path, validate_python_syntax


class FileSystemWatcherProtocol(Protocol):
    """Protocol for file system watchers."""

    def start(self) -> None:
        """Start the file system watcher."""
        ...

    def stop(self) -> None:
        """Stop the file system watcher."""
        ...


class CogWatcher(watchdog.events.FileSystemEventHandler):
    """File system event handler for cog reloading."""

    def __init__(
        self,
        config: HotReloadConfig,
        reload_callback: Callable[[str], None],
        base_dir: Path,
        event_loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        """
        Initialize the cog watcher.

        Parameters
        ----------
        config : HotReloadConfig
            Hot reload configuration.
        reload_callback : Callable[[str], None]
            Callback function to invoke when a reload is needed.
        base_dir : Path
            Base directory to watch.
        event_loop : asyncio.AbstractEventLoop | None, optional
            Event loop for async operations, by default None.
        """
        super().__init__()
        self.config = config
        self.reload_callback = reload_callback
        self.base_dir = base_dir
        self.event_loop = event_loop
        self.hash_tracker = FileHashTracker()
        logger.info(
            f"Created CogWatcher for base_dir: {base_dir} (exists: {base_dir.exists()})",
        )

    def should_process_file(self, file_path: Path) -> bool:
        """
        Check if file should be processed based on patterns.

        Returns
        -------
        bool
            True if file should be processed, False otherwise.
        """
        # Check file patterns
        if not any(
            fnmatch.fnmatch(file_path.name, pattern)
            for pattern in self.config.file_patterns
        ):
            return False

        # Check ignore patterns
        path_str = str(file_path)
        return not any(
            fnmatch.fnmatch(path_str, pattern)
            for pattern in self.config.ignore_patterns
        )

    def on_modified(self, event: watchdog.events.FileSystemEvent) -> None:
        """Handle file modification events."""
        logger.info(
            f"WATCHDOG EVENT: {event.event_type} for {event.src_path} (is_directory: {event.is_directory})",
        )
        if event.is_directory:
            return

        file_path = Path(str(event.src_path))
        logger.debug(f"Processing file: {file_path}")

        if not self.should_process_file(file_path):
            logger.info(f"File {file_path} filtered out by should_process_file")
            return

        logger.info(f"File {file_path} passed filtering")

        # Check if file actually changed (avoid duplicate events)
        if not self.hash_tracker.has_changed(file_path):
            logger.info(f"File {file_path} has not changed")
            return

        logger.info(f"File {file_path} has changed, proceeding")

        # Validate syntax if enabled
        if self.config.enable_syntax_checking and not validate_python_syntax(file_path):
            logger.warning(f"Skipping reload due to syntax errors in {file_path}")
            return

        # Get extension name
        if extension := get_extension_from_path(file_path, self.base_dir):
            logger.info(f"Determined extension: {extension}")
            logger.info(f"Calling reload callback for {extension}")

            # If we have an event loop reference, use run_coroutine_threadsafe
            if self.event_loop and self.event_loop.is_running():
                try:
                    # Make the callback async by wrapping it
                    async def async_callback():
                        """
                        Async wrapper for reload callback.

                        This coroutine wraps the reload callback to handle exceptions
                        and ensure proper execution in the event loop.
                        """
                        try:
                            self.reload_callback(extension)
                        except Exception as e:
                            logger.error(
                                f"Error in reload callback for {extension}: {e}",
                            )

                    asyncio.run_coroutine_threadsafe(async_callback(), self.event_loop)
                except Exception as e:
                    logger.error(f"Failed to schedule reload callback: {e}")
            else:
                # Fallback to direct call (may not work in different thread)
                try:
                    self.reload_callback(extension)
                except Exception as e:
                    logger.error(f"Error in reload callback for {extension}: {e}")
        else:
            logger.warning(f"Could not determine extension for {file_path}")

    def on_created(self, event: watchdog.events.FileSystemEvent) -> None:
        """Handle file creation events."""
        self.on_modified(event)

    def on_deleted(self, event: watchdog.events.FileSystemEvent) -> None:
        """Handle file deletion events."""
        if event.is_directory:
            return

        file_path = Path(str(event.src_path))
        self.hash_tracker.remove_file(file_path)

        if extension := get_extension_from_path(file_path, self.base_dir):
            logger.info(f"File deleted: {file_path} -> {extension}")


class FileWatcher:
    """Manages file system watching for hot reload."""

    def __init__(
        self,
        config: HotReloadConfig,
        reload_callback: Callable[[str], None],
    ) -> None:
        """
        Initialize the file watcher.

        Parameters
        ----------
        config : HotReloadConfig
            Hot reload configuration.
        reload_callback : Callable[[str], None]
            Callback function to invoke when a reload is needed.
        """
        self.config = config
        self.reload_callback = reload_callback
        self.observer: Any = None  # Use Any to avoid watchdog typing issues
        self.watchers: list[CogWatcher] = []

    def start(self) -> None:
        """
        Start file system watching.

        Raises
        ------
        FileWatchError
            If starting the file watcher fails.
        """
        if self.observer is not None:
            logger.warning("File watcher already started")
            return

        try:
            current_dir = Path.cwd()
            logger.debug(f"Current working directory: {current_dir}")
            logger.info(
                f"Hot reload config watch directories: {self.config.watch_directories}",
            )

            self.observer = watchdog.observers.Observer()

            for watch_dir in self.config.watch_directories:
                abs_watch_dir = watch_dir.resolve()
                logger.info(
                    f"Setting up watch for directory: {watch_dir} -> {abs_watch_dir} (exists: {abs_watch_dir.exists()})",
                )
                if not abs_watch_dir.exists():
                    logger.warning(f"Watch directory does not exist: {abs_watch_dir}")
                    continue

                # Get the current event loop to pass to CogWatcher
                try:
                    current_loop = asyncio.get_event_loop()
                except RuntimeError:
                    current_loop = None

                watcher = CogWatcher(
                    self.config,
                    self.reload_callback,
                    abs_watch_dir,
                    current_loop,
                )
                self.watchers.append(watcher)

                self.observer.schedule(watcher, str(abs_watch_dir), recursive=True)
                logger.info(f"Watching directory: {abs_watch_dir}")

            self.observer.start()
            logger.success("File watcher started successfully")

        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")
            error_msg = f"Failed to start file watcher: {e}"
            raise FileWatchError(error_msg) from e

    def stop(self) -> None:
        """
        Stop file system watching.

        Raises
        ------
        FileWatchError
            If stopping the file watcher fails.
        """
        if self.observer is None:
            return

        try:
            self.observer.stop()
            self.observer.join(timeout=5.0)
            self.observer = None
            self.watchers.clear()
            logger.info("File watcher stopped")

        except Exception as e:
            logger.error(f"Error stopping file watcher: {e}")
            error_msg = f"Error stopping file watcher: {e}"
            raise FileWatchError(error_msg) from e

    def is_running(self) -> bool:
        """
        Check if file watcher is running.

        Returns
        -------
        bool
            True if watcher is running, False otherwise.
        """
        return self.observer is not None and self.observer.is_alive()
