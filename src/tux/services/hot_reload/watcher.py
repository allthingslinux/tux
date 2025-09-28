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

    def start(self) -> None: ...
    def stop(self) -> None: ...


class CogWatcher(watchdog.events.FileSystemEventHandler):
    """File system event handler for cog reloading."""

    def __init__(
        self,
        config: HotReloadConfig,
        reload_callback: Callable[[str], None],
        base_dir: Path,
    ) -> None:
        super().__init__()
        self.config = config
        self.reload_callback = reload_callback
        self.base_dir = base_dir
        self.hash_tracker = FileHashTracker()
        self._debounce_tasks: dict[str, asyncio.Task[None]] = {}

    def should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed based on patterns."""
        # Check file patterns
        if not any(fnmatch.fnmatch(file_path.name, pattern) for pattern in self.config.file_patterns):
            return False

        # Check ignore patterns
        path_str = str(file_path)
        return not any(fnmatch.fnmatch(path_str, pattern) for pattern in self.config.ignore_patterns)

    def on_modified(self, event: watchdog.events.FileSystemEvent) -> None:
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = Path(str(event.src_path))
        if not self.should_process_file(file_path):
            return

        # Check if file actually changed (avoid duplicate events)
        if not self.hash_tracker.has_changed(file_path):
            return

        # Validate syntax if enabled
        if self.config.enable_syntax_checking and not validate_python_syntax(file_path):
            logger.warning(f"Skipping reload due to syntax errors in {file_path}")
            return

        # Get extension name
        if extension := get_extension_from_path(file_path, self.base_dir):
            logger.info(f"File changed: {file_path} -> {extension}")
            self._debounce_reload(extension)

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

    def _debounce_reload(self, extension: str) -> None:
        """Debounce reload requests to avoid rapid successive reloads."""
        # Cancel existing task for this extension
        if extension in self._debounce_tasks:
            self._debounce_tasks[extension].cancel()

        # Create new debounced task
        async def debounced_reload() -> None:
            await asyncio.sleep(self.config.debounce_delay)
            try:
                self.reload_callback(extension)
            except Exception as e:
                logger.error(f"Error in reload callback for {extension}: {e}")
            finally:
                self._debounce_tasks.pop(extension, None)

        # Schedule the task
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                return  # Don't reload if loop is closed
            self._debounce_tasks[extension] = loop.create_task(debounced_reload())
        except RuntimeError:
            # No event loop running, skip reload during shutdown
            return


class FileWatcher:
    """Manages file system watching for hot reload."""

    def __init__(self, config: HotReloadConfig, reload_callback: Callable[[str], None]) -> None:
        self.config = config
        self.reload_callback = reload_callback
        self.observer: Any = None  # Use Any to avoid watchdog typing issues
        self.watchers: list[CogWatcher] = []

    def start(self) -> None:
        """Start file system watching."""
        if self.observer is not None:
            logger.warning("File watcher already started")
            return

        try:
            self.observer = watchdog.observers.Observer()

            for watch_dir in self.config.watch_directories:
                if not watch_dir.exists():
                    logger.warning(f"Watch directory does not exist: {watch_dir}")
                    continue

                watcher = CogWatcher(self.config, self.reload_callback, watch_dir)
                self.watchers.append(watcher)

                self.observer.schedule(watcher, str(watch_dir), recursive=True)
                logger.info(f"Watching directory: {watch_dir}")

            self.observer.start()
            logger.info("File watcher started successfully")

        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")
            error_msg = f"Failed to start file watcher: {e}"
            raise FileWatchError(error_msg) from e

    def stop(self) -> None:
        """Stop file system watching."""
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
        """Check if file watcher is running."""
        return self.observer is not None and self.observer.is_alive()
