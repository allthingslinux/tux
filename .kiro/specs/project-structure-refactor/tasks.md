# Implementation Plan

- [x] 1. Create new directory structure and base infrastructure
  - Create the new directory structure with all required folders
  - Set up base __init__.py files for proper Python package structure
  - Create tux/ui/, tux/utils/, tux/services/, tux/shared/, tux/modules/, tux/custom_modules/ directories
  - _Requirements: 1.1, 1.2, 3.1, 3.2_

- [x] 2. Migrate core infrastructure components
  - [x] 2.1 Move core components to tux/core/
    - Move tux/app.py to tux/core/app.py
    - Move tux/bot.py to tux/core/bot.py  
    - Move tux/cog_loader.py to tux/core/cog_loader.py
    - Update imports in moved files
    - Verify existing tux/core/ dependency injection system works
    - _Requirements: 1.1, 1.2, 7.1, 7.2, 8.1_

  - [x] 2.2 Update core module loading for new structure
    - Update cog_loader.py to discover modules from tux/modules/
    - Add support for loading from tux/custom_modules/
    - Ensure existing dependency injection continues to work
    - _Requirements: 3.1, 3.2, 5.1_

- [x] 3. Create shared utilities layer
  - [x] 3.1 Set up shared directory structure
    - Create tux/shared/ with proper __init__.py
    - Create tux/shared/config/ subdirectory
    - Move generic utilities to shared layer
    - _Requirements: 1.3, 8.1, 8.2_

  - [x] 3.2 Move shared utilities and configuration
    - Move tux/utils/constants.py to tux/shared/constants.py
    - Move tux/utils/exceptions.py to tux/shared/exceptions.py
    - Move tux/utils/functions.py to tux/shared/functions.py
    - Move tux/utils/regex.py to tux/shared/regex.py
    - Move tux/utils/substitutions.py to tux/shared/substitutions.py
    - Move tux/utils/config.py to tux/shared/config/settings.py
    - Move tux/utils/env.py to tux/shared/config/env.py
    - Update all imports across the codebase
    - _Requirements: 1.3, 8.1, 8.2_

- [x] 4. Migrate UI components
  - UI components are already properly located in tux/ui/
  - Verify all UI components continue to function
  - Test that embeds, views, modals, and buttons work correctly
  - _Requirements: 1.2, 5.2, 7.1, 7.2, 8.1_

- [x] 5. Migrate bot-specific utilities
  - [x] 5.1 Keep Discord-specific utilities in tux/utils/
    - Verify tux/utils/ascii.py remains in place
    - Verify tux/utils/banner.py remains in place
    - Verify tux/utils/checks.py remains in place
    - Verify tux/utils/converters.py remains in place
    - Verify tux/utils/emoji.py remains in place
    - Verify tux/utils/flags.py remains in place
    - Verify tux/utils/help_utils.py remains in place
    - _Requirements: 1.3, 8.1, 8.2_

  - [x] 5.2 Clean up utils directory
    - Remove files that were moved to shared/
    - Update tux/utils/__init__.py to only export bot-specific utilities
    - Verify all remaining utilities are Discord/bot-specific
    - _Requirements: 1.3, 8.1, 8.2_

- [ ] 6. Migrate services infrastructure
  - [x] 6.1 Create services directory structure
    - Create tux/services/ with proper __init__.py
    - Create tux/services/database/, tux/services/wrappers/, tux/services/handlers/ subdirectories
    - _Requirements: 1.2, 1.3, 7.1, 7.2, 8.1_

  - [x] 6.2 Move database components to services
    - Database files have been copied to tux/services/database/ but originals still exist
    - Remove original tux/database/ directory after verifying services version works
    - Update all imports from tux.database to tux.services.database
    - _Requirements: 1.2, 1.3, 7.1, 7.2, 8.1_

  - [x] 6.3 Move wrappers to services
    - Move tux/wrappers/ contents to tux/services/wrappers/
    - Update all imports from tux.wrappers to tux.services.wrappers
    - Remove original tux/wrappers/ directory
    - _Requirements: 1.2, 1.3, 7.1, 7.2, 8.1_

  - [x] 6.4 Move handlers to services
    - Move tux/handlers/ contents to tux/services/handlers/
    - Update all imports from tux.handlers to tux.services.handlers
    - Remove original tux/handlers/ directory
    - _Requirements: 1.2, 1.3, 7.1, 7.2, 8.1_

  - [x] 6.5 Move service utilities to services
    - Move tux/utils/logger.py to tux/services/logger.py
    - Move tux/utils/sentry.py to tux/services/sentry.py
    - Move tux/utils/hot_reload.py to tux/services/hot_reload.py
    - Update all imports across the codebase
    - _Requirements: 1.2, 1.3, 7.1, 7.2, 8.1_

