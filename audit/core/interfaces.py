"""Core service interfaces for dependency injection."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class IServiceContainer(Protocol):
    """Interface for the dependency injection container."""

    def register_singleton(self, service_type: type[T], implementation: type[T] | None = None) -> None:
        """Register a service as singleton."""
        ...

    def register_transient(self, service_type: type[T], implementation: type[T] | None = None) -> None:
        """Register a service as transient."""
        ...

    def register_instance(self, service_type: type[T], instance: T) -> None:
        """Register a specific instance."""
        ...

    def get(self, service_type: type[T]) -> T:
        """Get a service instance."""
        ...

    def get_optional(self, service_type: type[T]) -> T | None:
        """Get a service instance or None if not registered."""
        ...


class IDatabaseService(ABC):
    """Interface for database operations."""

    @abstractmethod
    def get_controller(self) -> Any:
        """Get the database controller instance."""
        ...


class IExternalAPIService(ABC):
    """Interface for external API services."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the external service is available."""
        ...


class IEmbedService(ABC):
    """Interface for embed creation services."""

    @abstractmethod
    def create_info_embed(self, title: str, description: str, **kwargs: Any) -> Any:
        """Create an info embed."""
        ...

    @abstractmethod
    def create_error_embed(self, title: str, description: str, **kwargs: Any) -> Any:
        """Create an error embed."""
        ...

    @abstractmethod
    def create_success_embed(self, title: str, description: str, **kwargs: Any) -> Any:
        """Create a success embed."""
        ...


class IConfigurationService(ABC):
    """Interface for configuration management."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        ...

    @abstractmethod
    def get_required(self, key: str) -> Any:
        """Get a required configuration value."""
        ...


class ILoggingService(ABC):
    """Interface for logging services."""

    @abstractmethod
    def log_info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        ...

    @abstractmethod
    def log_error(self, message: str, error: Exception | None = None, **kwargs: Any) -> None:
        """Log an error message."""
        ...

    @abstractmethod
    def log_warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        ...
