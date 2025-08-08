# 001 - Dependency Injection System Implementation Examples

## Overview

This document provides concrete code examples for implementing the dependency injection system that eliminates 35+ direct database instantiations and enables modern architectural patterns.

---

## Current State Analysis

### ❌ Before: Direct Instantiation Pattern

**Typical Cog Implementation (35+ files follow this pattern):**

```python
# tux/cogs/moderation/ban.py
from discord.ext import commands
from tux.bot import Tux
from tux.database.controllers import DatabaseController

class BanCog(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()  # ❌ Direct instantiation
        
    @commands.command()
    async def ban(self, ctx: commands.Context, user: discord.Member, *, reason: str = None) -> None:
        # Use self.db directly
        await self.db.ban_user(ctx.guild.id, user.id, reason)
```

**Problems with Current Pattern:**
- ❌ Every cog creates its own DatabaseController instance
- ❌ Testing requires full database setup
- ❌ No way to mock or substitute services
- ❌ Tight coupling between cogs and concrete implementations
- ❌ Resource waste from multiple instances

---

## Proposed Implementation

### ✅ After: Dependency Injection Pattern

#### 1. Service Container Implementation

```python
# tux/core/container.py (Enhanced from audit/core/container.py)
from __future__ import annotations

import inspect
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar, get_type_hints

from loguru import logger

T = TypeVar("T")

class ServiceLifetime(Enum):
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"

class ServiceContainer:
    """Lightweight dependency injection container."""
    
    def __init__(self) -> None:
        self._services: dict[type, ServiceDescriptor] = {}
        self._singletons: dict[type, Any] = {}
        self._scoped_instances: dict[type, Any] = {}
    
    def register_singleton(self, service_type: type[T], implementation: type[T] | None = None) -> ServiceContainer:
        """Register a service as singleton."""
        impl_type = implementation or service_type
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            implementation_type=impl_type,
            lifetime=ServiceLifetime.SINGLETON,
        )
        logger.debug(f"Registered singleton: {service_type.__name__} -> {impl_type.__name__}")
        return self
    
    def get(self, service_type: type[T]) -> T:
        """Get a service instance with automatic dependency resolution."""
        if service_type not in self._services:
            raise ValueError(f"Service {service_type.__name__} is not registered")
        
        descriptor = self._services[service_type]
        
        # Return existing singleton
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if service_type in self._singletons:
                return self._singletons[service_type]
        
        # Create new instance with dependency injection
        instance = self._create_instance(descriptor)
        
        # Store singleton
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            self._singletons[service_type] = instance
        
        return instance
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create instance with constructor dependency injection."""
        try:
            sig = inspect.signature(descriptor.implementation_type.__init__)
            type_hints = get_type_hints(descriptor.implementation_type.__init__)
            kwargs = {}
            
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue
                
                param_type = type_hints.get(param_name, param.annotation)
                if param_type != inspect.Parameter.empty:
                    dependency = self.get_optional(param_type)
                    if dependency is not None:
                        kwargs[param_name] = dependency
            
            return descriptor.implementation_type(**kwargs)
        except Exception as e:
            logger.error(f"Failed to create {descriptor.implementation_type.__name__}: {e}")
            return descriptor.implementation_type()
```

#### 2. Service Interfaces

```python
# tux/core/interfaces.py (Enhanced from audit/core/interfaces.py)
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Protocol

class IDatabaseService(Protocol):
    """Interface for database operations."""
    
    def get_controller(self) -> Any:
        """Get the database controller instance."""
        ...
    
    async def execute_query(self, query: str, params: tuple = ()) -> Any:
        """Execute a database query."""
        ...

class IBotService(Protocol):
    """Interface for bot operations."""
    
    @property
    def latency(self) -> float:
        """Get bot latency."""
        ...
    
    def get_user(self, user_id: int) -> Any:
        """Get user by ID."""
        ...
    
    def get_emoji(self, name: str) -> Any:
        """Get emoji by name."""
        ...

class IConfigService(Protocol):
    """Interface for configuration access."""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        ...
```

#### 3. Service Implementations

```python
# tux/core/services.py (Enhanced from audit/core/services.py)
from __future__ import annotations
from typing import Any

from tux.core.interfaces import IDatabaseService, IBotService, IConfigService
from tux.database.controllers import DatabaseController
from tux.utils.config import Config

class DatabaseService(IDatabaseService):
    """Database service implementation."""
    
    def __init__(self) -> None:
        self._controller = DatabaseController()
    
    def get_controller(self) -> DatabaseController:
        """Get the database controller instance."""
        return self._controller
    
    async def execute_query(self, query: str, params: tuple = ()) -> Any:
        """Execute a database query."""
        return await self._controller.execute_query(query, params)

class BotService(IBotService):
    """Bot service implementation."""
    
    def __init__(self, bot: Any) -> None:
        self._bot = bot
    
    @property
    def latency(self) -> float:
        """Get bot latency."""
        return self._bot.latency
    
    def get_user(self, user_id: int) -> Any:
        """Get user by ID."""
        return self._bot.get_user(user_id)
    
    def get_emoji(self, name: str) -> Any:
        """Get emoji by name."""
        return self._bot.emoji_manager.get(name)

class ConfigService(IConfigService):
    """Configuration service implementation."""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return getattr(Config, key, default)
```