- [x] 7. Convert cogs to modules
  - [x] 7.1 Migrate core modules (moderation, admin, guild, utility, info)
    - Move tux/cogs/moderation/ to tux/modules/moderation/
    - Move tux/cogs/admin/ to tux/modules/admin/
    - Move tux/cogs/guild/ to tux/modules/guild/
    - Move tux/cogs/utility/ to tux/modules/utility/
    - Move tux/cogs/info/ to tux/modules/info/
    - Update imports in all moved modules
    - _Requirements: 2.1, 2.2, 4.1, 5.1, 5.2_

  - [x] 7.2 Migrate additional modules (fun, levels, snippets, tools, services)
    - Move tux/cogs/fun/ to tux/modules/fun/
    - Move tux/cogs/levels/ to tux/modules/levels/
    - Move tux/cogs/snippets/ to tux/modules/snippets/
    - Move tux/cogs/tools/ to tux/modules/tools/
    - Move tux/cogs/services/ to tux/modules/services/
    - Update imports in all moved modules
    - _Requirements: 2.1, 2.2, 4.1, 5.1, 5.2_

- [x] 8. Update dependency injection system
  - [x] 8.1 Update service container for new structure
    - Update ServiceContainer to work with new directory structure
    - Update service discovery to use tux/services/ paths
    - Ensure existing dependency injection continues to work
    - _Requirements: 3.1, 3.2, 8.2, 8.3_

  - [x] 8.2 Update service registry for new structure
    - Refactor ServiceRegistry to work with tux/services/ structure
    - Update service registration to use new import paths
    - Test that all services are properly registered and accessible
    - _Requirements: 3.1, 3.2, 8.2, 8.3_

- [x] 9. Update all internal imports
  - Update imports in all core components to use tux/core/, tux/shared/
  - Update imports in all modules to use tux/modules/
  - Update imports in services to use tux/services/
  - Update imports to use tux/shared/ for shared utilities
  - Update imports to use tux/ui/ for UI components
  - Update imports to use tux/utils/ for bot-specific utilities
  - Verify no circular import dependencies exist
  - _Requirements: 7.1, 7.2, 8.1, 8.2, 8.3_

- [x] 10. Set up custom modules support
  - Create tux/custom_modules/ directory with README
  - Update cog loader to scan custom_modules directory
  - Create documentation for custom module development
  - Test loading custom modules works correctly
  - _Requirements: 3.1, 3.2, 5.1, 6.1_

- [x] 11. Update configuration and deployment
  - [x] 11.1 Update configuration management
    - Ensure configuration system works with new structure
    - Update environment variable handling in shared/config/
    - Test configuration loading in new structure
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 11.2 Update deployment and build processes
    - Update Docker configuration for new structure
    - Update any build scripts or deployment configs
    - Verify application entry points work correctly
    - _Requirements: 6.1, 6.2, 6.3_

- [-] 12. Update tests and documentation
  - [ ] 12.1 Migrate and update test structure
    - Update test directory structure to mirror new code organization
    - Update test imports to use new paths
    - Ensure all existing tests pass with new structure
    - Add tests for new module loading system
    - _Requirements: 7.3, 7.4_

  - [ ] 12.2 Update documentation and examples
    - Update README and documentation with new structure
    - Update development setup instructions
    - Document new module creation process
    - _Requirements: 4.1, 4.2, 4.3_

- [ ] 13. Validation and cleanup
  - [ ] 13.1 Comprehensive functionality testing
    - Test all Discord commands work identically
    - Verify all database operations function correctly
    - Test module loading and custom module support
    - Validate error handling and logging work properly
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ] 13.2 Performance and cleanup validation
    - Verify bot startup time is not significantly impacted
    - Test memory usage patterns with new structure
    - Remove old tux/cogs/ directory
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
