"""Configuration and exceptions for hot reload system."""

from dataclasses import dataclass, field
from pathlib import Path

from tux.shared.constants import (
    DEPENDENCY_CACHE_SIZE,
    MAX_DEPENDENCY_DEPTH,
    RELOAD_TIMEOUT,
)


@dataclass(frozen=True)
class HotReloadConfig:
    """Configuration for the hot reload system."""

    # Core settings
    enabled: bool = True
    watch_directories: list[Path] = field(default_factory=lambda: [Path("src/tux")])
    file_patterns: list[str] = field(default_factory=lambda: ["*.py"])
    ignore_patterns: list[str] = field(
        default_factory=lambda: ["__pycache__", "*.pyc", ".git"],
    )

    # Performance settings
    debounce_delay: float = 0.5
    max_reload_attempts: int = 3
    reload_timeout: float = RELOAD_TIMEOUT

    # Dependency tracking
    track_dependencies: bool = True
    max_dependency_depth: int = MAX_DEPENDENCY_DEPTH
    dependency_cache_size: int = DEPENDENCY_CACHE_SIZE

    # Error handling
    continue_on_error: bool = True
    log_level: str = "INFO"

    # Advanced features
    enable_syntax_checking: bool = True
    enable_performance_monitoring: bool = True
    enable_class_tracking: bool = True

    def __post_init__(self) -> None:
        """
        Validate configuration after initialization.

        Raises
        ------
        ValueError
            If any configuration value is invalid.
        """
        if self.debounce_delay < 0:
            msg = "debounce_delay must be non-negative"
            raise ValueError(msg)
        if self.max_reload_attempts < 1:
            msg = "max_reload_attempts must be at least 1"
            raise ValueError(msg)
        if self.reload_timeout <= 0:
            msg = "reload_timeout must be positive"
            raise ValueError(msg)


class HotReloadError(Exception):
    """Base exception for hot reload system errors."""


class DependencyResolutionError(HotReloadError):
    """Raised when dependency resolution fails."""


class FileWatchError(HotReloadError):
    """Raised when file watching encounters an error."""


class ModuleReloadError(HotReloadError):
    """Raised when module reloading fails."""


class ConfigurationError(HotReloadError):
    """Raised when configuration is invalid."""


def validate_config(config: HotReloadConfig) -> None:
    """
    Validate hot reload configuration.

    Raises
    ------
    ConfigurationError
        If the configuration is invalid.
    """
    if not config.watch_directories:
        msg = "At least one watch directory must be specified"
        raise ConfigurationError(msg)

    for directory in config.watch_directories:
        if not directory.exists():
            msg = f"Watch directory does not exist: {directory}"
            raise ConfigurationError(msg)
        if not directory.is_dir():
            msg = f"Watch path is not a directory: {directory}"
            raise ConfigurationError(msg)

    if config.debounce_delay < 0:
        msg = "Debounce delay must be non-negative"
        raise ConfigurationError(msg)

    if config.max_reload_attempts < 1:
        msg = "Max reload attempts must be at least 1"
        raise ConfigurationError(msg)