#### 4. Service Registry

```python
# tux/core/service_registry.py
from __future__ import annotations
from typing import TYPE_CHECKING

from tux.core.container import ServiceContainer
from tux.core.interfaces import IDatabaseService, IBotService, IConfigService
from tux.core.services import DatabaseService, BotService, ConfigService

if TYPE_CHECKING:
    from tux.bot import Tux

class ServiceRegistry:
    """Central registry for configuring services."""
    
    @staticmethod
    def configure_container(bot: Tux) -> ServiceContainer:
        """Configure the service container with all services."""
        container = ServiceContainer()
        
        # Register core services as singletons
        container.register_singleton(IDatabaseService, DatabaseService)
        container.register_singleton(IConfigService, ConfigService)
        
        # Register bot service with bot instance
        container.register_instance(IBotService, BotService(bot))
        
        return container
```

#### 5. Enhanced Base Cog

```python
# tux/core/base_cog.py (Enhanced from audit/core/base_cog.py)
from __future__ import annotations
from typing import TYPE_CHECKING

from discord.ext import commands
from tux.core.interfaces import IDatabaseService, IBotService, IConfigService

if TYPE_CHECKING:
    from tux.bot import Tux

class BaseCog(commands.Cog):
    """Base cog with dependency injection support."""
    
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self._container = getattr(bot, 'container', None)
        
        # Inject services if container is available
        if self._container:
            self.db_service = self._container.get_optional(IDatabaseService)
            self.bot_service = self._container.get_optional(IBotService)
            self.config_service = self._container.get_optional(IConfigService)
        else:
            # Fallback for backward compatibility
            self._init_fallback_services()
    
    def _init_fallback_services(self) -> None:
        """Fallback service initialization."""
        from tux.database.controllers import DatabaseController
        self.db_service = DatabaseService()
        self.bot_service = BotService(self.bot)
        self.config_service = ConfigService()
    
    @property
    def db(self) -> Any:
        """Backward compatibility property."""
        return self.db_service.get_controller() if self.db_service else None
```

#### 6. Bot Integration

```python
# tux/bot.py (Integration changes)
from tux.core.service_registry import ServiceRegistry

class Tux(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.container = None
    
    async def setup(self) -> None:
        """Setup bot with dependency injection."""
        try:
            # Initialize database first
            await self._setup_database()
            
            # ✅ NEW: Initialize dependency injection
            self.container = ServiceRegistry.configure_container(self)
            logger.info("Dependency injection container initialized")
            
            # Load extensions and cogs
            await self._load_extensions()
            await self._load_cogs()
            
        except Exception as e:
            logger.critical(f"Critical error during setup: {e}")
            raise
```

#### 7. Migrated Cog Example

```python
# tux/cogs/moderation/ban.py (After migration)
from discord.ext import commands
from tux.core.base_cog import BaseCog

class BanCog(BaseCog):  # ✅ Inherits from BaseCog
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)  # ✅ Services injected automatically
        
    @commands.command()
    async def ban(self, ctx: commands.Context, user: discord.Member, *, reason: str = None) -> None:
        # ✅ Use injected service
        if self.db_service:
            controller = self.db_service.get_controller()
            await controller.ban_user(ctx.guild.id, user.id, reason)
        else:
            # Fallback for backward compatibility
            from tux.database.controllers import DatabaseController
            db = DatabaseController()
            await db.ban_user(ctx.guild.id, user.id, reason)
```

---

## Migration Steps

### Phase 1: Infrastructure Setup (Week 1-2)

1. **Create Core Infrastructure:**
```bash
# Create new files
touch tux/core/__init__.py
touch tux/core/container.py
touch tux/core/interfaces.py
touch tux/core/services.py
touch tux/core/service_registry.py
```

2. **Implement Service Container:**
```python
# Copy and enhance audit/core/container.py
# Add error handling and logging
# Add service descriptor functionality
```

3. **Define Service Interfaces:**
```python
# Create protocol-based interfaces
# Define common service contracts
# Ensure backward compatibility
```

### Phase 2: Service Implementation (Week 2-3)

1. **Implement Core Services:**
```python
# DatabaseService - wraps existing DatabaseController
# BotService - abstracts bot operations
# ConfigService - centralizes configuration access
```

