# Implementation Plan

- [x] 1. Create core dependency injection infrastructure
  - Set up the core module structure and implement the foundational container
  - Create the directory structure for dependency injection components
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 1.1 Create core module structure and service container
  - Create `tux/core/__init__.py` file to establish the core module
  - Implement `tux/core/container.py` with ServiceContainer class supporting singleton, transient, and scoped lifetimes
  - Add ServiceLifetime enum and ServiceDescriptor dataclass
  - Implement service registration methods (register_singleton, register_transient, register_instance)
  - Add automatic dependency resolution through constructor injection
  - Include comprehensive error handling and logging
  - Write unit tests for service container functionality
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 1.2 Implement service interfaces using Python protocols
  - Create `tux/core/interfaces.py` with protocol-based service interfaces
  - Define IDatabaseService protocol with get_controller and execute_query methods
  - Define IBotService protocol with latency, get_user, and get_emoji methods
  - Define IConfigService protocol with get method for configuration access
  - Add comprehensive type hints and docstrings for all interface methods
  - Write unit tests to verify interface contracts
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 1.3 Create concrete service implementations
  - Create `tux/core/services.py` with concrete service implementations
  - Implement DatabaseService class that wraps existing DatabaseController
  - Implement BotService class that provides access to bot properties and operations
  - Implement ConfigService class that wraps configuration utilities
  - Ensure all implementations maintain backward compatibility with existing functionality
  - Add error handling and logging to service implementations
  - Write unit tests for each service implementation
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 2. Implement service registry and bot integration
  - Create centralized service registration and integrate with bot startup process
  - Implement service registry for managing service configuration
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 2.1 Create service registry for centralized configuration
  - Create `tux/core/service_registry.py` with ServiceRegistry class
  - Implement configure_container static method that registers all core services
  - Register DatabaseService and ConfigService as singletons
  - Register BotService with bot instance dependency
  - Add proper error handling for service registration failures
  - Include logging for service registration process
  - Write unit tests for service registry functionality
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 2.2 Integrate dependency injection container with bot startup
  - Modify `tux/bot.py` to initialize service container during startup
  - Add container property to Tux bot class
  - Initialize container in setup() method before loading cogs
  - Add error handling for container initialization failures
  - Ensure container is available to cogs during loading
  - Add logging for container initialization process
  - Write integration tests for bot startup with dependency injection
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 3. Create enhanced base cog with dependency injection support
  - Implement base cog class that automatically injects services while maintaining backward compatibility
  - Create enhanced base cog with automatic service injection
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 3.1 Implement BaseCog with automatic dependency injection
  - Create `tux/core/base_cog.py` with enhanced BaseCog class
  - Implement automatic service injection through constructor
  - Add fallback mechanism for backward compatibility when container is unavailable
  - Provide access to injected services through standard properties (db_service, bot_service, config_service)
  - Maintain backward compatibility with existing property access patterns (self.db)
  - Add comprehensive error handling for service injection failures
  - Write unit tests for BaseCog with both injection and fallback scenarios
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 4. Set up comprehensive testing infrastructure
  - Create testing utilities and fixtures for dependency injection system
  - Implement testing infrastructure for mocking and validation
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 4.1 Create testing fixtures and mock services
  - Create `tests/fixtures/dependency_injection.py` with testing utilities
  - Implement MockDatabaseService, MockBotService, and MockConfigService classes
  - Create pytest fixtures for mock container and mock bot with container
  - Add helper functions for creating test containers with mock services
  - Implement performance testing utilities for measuring service resolution times
  - Write example unit tests demonstrating how to test cogs with dependency injection
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 4.2 Create integration tests for full system
  - Create `tests/integration/test_dependency_injection.py` for full system testing
  - Test complete bot startup with container initialization
  - Test service registration and resolution in real environment
  - Test cog loading with dependency injection
  - Verify end-to-end functionality with injected services
  - Add performance tests to ensure no degradation in startup time
  - _Requirements: 8.3, 8.4, 8.5_

- [x] 5. Migrate moderation base cog to use dependency injection
  - Convert the ModerationCogBase to use BaseCog and injected services
  - Update the base class that all moderation cogs inherit from
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 5.1 Migrate ModerationCogBase to use dependency injection
  - Update `tux/cogs/moderation/__init__.py` ModerationCogBase to inherit from BaseCog
  - Replace direct DatabaseController instantiation with injected db_service
  - Update all methods to use injected services instead of self.db
  - Maintain all existing functionality and method signatures
  - Add fallback mechanisms for backward compatibility
  - Write unit tests for migrated ModerationCogBase using mock services
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 6. Migrate utility and service cogs to use dependency injection
  - Convert remaining cog categories to use dependency injection
  - Migrate utility and service cogs to new architecture
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 6.1 Migrate utility cogs with direct DatabaseController usage
  - Update `tux/cogs/utility/afk.py` to inherit from BaseCog and use injected services
  - Update `tux/cogs/utility/poll.py` to inherit from BaseCog and use injected services
  - Update `tux/cogs/utility/remindme.py` to inherit from BaseCog and use injected services
  - Update `tux/cogs/utility/self_timeout.py` to inherit from BaseCog and use injected services
  - Replace direct DatabaseController instantiations with injected db_service
  - Maintain all existing functionality and command behavior
  - Write unit tests for migrated utility cogs
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 6.2 Migrate service cogs with direct DatabaseController usage
  - Update `tux/cogs/services/levels.py` to inherit from BaseCog and use injected services
  - Update `tux/cogs/services/influxdblogger.py` to inherit from BaseCog and use injected services
  - Update `tux/cogs/services/starboard.py` to inherit from BaseCog and use injected services
  - Replace direct DatabaseController instantiations with injected db_service
  - Maintain all existing functionality and service capabilities
  - Write unit tests for migrated service cogs
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 6.3 Migrate levels and guild cogs with direct DatabaseController usage
  - Update `tux/cogs/levels/level.py` to inherit from BaseCog and use injected services
  - Update `tux/cogs/levels/levels.py` to inherit from BaseCog and use injected services
  - Update `tux/cogs/guild/setup.py` to inherit from BaseCog and use injected services
  - Update `tux/cogs/guild/config.py` to inherit from BaseCog and use injected services
  - Replace direct DatabaseController instantiations with injected db_service
  - Maintain all existing functionality and administrative capabilities
  - Write unit tests for migrated cogs
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 6.4 Migrate snippets base cog to use dependency injection
  - Update `tux/cogs/snippets/__init__.py` SnippetsBaseCog to inherit from BaseCog
  - Replace direct DatabaseController instantiation with injected db_service
  - Update all methods to use injected services instead of self.db
  - Maintain all existing functionality and method signatures
  - Add fallback mechanisms for backward compatibility
  - Write unit tests for migrated SnippetsBaseCog using mock services
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 7. Implement validation and success metrics
  - Create validation tools and measure implementation success
  - Implement success metrics validation and cleanup
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 7.1 Create validation scripts and success metrics
  - Create `scripts/validate_dependency_injection.py` script to check migration completeness
  - Implement checks for zero direct DatabaseController instantiations in cogs
  - Add validation for 100% BaseCog inheritance across all cogs
  - Create performance measurement tools for startup time and service resolution
  - Implement boilerplate reduction measurement tools
  - Add automated validation commands for continuous verification
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 7.2 Final cleanup and optimization
  - Remove any unused direct instantiation patterns
  - Optimize service container performance for production use
  - Clean up any temporary compatibility code that is no longer needed
  - Update documentation to reflect new dependency injection patterns
  - Run comprehensive test suite to ensure all functionality is preserved
  - Verify all success metrics are met and document results
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
