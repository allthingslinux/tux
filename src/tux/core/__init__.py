"""Core dependency injection module for Tux bot.

This module provides the dependency injection infrastructure including:
- Service container for managing object lifecycles
- Service interfaces using Python protocols
- Concrete service implementations
- Service registry for centralized configuration
- Enhanced base cog with automatic dependency injection
"""

from tux.core.base_cog import BaseCog
from tux.core.container import (
    ServiceContainer,
    ServiceDescriptor,
    ServiceLifetime,
    ServiceRegistrationError,
    ServiceResolutionError,
)
from tux.core.interfaces import IBotService, IConfigService
from tux.core.service_registry import ServiceRegistry
from tux.core.services import BotService, ConfigService
from tux.database.service import DatabaseService

__all__ = [
    "BaseCog",
    "BotService",
    "ConfigService",
    "DatabaseService",
    "IBotService",
    "IConfigService",
    "ServiceContainer",
    "ServiceDescriptor",
    "ServiceLifetime",
    "ServiceRegistrationError",
    "ServiceRegistry",
    "ServiceResolutionError",
]