2. **Create Service Registry:**
```python
# Central configuration point
# Service lifetime management
# Dependency resolution
```

### Phase 3: Base Cog Enhancement (Week 3-4)

1. **Enhance BaseCog:**
```python
# Add dependency injection support
# Maintain backward compatibility
# Provide fallback mechanisms
```

2. **Create Specialized Base Classes:**
```python
# ModerationBaseCog
# UtilityBaseCog
# ServiceBaseCog
```

### Phase 4: Cog Migration (Week 4-7)

1. **Batch Migration Strategy:**
```python
# Week 4: Moderation cogs (8-10 files)
# Week 5: Utility cogs (8-10 files)
# Week 6: Service cogs (8-10 files)
# Week 7: Remaining cogs (5-7 files)
```

2. **Migration Pattern:**
```python
# Change inheritance: commands.Cog -> BaseCog
# Remove direct instantiation: self.db = DatabaseController()
# Use injected services: self.db_service.get_controller()
# Add fallback for compatibility
```

---

## Testing Examples

### Unit Testing with Mocks

```python
# tests/test_ban_cog.py
import pytest
from unittest.mock import Mock, AsyncMock
from tux.modules.moderation.ban import BanCog
from tux.core.container import ServiceContainer
from tux.core.interfaces import IDatabaseService

class MockDatabaseService:
    def __init__(self):
        self.controller = Mock()
        self.controller.ban_user = AsyncMock()
    
    def get_controller(self):
        return self.controller

@pytest.fixture
def mock_bot():
    bot = Mock()
    container = ServiceContainer()
    container.register_instance(IDatabaseService, MockDatabaseService())
    bot.container = container
    return bot

@pytest.mark.asyncio
async def test_ban_command(mock_bot):
    # Arrange
    cog = BanCog(mock_bot)
    ctx = Mock()
    user = Mock()
    user.id = 12345
    ctx.guild.id = 67890
    
    # Act
    await cog.ban(ctx, user, reason="Test ban")
    
    # Assert
    cog.db_service.get_controller().ban_user.assert_called_once_with(67890, 12345, "Test ban")
```

### Integration Testing

```python
# tests/integration/test_dependency_injection.py
import pytest
from tux.bot import Tux
from tux.core.service_registry import ServiceRegistry
from tux.core.interfaces import IDatabaseService

@pytest.mark.asyncio
async def test_service_container_integration():
    # Arrange
    bot = Mock()
    
    # Act
    container = ServiceRegistry.configure_container(bot)
    
    # Assert
    assert container.is_registered(IDatabaseService)
    db_service = container.get(IDatabaseService)
    assert db_service is not None
    assert hasattr(db_service, 'get_controller')
```

### Performance Testing

```python
# tests/performance/test_di_performance.py
import time
import pytest
from tux.core.container import ServiceContainer
from tux.core.interfaces import IDatabaseService
from tux.core.services import DatabaseService

def test_service_resolution_performance():
    # Arrange
    container = ServiceContainer()
    container.register_singleton(IDatabaseService, DatabaseService)
    
    # Act - First resolution (creation)
    start_time = time.time()
    service1 = container.get(IDatabaseService)
    first_resolution_time = time.time() - start_time
    
    # Act - Second resolution (cached)
    start_time = time.time()
    service2 = container.get(IDatabaseService)
    second_resolution_time = time.time() - start_time
    
    # Assert
    assert service1 is service2  # Same instance (singleton)
    assert second_resolution_time < first_resolution_time  # Cached is faster
    assert first_resolution_time < 0.001  # Less than 1ms
    assert second_resolution_time < 0.0001  # Less than 0.1ms
```

---

## Success Metrics

### Quantitative Targets
- ✅ **35+ direct instantiations eliminated**: `grep -r "DatabaseController()" tux/cogs/` returns 0 results
- ✅ **100% cog migration**: All cogs inherit from BaseCog
- ✅ **Zero performance degradation**: Bot startup time unchanged
- ✅ **90% boilerplate reduction**: Average 15 lines removed per cog

### Validation Commands
```bash
# Check for remaining direct instantiations
grep -r "DatabaseController()" tux/cogs/

# Check for BaseCog inheritance
grep -r "class.*Cog.*BaseCog" tux/cogs/ | wc -l

# Check container registration
python -c "from tux.core.service_registry import ServiceRegistry; from tux.bot import Tux; bot = Tux(); container = ServiceRegistry.configure_container(bot); print(f'Services registered: {len(container.get_registered_services())}')"
```

### Testing Validation
```bash
# Run unit tests with mocking
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run performance tests
pytest tests/performance/ -v --benchmark-only
```

This dependency injection implementation provides a solid foundation for all other improvements while maintaining backward compatibility and enabling comprehensive testing.
