"""
Enhanced hot reload system for Tux Discord bot.

Provides intelligent dependency tracking, file watching, and cog reloading
with comprehensive error handling and performance monitoring.
"""

import ast
import asyncio
import hashlib
import importlib
import os
import re
import sys
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol, TypeVar, cast

import sentry_sdk
import watchdog.events
import watchdog.observers
from discord.ext import commands
from loguru import logger

from tux.utils.sentry import span

# Type variables and protocols
F = TypeVar("F", bound=Callable[..., Any])


class BotProtocol(Protocol):
    """Protocol for bot-like objects."""

    @property
    def extensions(self) -> Mapping[str, ModuleType]: ...

    help_command: Any

    async def load_extension(self, name: str) -> None: ...
    async def reload_extension(self, name: str) -> None: ...


class FileSystemWatcherProtocol(Protocol):
    """Protocol for file system watchers."""

    def start(self) -> None: ...
    def stop(self) -> None: ...


@dataclass(frozen=True)
class HotReloadConfig:
    """Configuration for hot reload system following 12-factor principles."""

    # File watching configuration
    debounce_delay: float = float(os.getenv("HOT_RELOAD_DEBOUNCE_DELAY", "0.5"))
    cleanup_threshold: int = int(os.getenv("HOT_RELOAD_CLEANUP_THRESHOLD", "100"))
    max_dependency_depth: int = int(os.getenv("HOT_RELOAD_MAX_DEPENDENCY_DEPTH", "5"))
    cache_cleanup_interval: int = int(os.getenv("HOT_RELOAD_CACHE_CLEANUP_INTERVAL", "300"))

    # Feature toggles
    enable_hot_patching: bool = os.getenv("HOT_RELOAD_ENABLE_HOT_PATCHING", "false").lower() == "true"
    enable_dependency_tracking: bool = os.getenv("HOT_RELOAD_ENABLE_DEPENDENCY_TRACKING", "true").lower() == "true"
    enable_performance_monitoring: bool = (
        os.getenv("HOT_RELOAD_ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"
    )

    # Observability configuration
    log_level: str = os.getenv("HOT_RELOAD_LOG_LEVEL", "INFO")
    metrics_enabled: bool = os.getenv("HOT_RELOAD_METRICS_ENABLED", "false").lower() == "true"

    # File patterns
    watch_patterns: Sequence[str] = field(
        default_factory=lambda: [
            pattern.strip() for pattern in os.getenv("HOT_RELOAD_WATCH_PATTERNS", "*.py").split(",")
        ],
    )
    ignore_patterns: Sequence[str] = field(
        default_factory=lambda: [
            pattern.strip()
            for pattern in os.getenv("HOT_RELOAD_IGNORE_PATTERNS", ".tmp,.bak,.swp,__pycache__").split(",")
        ],
    )


# Exception hierarchy with better structure
class HotReloadError(Exception):
    """Base exception for hot reload operations."""

    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.context = context or {}


class DependencyResolutionError(HotReloadError):
    """Raised when dependency resolution fails."""


class FileWatchError(HotReloadError):
    """Raised when file watching operations fail."""


class ModuleReloadError(HotReloadError):
    """Raised when module reloading fails."""


class ConfigurationError(HotReloadError):
    """Raised when configuration is invalid."""


# Utility functions with better error handling
def validate_config(config: HotReloadConfig) -> None:
    """Validate hot reload configuration."""
    errors: list[str] = []

    if config.debounce_delay < 0:
        errors.append("debounce_delay must be non-negative")

    if config.cleanup_threshold < 1:
        errors.append("cleanup_threshold must be positive")

    if config.max_dependency_depth < 1:
        errors.append("max_dependency_depth must be positive")

    if errors:
        msg = f"Invalid configuration: {'; '.join(errors)}"
        raise ConfigurationError(msg)


def path_from_extension(extension: str, *, base_dir: Path | None = None) -> Path:
    """Convert an extension notation to a file path."""
    if base_dir is None:
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
    """
    Convert a file path to a possible extension name.

    Parameters
    ----------
    file_path : Path
        The file path to convert.
    base_dir : Path
        The base directory.

    Returns
    -------
    str | None
        The extension name, or None if not convertible.
    """
    try:
        relative_path = file_path.relative_to(base_dir)
        # Remove the .py extension
        path_without_ext = relative_path.with_suffix("")
        # Convert to dot notation
        extension = str(path_without_ext).replace(os.sep, ".")
    except ValueError:
        return None
    else:
        return f"tux.{extension}"


@contextmanager
def module_reload_context(module_name: str):
    """Context manager for safely reloading modules."""
    original_module = sys.modules.get(module_name)
    try:
        yield
    except Exception:
        # Restore original module on failure
        if original_module is not None:
            sys.modules[module_name] = original_module
        elif module_name in sys.modules:
            del sys.modules[module_name]
        raise


@span("reload.module")
def reload_module_by_name(module_name: str) -> bool:
    """Reload a module by name if it exists in sys.modules."""
    if module_name not in sys.modules:
        logger.debug(f"Module {module_name} not in sys.modules, skipping reload")
        return False

    try:
        with module_reload_context(module_name):
            importlib.reload(sys.modules[module_name])
    except Exception as e:
        logger.error(f"Failed to reload module {module_name}: {e}")
        if sentry_sdk.is_initialized():
            sentry_sdk.capture_exception(e)
        return False
    else:
        logger.debug(f"Reloaded module {module_name}")
        return True


class DependencyTracker(ABC):
    """Abstract base class for dependency tracking."""

    @abstractmethod
    def scan_dependencies(self, file_path: Path) -> set[str]:
        """Scan file for dependencies."""

    @abstractmethod
    def get_dependents(self, module_name: str) -> set[str]:
        """Get direct dependents of a module."""

    @abstractmethod
    def get_transitive_dependents(self, module_name: str) -> set[str]:
        """Get all transitive dependents of a module."""


class FileHashTracker:
    """Tracks file hashes for change detection."""

    def __init__(self) -> None:
        self._file_hashes: dict[str, str] = {}

    @property
    def cache_size(self) -> int:
        """Get the number of cached file hashes."""
        return len(self._file_hashes)

    @span("dependency.get_file_hash")
    def get_file_hash(self, file_path: Path) -> str:
        """Get SHA256 hash of file content for change detection."""
        try:
            with file_path.open("rb") as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except OSError as e:
            logger.debug(f"Failed to read file {file_path}: {e}")
            return ""

    def has_file_changed(self, file_path: Path, *, silent: bool = False) -> bool:
        """Check if file has actually changed since last scan."""
        current_hash = self.get_file_hash(file_path)
        file_key = str(file_path)

        if file_key not in self._file_hashes:
            # First time seeing this file - store hash but don't consider it "changed"
            # unless this is a brand new file that didn't exist before
            self._file_hashes[file_key] = current_hash
            if not silent:
                logger.debug(f"First time tracking {file_path.name}, storing baseline hash")
            return False  # Don't reload on first encounter

        if self._file_hashes[file_key] != current_hash:
            logger.debug(
                f"Content changed for {file_path.name}: hash {self._file_hashes[file_key][:8]} -> {current_hash[:8]}",
            )
            self._file_hashes[file_key] = current_hash
            return True

        logger.debug(f"No content change for {file_path.name}")
        return False

    def clear_cache(self) -> None:
        """Clear the file hash cache."""
        self._file_hashes.clear()


class ClassDefinitionTracker:
    """Tracks class definitions for hot patching capabilities."""

    def __init__(self) -> None:
        self._class_registry: dict[str, dict[str, dict[str, Any]]] = {}

    @property
    def tracked_classes_count(self) -> int:
        """Get the number of tracked classes."""
        return len(self._class_registry)

    @span("dependency.scan_classes")
    def scan_class_definitions(self, file_path: Path, module_name: str) -> dict[str, dict[str, Any]]:
        """Scan for class definitions in a file for hot patching capabilities."""
        if not file_path.exists() or file_path.suffix != ".py":
            return {}

        try:
            with file_path.open(encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            classes: dict[str, dict[str, Any]] = {}

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    base_names: list[str] = []
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            base_names.append(base.id)
                        elif isinstance(base, ast.Attribute):
                            base_names.append(ast.unparse(base))

                    classes[node.name] = {
                        "bases": base_names,
                        "lineno": node.lineno,
                        "module": module_name,
                    }

        except Exception as e:
            logger.debug(f"Error scanning class definitions in {file_path}: {e}")
            if sentry_sdk.is_initialized():
                sentry_sdk.capture_exception(e)
            return {}
        else:
            return classes

    def register_classes(self, module_name: str, file_path: Path) -> None:
        """Register class definitions for a module for hot patching tracking."""
        if classes := self.scan_class_definitions(file_path, module_name):
            self._class_registry[module_name] = classes
            logger.debug(f"Registered {len(classes)} classes for {module_name}: {list(classes.keys())}")

    def get_changed_classes(self, module_name: str, file_path: Path) -> list[str]:
        """Detect which classes have changed in a module."""
        old_classes = self._class_registry.get(module_name, {})
        new_classes = self.scan_class_definitions(file_path, module_name)

        changed_classes: list[str] = []

        # Check for new or modified classes
        changed_classes.extend(
            class_name
            for class_name, class_info in new_classes.items()
            if class_name not in old_classes or old_classes[class_name] != class_info
        )
        # Check for removed classes
        changed_classes.extend(class_name for class_name in old_classes if class_name not in new_classes)

        # Update registry
        if new_classes:
            self._class_registry[module_name] = new_classes
        elif module_name in self._class_registry:
            del self._class_registry[module_name]

        return changed_classes

    def clear_cache(self) -> None:
        """Clear the class registry cache."""
        self._class_registry.clear()


class DependencyGraph(DependencyTracker):
    """Smart dependency tracking for modules and extensions with memory optimization."""

    def __init__(self, config: HotReloadConfig) -> None:
        self._config = config
        self._module_dependencies: dict[str, set[str]] = {}
        self._reverse_dependencies: dict[str, set[str]] = {}
        self._last_scan_time: dict[str, float] = {}
        self._last_cleanup: float = time.time()

        # Composition over inheritance for specialized trackers
        self._file_tracker = FileHashTracker()
        self._class_tracker = ClassDefinitionTracker() if config.enable_hot_patching else None

    @span("dependency.scan_dependencies")
    def scan_dependencies(self, file_path: Path) -> set[str]:
        """Enhanced dependency scanning with better import detection."""
        if not file_path.exists() or file_path.suffix != ".py":
            return set()

        try:
            with file_path.open(encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            dependencies: set[str] = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name and alias.name.startswith(("tux.", "discord")):
                            dependencies.add(alias.name)

                elif isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith(("tux.", "discord")):
                        dependencies.add(node.module)
                    # Handle relative imports
                    elif (
                        node.level > 0
                        and (abs_module := self._resolve_relative_import(file_path, node.module, node.level))
                        and abs_module.startswith("tux.")
                    ):
                        dependencies.add(abs_module)

        except Exception as e:
            logger.debug(f"Error scanning dependencies in {file_path}: {e}")
            if sentry_sdk.is_initialized():
                sentry_sdk.capture_exception(e)
            return set()
        else:
            return dependencies

    def has_file_changed(self, file_path: Path, *, silent: bool = False) -> bool:
        """Check if file has actually changed since last scan."""
        return self._file_tracker.has_file_changed(file_path, silent=silent)

    def register_classes(self, module_name: str, file_path: Path) -> None:
        """Register class definitions for a module for hot patching tracking."""
        if self._class_tracker:
            self._class_tracker.register_classes(module_name, file_path)

    def get_changed_classes(self, module_name: str, file_path: Path) -> list[str]:
        """Detect which classes have changed in a module."""
        if self._class_tracker:
            return self._class_tracker.get_changed_classes(module_name, file_path)
        return []

    def _resolve_relative_import(self, file_path: Path, module: str | None, level: int) -> str | None:
        """Resolve relative imports to absolute module names."""
        try:
            # Get the module path relative to tux package
            base_dir = Path(__file__).parent.parent
            relative_path = file_path.relative_to(base_dir)

            # Calculate the parent directory based on level
            path_parts = list(relative_path.parts[:-1])  # Remove filename

            # Go up 'level' directories
            for _ in range(level - 1):
                if path_parts:
                    path_parts.pop()

            # Add the relative module if provided
            if module:
                path_parts.extend(module.split("."))

            if path_parts:
                return f"tux.{'.'.join(path_parts)}"
        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to resolve relative import: {e}")

        return None

    @span("dependency.update")
    def update_dependencies(self, file_path: Path, module_name: str) -> None:
        """Update dependency tracking for a module."""
        if not self._config.enable_dependency_tracking:
            return

        dependencies = self.scan_dependencies(file_path)

        # Clean up old reverse dependencies
        if module_name in self._module_dependencies:
            for old_dep in self._module_dependencies[module_name]:
                if old_dep in self._reverse_dependencies:
                    self._reverse_dependencies[old_dep].discard(module_name)
                    if not self._reverse_dependencies[old_dep]:
                        del self._reverse_dependencies[old_dep]

        # Update forward dependencies
        self._module_dependencies[module_name] = dependencies

        # Update reverse dependencies
        for dep in dependencies:
            if dep not in self._reverse_dependencies:
                self._reverse_dependencies[dep] = set()
            self._reverse_dependencies[dep].add(module_name)

        # Register classes for hot patching
        self.register_classes(module_name, file_path)

        # Update scan time
        self._last_scan_time[module_name] = time.time()

        # Periodic cleanup
        self._cleanup_if_needed()

    def get_dependents(self, module_name: str) -> set[str]:
        """Get direct dependents of a module."""
        return self._reverse_dependencies.get(module_name, set()).copy()

    @span("dependency.get_transitive")
    def get_transitive_dependents(self, module_name: str) -> set[str]:
        """Get all transitive dependents of a module with cycle detection."""
        visited: set[str] = set()
        result: set[str] = set()
        max_depth = self._config.max_dependency_depth

        def _visit(current_module: str, depth: int) -> None:
            if depth >= max_depth or current_module in visited:
                return

            visited.add(current_module)
            direct_dependents = self.get_dependents(current_module)

            for dependent in direct_dependents:
                if dependent not in result:
                    result.add(dependent)
                    _visit(dependent, depth + 1)

        _visit(module_name, 0)
        return result

    def get_all_tracked_modules(self) -> list[str]:
        """Get all tracked modules."""
        return list(self._module_dependencies.keys())

    def get_module_dependencies(self, module_name: str) -> set[str]:
        """Get direct dependencies of a module."""
        return self._module_dependencies.get(module_name, set()).copy()

    def get_stats(self) -> dict[str, int]:
        """Get statistics about the dependency graph."""
        return {
            "total_modules": len(self._module_dependencies),
            "total_reverse_deps": len(self._reverse_dependencies),
            "cached_files": self._file_tracker.cache_size,
            "tracked_classes": self._class_tracker.tracked_classes_count if self._class_tracker else 0,
        }

    def _cleanup_if_needed(self) -> None:
        """Perform cleanup if threshold is exceeded or enough time has passed."""
        current_time = time.time()

        should_cleanup = (
            self._file_tracker.cache_size > self._config.cleanup_threshold
            or current_time - self._last_cleanup > self._config.cache_cleanup_interval
        )

        if should_cleanup:
            self._cleanup_stale_entries()
            self._last_cleanup = current_time

    def _cleanup_stale_entries(self) -> None:
        """Clean up stale entries from caches."""
        current_time = time.time()
        stale_threshold = 3600  # 1 hour

        # Clean up old scan times and associated data
        stale_modules = [
            module for module, scan_time in self._last_scan_time.items() if current_time - scan_time > stale_threshold
        ]

        for module in stale_modules:
            self._remove_module_tracking(module)

        if stale_modules:
            logger.debug(f"Cleaned up {len(stale_modules)} stale dependency entries")

    def _remove_module_tracking(self, module_name: str) -> None:
        """Remove all tracking data for a module."""
        # Remove from scan times
        self._last_scan_time.pop(module_name, None)

        # Clean up dependencies
        if module_name in self._module_dependencies:
            for dep in self._module_dependencies[module_name]:
                if dep in self._reverse_dependencies:
                    self._reverse_dependencies[dep].discard(module_name)
                    if not self._reverse_dependencies[dep]:
                        del self._reverse_dependencies[dep]
            del self._module_dependencies[module_name]

        # Remove reverse dependencies
        if module_name in self._reverse_dependencies:
            del self._reverse_dependencies[module_name]

    @span("dependency.hot_patch_class")
    def hot_patch_class(self, module_name: str, class_name: str, new_class: type) -> bool:
        """Attempt to hot patch a class definition (experimental)."""
        if not self._config.enable_hot_patching:
            logger.debug("Hot patching disabled in configuration")
            return False

        try:
            if module_name not in sys.modules:
                logger.debug(f"Module {module_name} not loaded, cannot hot patch {class_name}")
                return False

            module = sys.modules[module_name]
            if not hasattr(module, class_name):
                logger.debug(f"Class {class_name} not found in {module_name}")
                return False

            # Attempt to patch
            setattr(module, class_name, new_class)
        except Exception as e:
            logger.error(f"Failed to hot patch class {class_name} in {module_name}: {e}")
            if sentry_sdk.is_initialized():
                sentry_sdk.capture_exception(e)
            return False
        else:
            logger.info(f"Hot patched class {class_name} in {module_name}")
            return True

    @contextmanager
    def cleanup_context(self):
        """Context manager for automatic cleanup."""
        try:
            yield self
        finally:
            self._file_tracker.clear_cache()
            if self._class_tracker:
                self._class_tracker.clear_cache()


class CogWatcher(watchdog.events.FileSystemEventHandler):
    """Enhanced cog watcher with smart dependency tracking and improved error handling."""

    def __init__(self, bot: BotProtocol, path: str, *, recursive: bool = True, config: HotReloadConfig | None = None):
        """Initialize the cog watcher with validation."""
        self._config = config or HotReloadConfig()
        validate_config(self._config)

        watch_path = Path(path)
        if not watch_path.exists():
            msg = f"Watch path does not exist: {path}"
            raise FileWatchError(msg)

        self.bot = bot
        self.path = str(watch_path.resolve())
        self.recursive = recursive
        self.observer = watchdog.observers.Observer()
        self.observer.schedule(self, self.path, recursive=recursive)
        self.base_dir = Path(__file__).parent.parent

        # Store a relative path for logging
        try:
            self.display_path = str(Path(path).relative_to(self.base_dir.parent))
        except ValueError:
            self.display_path = path

        # Store the main event loop from the calling thread
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError as e:
            msg = "Hot reload must be initialized from within an async context"
            raise HotReloadError(msg) from e

        # Track special files
        self.help_file_path = self.base_dir / "help.py"

        # Extension tracking
        self.path_to_extension: dict[str, str] = {}
        self.pending_tasks: list[asyncio.Task[None]] = []

        # Enhanced dependency tracking
        self.dependency_graph = DependencyGraph(self._config)

        # Debouncing configuration
        self._debounce_timers: dict[str, asyncio.Handle] = {}

        # Build initial extension map
        self._build_extension_map()

        logger.debug(f"CogWatcher initialized for path: {self.display_path}")

    @span("watcher.build_extension_map")
    def _build_extension_map(self) -> None:
        """Build a map of file paths to extension names and scan initial dependencies."""
        extension_count = 0

        for extension in list(self.bot.extensions.keys()):
            if extension == "jishaku":
                continue

            try:
                path = path_from_extension(extension)
                if path.exists():
                    self.path_to_extension[str(path)] = extension
                    self.dependency_graph.update_dependencies(path, extension)
                    extension_count += 1
                else:
                    logger.warning(f"Could not find file for extension {extension}, expected at {path}")
            except Exception as e:
                logger.error(f"Error processing extension {extension}: {e}")
                if sentry_sdk.is_initialized():
                    sentry_sdk.capture_exception(e)

        # Pre-populate hash cache for all Python files in watched directories
        # This eliminates "first encounter" issues for any file
        cached_files = self._populate_all_file_hashes()

        if cached_files > 0:
            logger.debug(f"Pre-populated hash cache for {cached_files} Python files")

        logger.debug(f"Mapped {extension_count} extensions for hot reload")

    def _populate_all_file_hashes(self) -> int:
        """Pre-populate hash cache for all Python files in watched directories."""
        cached_count = 0

        # Get the root watch path (this includes the entire tux directory)
        watch_root = Path(self.path)

        try:
            # Scan all Python files recursively
            for py_file in watch_root.rglob("*.py"):
                # Skip files we don't want to track
                if (
                    py_file.name.startswith(".")
                    or py_file.name.endswith((".tmp", ".bak", ".swp"))
                    or "__pycache__" in str(py_file)
                ):
                    continue

                # Pre-populate cache silently
                self.dependency_graph.has_file_changed(py_file, silent=True)
                cached_count += 1

        except Exception as e:
            logger.debug(f"Error during file cache pre-population: {e}")

        return cached_count

    def start(self) -> None:
        """Start watching for file changes."""
        try:
            self.observer.start()
            logger.info(f"Hot reload watching {self.display_path}")
        except Exception as e:
            msg = f"Failed to start file watcher: {e}"
            raise FileWatchError(msg) from e

    def stop(self) -> None:
        """Stop watching for file changes and cleanup resources."""
        try:
            self.observer.stop()
            self.observer.join(timeout=5.0)  # Add timeout to prevent hanging
        except Exception as e:
            logger.error(f"Error stopping file watcher: {e}")

        # Cancel any pending tasks
        for task in self.pending_tasks:
            if not task.done():
                task.cancel()

        # Cancel debounce timers
        for timer in self._debounce_timers.values():
            timer.cancel()
        self._debounce_timers.clear()

        logger.info("Stopped watching for changes")

    @span("watcher.on_modified")
    def on_modified(self, event: watchdog.events.FileSystemEvent) -> None:
        """Handle file modification events with debouncing and validation."""
        # Skip non-Python files and directories
        if event.is_directory or not str(event.src_path).endswith(".py"):
            return

        file_path = Path(str(event.src_path))

        # Skip temporary/backup files
        if file_path.name.startswith(".") or file_path.name.endswith((".tmp", ".bak", ".swp")):
            return

        logger.debug(f"File modification event: {file_path.name}")

        # Check if file actually changed - this prevents unnecessary reloads on save without changes
        if not self.dependency_graph.has_file_changed(file_path):
            logger.debug(f"File {file_path.name} saved but content unchanged, skipping reload")
            return

        logger.debug(f"File {file_path.name} content changed, scheduling reload")
        file_key = str(file_path)

        # Cancel existing debounce timer if any
        if file_key in self._debounce_timers:
            self._debounce_timers[file_key].cancel()

        # Set new debounce timer
        try:
            self._debounce_timers[file_key] = self.loop.call_later(
                self._config.debounce_delay,
                self._handle_file_change_debounced,
                file_path,
            )
        except Exception as e:
            logger.error(f"Failed to schedule file change handler: {e}")

    def _handle_file_change_debounced(self, file_path: Path) -> None:
        """Handle file change after debounce period with comprehensive error handling."""
        file_key = str(file_path)

        # Remove from debounce tracking
        if file_key in self._debounce_timers:
            del self._debounce_timers[file_key]

        logger.debug(f"Processing file change: {file_path.name}")

        try:
            # Handle special cases first
            if self._handle_special_files(file_path):
                return

            # Handle regular extension files
            self._handle_extension_file(file_path)
        except Exception as e:
            logger.error(f"Error handling file change for {file_path}: {e}")
            if sentry_sdk.is_initialized():
                sentry_sdk.capture_exception(e)

    def _handle_special_files(self, file_path: Path) -> bool:
        """Handle special files like help.py and __init__.py."""
        # Check if it's the help file
        if file_path == self.help_file_path:
            self._reload_help()
            return True

        # Special handling for __init__.py files
        if file_path.name == "__init__.py":
            self._handle_init_file_change(file_path)
            return True

        return False

    @span("watcher.handle_extension_file")
    def _handle_extension_file(self, file_path: Path) -> None:
        """Handle changes to regular extension files with smart dependency resolution."""
        # Convert file path to module name for dependency tracking
        if module_name := self._file_path_to_module_name(file_path):
            self.dependency_graph.update_dependencies(file_path, module_name)

        # Check direct mapping first
        if extension := self.path_to_extension.get(str(file_path)):
            self._reload_extension(extension)
            return

        # Check for utility module dependencies
        if self._handle_utility_dependency(file_path):
            return

        # Try to infer extension name from path
        if (
            possible_extension := get_extension_from_path(file_path, self.base_dir)
        ) and self._try_reload_extension_variations(possible_extension, file_path):
            return

        logger.debug(f"Changed file {file_path} not mapped to any extension")

    def _file_path_to_module_name(self, file_path: Path) -> str | None:
        """Convert file path to module name."""
        try:
            rel_path = file_path.relative_to(self.base_dir)
            module_path = str(rel_path.with_suffix("")).replace(os.sep, ".")
        except ValueError:
            return None
        else:
            return f"tux.{module_path}"

    @span("watcher.handle_utility_dependency")
    def _handle_utility_dependency(self, file_path: Path) -> bool:
        """Handle changes to utility modules using enhanced dependency tracking."""
        try:
            rel_path = file_path.relative_to(self.base_dir)
            rel_path_str = str(rel_path).replace(os.sep, "/")
        except ValueError:
            return False

        module_name = f"tux.{rel_path_str.replace('/', '.').replace('.py', '')}"

        # Special handling for flags.py - only reload cogs that actually use flag classes
        if rel_path_str == "utils/flags.py":
            self._reload_flag_class_dependent_cogs()
            return True

        # Handle utils/ or ui/ changes with smart dependency resolution
        if rel_path_str.startswith(("utils/", "ui/")):
            # Reload the changed module first
            reload_module_by_name(module_name)

            if dependent_extensions := self._get_dependent_extensions(module_name):
                # Use batch reload for multiple dependents
                asyncio.run_coroutine_threadsafe(
                    self._batch_reload_extensions(dependent_extensions, f"cogs dependent on {module_name}"),
                    self.loop,
                )
            else:
                logger.debug(f"No cogs found depending on {module_name}")
            return True

        return False

    def _get_dependent_extensions(self, module_name: str) -> list[str]:
        """Get extensions that depend on the given module using the dependency graph."""
        dependents = self.dependency_graph.get_transitive_dependents(module_name)

        # Filter to only include loaded extensions (excluding jishaku)
        return [dep for dep in dependents if dep in self.bot.extensions and dep != "jishaku"]

    def _process_extension_reload(self, extension: str, file_path: Path | None = None) -> None:
        """Process extension reload with logging and path mapping."""
        self._reload_extension(extension)

        if file_path:
            self.path_to_extension[str(file_path)] = extension

    @span("watcher.try_reload_variations")
    def _try_reload_extension_variations(self, extension: str, file_path: Path) -> bool:
        """Try to reload an extension with different name variations."""
        # Check exact match
        if extension in self.bot.extensions:
            self._process_extension_reload(extension, file_path)
            return True

        # Check if a shorter version is already loaded (prevents duplicates)
        parts = extension.split(".")
        for i in range(len(parts) - 1, 0, -1):
            shorter_ext = ".".join(parts[:i])
            if shorter_ext in self.bot.extensions:
                logger.warning(f"Skipping reload of {extension} as parent module {shorter_ext} already loaded")
                self.path_to_extension[str(file_path)] = shorter_ext
                return True

        # Check parent modules
        parent_ext = extension
        while "." in parent_ext:
            parent_ext = parent_ext.rsplit(".", 1)[0]
            if parent_ext in self.bot.extensions:
                self._process_extension_reload(parent_ext, file_path)
                return True

        # Try without tux prefix
        if extension.startswith("tux.") and (no_prefix := extension[4:]) in self.bot.extensions:
            self._process_extension_reload(no_prefix, file_path)
            return True

        return False

    @span("watcher.handle_init_file")
    def _handle_init_file_change(self, init_file_path: Path) -> None:
        """Handle changes to __init__.py files that may be used by multiple cogs."""
        try:
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
            reload_module_by_name(package_name)

            if extensions_to_reload := self._collect_extensions_to_reload(full_package, package_name):
                logger.info(f"Reloading {len(extensions_to_reload)} extensions after __init__.py change")
                for ext in extensions_to_reload:
                    self._process_extension_reload(ext)
        except Exception as e:
            logger.error(f"Error handling __init__.py change for {init_file_path}: {e}")
            if sentry_sdk.is_initialized():
                sentry_sdk.capture_exception(e)

    def _collect_extensions_to_reload(self, full_package: str, short_package: str) -> list[str]:
        """Collect extensions that need to be reloaded based on package names."""
        # Find extensions with full and short package prefixes
        extensions_with_full_prefix = [
            ext for ext in self.bot.extensions if ext.startswith(f"{full_package}.") or ext == full_package
        ]
        extensions_with_short_prefix = [
            ext for ext in self.bot.extensions if ext.startswith(f"{short_package}.") or ext == short_package
        ]

        # Combine and remove duplicates while preserving order
        all_extensions = extensions_with_full_prefix + extensions_with_short_prefix
        return list(dict.fromkeys(all_extensions))

    def _reload_extension(self, extension: str) -> None:
        """Reload an extension with proper error handling."""
        try:
            # Add a small delay to ensure file write is complete
            time.sleep(0.1)

            # Schedule async reload
            asyncio.run_coroutine_threadsafe(self._async_reload_extension(extension), self.loop)
        except Exception as e:
            logger.error(f"Failed to schedule reload of extension {extension}: {e}")
            if sentry_sdk.is_initialized():
                sentry_sdk.capture_exception(e)

    def _reload_help(self) -> None:
        """Reload the help command with proper error handling."""
        try:
            time.sleep(0.1)  # Ensure file write is complete

            # Schedule async reload - simplify task tracking
            asyncio.run_coroutine_threadsafe(self._async_reload_help(), self.loop)
        except Exception as e:
            logger.error(f"Failed to schedule reload of help command: {e}")
            if sentry_sdk.is_initialized():
                sentry_sdk.capture_exception(e)

    @span("reload.extension")
    async def _async_reload_extension(self, extension: str) -> None:
        """Asynchronously reload an extension with logging (for single reloads)."""
        try:
            # Clear related module cache entries before reloading
            if modules_to_clear := [key for key in sys.modules if key.startswith(extension)]:
                logger.debug(f"Clearing {len(modules_to_clear)} cached modules for {extension}")
                for module_key in modules_to_clear:
                    del sys.modules[module_key]

            # Reload the extension
            await self.bot.reload_extension(extension)

            # Log individual reloads at INFO level for single operations
            if extension.startswith("tux.cogs"):
                short_name = extension.replace("tux.cogs.", "")
                logger.info(f"✅ Reloaded {short_name}")
            else:
                logger.info(f"✅ Reloaded extension {extension}")
        except commands.ExtensionNotLoaded:
            try:
                # Try to load it if it wasn't loaded before
                await self.bot.load_extension(extension)
                logger.info(f"✅ Loaded new extension {extension}")

                # Update our mapping
                path = path_from_extension(extension)
                self.path_to_extension[str(path)] = extension
            except commands.ExtensionError as e:
                logger.error(f"❌ Failed to load new extension {extension}: {e}")
                if sentry_sdk.is_initialized():
                    sentry_sdk.capture_exception(e)
        except commands.ExtensionError as e:
            logger.error(f"❌ Failed to reload extension {extension}: {e}")
            if sentry_sdk.is_initialized():
                sentry_sdk.capture_exception(e)

    @span("reload.help")
    async def _async_reload_help(self) -> None:
        """Asynchronously reload the help command."""
        try:
            # Force reload of the help module
            if "tux.help" in sys.modules:
                importlib.reload(sys.modules["tux.help"])
            else:
                importlib.import_module("tux.help")

            try:
                # Dynamic import to break circular dependencies
                help_module = importlib.import_module("tux.help")
                tux_help = help_module.TuxHelp

                # Reset the help command with new instance
                self.bot.help_command = tux_help()
                logger.info("✅ Reloaded help command")
            except (AttributeError, ImportError) as e:
                logger.error(f"Error accessing TuxHelp class: {e}")
                if sentry_sdk.is_initialized():
                    sentry_sdk.capture_exception(e)
        except Exception as e:
            logger.error(f"❌ Failed to reload help command: {e}")
            if sentry_sdk.is_initialized():
                sentry_sdk.capture_exception(e)

    @span("reload.flag_dependent_cogs")
    def _reload_flag_class_dependent_cogs(self) -> None:
        """Reload only cogs that actually use flag classes from tux.utils.flags."""
        logger.info("Flags module changed, reloading dependent cogs...")

        # First reload the flags module
        reload_module_by_name("tux.utils.flags")

        # Find cogs that actually import flag classes
        flag_using_cogs: set[str] = set()

        for ext_name in self.bot.extensions:
            try:
                if self._get_flag_classes_used(ext_name):
                    flag_using_cogs.add(ext_name)
            except Exception as e:
                logger.debug(f"Error checking flag usage for {ext_name}: {e}")

        if flag_using_cogs:
            # Schedule async batch reload with proper completion tracking
            asyncio.run_coroutine_threadsafe(
                self._batch_reload_extensions(list(flag_using_cogs), "flag-dependent"),
                self.loop,
            )
        else:
            logger.debug("No cogs found using flag classes")

    async def _batch_reload_extensions(self, extensions: list[str], description: str) -> None:
        """Reload multiple extensions and log a single summary."""
        start_time = time.time()

        # Reload all extensions concurrently but quietly
        tasks = [self._async_reload_extension_quiet(ext) for ext in extensions]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successes and failures
        successes = len([r for r in results if not isinstance(r, Exception)])
        failures = len(results) - successes

        elapsed = time.time() - start_time

        if failures > 0:
            logger.warning(
                f"✅ Reloaded {successes}/{len(extensions)} {description} cogs in {elapsed:.1f}s ({failures} failed)",
            )
        else:
            logger.info(f"✅ Reloaded {successes} {description} cogs in {elapsed:.1f}s")

    async def _async_reload_extension_quiet(self, extension: str) -> None:
        """Quietly reload an extension without individual logging."""
        try:
            # Clear related module cache entries before reloading
            if modules_to_clear := [key for key in sys.modules if key.startswith(extension)]:
                for module_key in modules_to_clear:
                    del sys.modules[module_key]

            # Reload the extension
            await self.bot.reload_extension(extension)

        except commands.ExtensionNotLoaded:
            try:
                # Try to load it if it wasn't loaded before
                await self.bot.load_extension(extension)
                logger.info(f"✅ Loaded new extension {extension}")

                # Update our mapping
                path = path_from_extension(extension)
                self.path_to_extension[str(path)] = extension
            except commands.ExtensionError as e:
                logger.error(f"❌ Failed to load new extension {extension}: {e}")
                if sentry_sdk.is_initialized():
                    sentry_sdk.capture_exception(e)
                raise
        except commands.ExtensionError as e:
            logger.error(f"❌ Failed to reload extension {extension}: {e}")
            if sentry_sdk.is_initialized():
                sentry_sdk.capture_exception(e)
            raise

    def _get_flag_classes_used(self, extension_name: str) -> bool:
        """Get list of flag classes used by an extension."""
        try:
            # Get the module object
            module = sys.modules.get(extension_name)
            if not module or not hasattr(module, "__file__"):
                return False

            module_file = module.__file__
            if not module_file or not Path(module_file).exists():
                return False

            # Read the source code
            with Path(module_file).open(encoding="utf-8") as f:
                source = f.read()

            # Pattern to match flag class imports
            pattern = r"from\s+tux\.utils\.flags\s+import\s+([^#\n]+)"

            for match in re.finditer(pattern, source):
                import_items = match.group(1)

                # Parse the import list (handle both single line and multiline)
                import_items = re.sub(r"[()]", "", import_items)
                items = [item.strip() for item in import_items.split(",")]

                # Check if any imported item is a flag class
                for item in items:
                    if item.endswith("Flags"):
                        return True

        except Exception as e:
            logger.debug(f"Error analyzing {extension_name} for flag usage: {e}")
            return False
        else:
            return False

    def _cog_uses_flag_classes(self, extension_name: str) -> bool:
        """Check if a cog actually uses flag classes (not just generate_usage)."""
        return bool(self._get_flag_classes_used(extension_name))

    def debug_dependencies(self, module_name: str) -> dict[str, Any]:
        """Debug method to get dependency information for a module."""
        return {
            "direct_dependents": list(self.dependency_graph.get_dependents(module_name)),
            "transitive_dependents": list(self.dependency_graph.get_transitive_dependents(module_name)),
            "dependent_cogs": self._get_dependent_extensions(module_name),
            "all_loaded_cogs": list(self.bot.extensions.keys()),
            "dependency_graph_size": len(self.dependency_graph.get_all_tracked_modules()),
        }


def watch(
    path: str = "cogs",
    preload: bool = False,
    recursive: bool = True,
    debug: bool = True,
    colors: bool = True,
    default_logger: bool = True,
) -> Callable[[F], F]:
    """
    Enhanced decorator to watch for file changes and reload cogs.

    Inspired by cogwatch but with advanced dependency tracking and change detection.
    Works with the existing CogLoader system for initial loading.

    Parameters
    ----------
    path : str, optional
        The path to watch for changes, by default "cogs"
    preload : bool, optional
        Deprecated - use CogLoader.setup() for initial loading, by default False
    recursive : bool, optional
        Whether to watch recursively, by default True
    debug : bool, optional
        Whether to only run when Python's __debug__ flag is True, by default True
    colors : bool, optional
        Whether to use colorized output (reserved for future use), by default True
    default_logger : bool, optional
        Whether to use default logger configuration (reserved for future use), by default True

    Returns
    -------
    Callable
        The decorated function.

    Examples
    --------
    >>> @watch(path="cogs", debug=False)
    >>> async def on_ready(self):
    >>>     print("Bot ready with hot reloading!")
    """

    def decorator(func: F) -> F:
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Check debug flag - only run hot reloader in debug mode unless disabled
            if debug and not __debug__:
                logger.info("Hot reload disabled: Python not running in debug mode (use -O to disable debug)")
                return await func(self, *args, **kwargs)

            # Run the original function first
            result = await func(self, *args, **kwargs)

            # Warn about deprecated preload option
            if preload:
                logger.warning("preload=True is deprecated. Use CogLoader.setup() for initial cog loading.")

            try:
                # Start watching for file changes
                watch_path = Path(__file__).parent.parent / path
                watcher = CogWatcher(self, str(watch_path), recursive=recursive)
                watcher.start()

                # Store the watcher reference so it doesn't get garbage collected
                self.cog_watcher = watcher

                logger.info("🔥 Hot reload active")
            except Exception as e:
                logger.error(f"Failed to start hot reload system: {e}")
                if sentry_sdk.is_initialized():
                    sentry_sdk.capture_exception(e)

            return result

        return cast(F, wrapper)

    return decorator


def auto_discover_cogs(path: str = "cogs") -> list[str]:
    """
    Discover all potential cog modules in a directory.

    Note: Consider using CogLoader.setup() for actual cog loading.

    Parameters
    ----------
    path : str, optional
        Directory to search, by default "cogs"

    Returns
    -------
    list[str]
        List of discovered extension names
    """
    base_dir = Path(__file__).parent.parent
    watch_path = base_dir / path

    if not watch_path.exists():
        logger.warning(f"Cog discovery path does not exist: {watch_path}")
        return []

    discovered: list[str] = []

    try:
        for py_file in watch_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            try:
                rel_path = py_file.relative_to(base_dir)
                extension_name = str(rel_path.with_suffix("")).replace(os.sep, ".")
                extension_name = f"tux.{extension_name}"
                discovered.append(extension_name)
            except ValueError:
                continue
    except Exception as e:
        logger.error(f"Error during cog discovery: {e}")
        if sentry_sdk.is_initialized():
            sentry_sdk.capture_exception(e)
        return []
    else:
        return sorted(discovered)


class HotReload(commands.Cog):
    """Hot reload cog for backward compatibility and direct usage."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        logger.debug(f"Initializing HotReload cog with {len(bot.extensions)} loaded extensions")

        try:
            # Watch the entire tux directory, not just cogs, to catch utility changes
            watch_path = Path(__file__).parent.parent
            self.watcher = CogWatcher(bot, str(watch_path), recursive=True)
            self.watcher.start()
        except Exception as e:
            logger.error(f"Failed to initialize hot reload watcher: {e}")
            if sentry_sdk.is_initialized():
                sentry_sdk.capture_exception(e)
            raise

    async def cog_unload(self) -> None:
        """Clean up resources when the cog is unloaded."""
        logger.debug("Unloading HotReload cog")
        try:
            if hasattr(self, "watcher"):
                self.watcher.stop()
        except Exception as e:
            logger.error(f"Error during HotReload cog unload: {e}")


async def setup(bot: commands.Bot) -> None:
    """Set up the hot reload cog."""
    logger.info("Setting up hot reloader")
    logger.debug(f"Bot has {len(bot.extensions)} extensions loaded")

    # Validate system requirements
    if validation_issues := validate_hot_reload_requirements():
        logger.warning(f"Hot reload setup issues detected: {validation_issues}")
        for issue in validation_issues:
            logger.warning(f"  - {issue}")

    try:
        await bot.add_cog(HotReload(bot))
    except Exception as e:
        logger.error(f"Failed to setup hot reload cog: {e}")
        if sentry_sdk.is_initialized():
            sentry_sdk.capture_exception(e)
        raise


def validate_hot_reload_requirements() -> list[str]:
    """
    Validate system requirements for hot reload functionality.

    Returns
    -------
    list[str]
        List of validation issues found, empty if all good.
    """
    issues: list[str] = []

    # Check if we're in debug mode
    if not __debug__:
        issues.append("Python not running in debug mode (use python without -O flag)")

    # Check if required modules are available
    try:
        import watchdog

        if not hasattr(watchdog, "observers"):
            issues.append("watchdog.observers not available")
    except ImportError:
        issues.append("watchdog package not installed")

    # Check if we have access to modify sys.modules
    try:
        test_module = "test_hot_reload_module"
        if test_module in sys.modules:
            del sys.modules[test_module]
    except Exception:
        issues.append("Cannot modify sys.modules (required for hot reloading)")

    # Check if asyncio event loop is available
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        issues.append("No running asyncio event loop (hot reload must be used in async context)")

    # Check file system permissions
    base_dir = Path(__file__).parent.parent
    if not base_dir.exists():
        issues.append(f"Base directory does not exist: {base_dir}")
    elif not os.access(base_dir, os.R_OK):
        issues.append(f"No read access to base directory: {base_dir}")

    return issues
