<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

* **Cursor Rules & Commands System**: Comprehensive system for managing AI-assisted development patterns
  * CLI tool for validating Cursor rules and commands (`uv run ai validate-rules`)
  * Comprehensive guides for creating Cursor rules and commands
  * Templates for rule and command documentation
  * Enhanced validation with frontmatter checking and large file exception support
  * README for Cursor rules and commands system
* **Docker Improvements**: Enhanced Docker setup and deployment
  * Production Docker Compose configuration (`compose.production.yaml`)
  * Multi-stage Containerfile build with common setup stage
  * Auto-login form plugin for Adminer database administration
  * Validation and date generation functions in Docker scripts
  * Enhanced CI/CD pipeline with validation and caching improvements
* **Documentation**: New self-hosting and installation guides
  * Bare metal installation guide
  * Enhanced self-hosting guide with detailed requirements and installation methods
  * CI/CD best practices documentation
* **Bot Infrastructure**: Improved initialization and setup
  * Prefix manager setup service for bot initialization
  * `VALID_LOG_LEVELS` constant exported from logging module
  * `SLOW_COG_LOAD_THRESHOLD` constant for performance monitoring
* **Test Structure Reorganization**: Comprehensive test reorganization from flat structure to domain-based organization
  * New test directories: `tests/core/`, `tests/database/`, `tests/services/`, `tests/shared/`, `tests/modules/`, `tests/help/`, `tests/plugins/`
  * Database model tests: creation, queries, relationships, serialization, performance, and timestamp functionality
  * Error extractor tests: arguments, flags, HTTP, permissions, roles, utilities, and integration tests
  * Config loader tests: basic loading, environment variable handling, and generation
  * Version system tests: module functions, version objects, and system integration
* **Test Fixture Improvements**: Enhanced test fixture organization and utilities
  * New `tests/fixtures/data_fixtures.py` for test constants and sample data
  * New `tests/fixtures/utils.py` with validation utilities for guild configs, guilds, and relationship integrity
  * Improved database fixture organization and PGlite management
* Database controller improvements with enhanced error handling and logging

### Changed

* **Cursor Rules System**: Refactored validation command structure and enhanced documentation
  * Updated AGENTS.md with Cursor rules and commands overview
  * Expanded and organized Cursor rules and commands documentation
  * Enhanced pre-commit configuration for commit message handling
* **Docker Configuration**: Updated Docker Compose and build processes
  * Updated Docker Compose configurations for production and development environments
  * Enhanced health checks and service management
  * Restructured Containerfile into multi-stage build with common setup
  * Enhanced database connection handling and startup logic in entrypoint script
  * Expanded `.dockerignore` to include additional files and directories
  * Disabled attestations in GitHub Actions for improved architecture visibility
* **Bot Architecture**: Improved initialization and error handling
  * Consolidated setup services with improved error handling
  * Simplified bot startup and enhanced shutdown handling
  * Streamlined prefix resolution
  * Enhanced configuration loading and data handling
  * Improved bot readiness checks and logging
* **Code Quality**: Enhanced error handling and type annotations across modules
  * Improved error handling in database migration tests
  * Enhanced logging configuration and error handling
  * Improved type annotations across multiple modules (AFK, Godbolt, TLDR, info, task monitor, decorators)
  * Enhanced error handling in validation, linting, and VSCode settings parsing
  * Improved error extractor tests for httpx exceptions
  * Enhanced database model relationship tests
* **Module Refactoring**: Improved code organization and functionality
  * Streamlined embed creation and improved boolean formatting in info module
  * Enhanced cache handling and command processing in TLDR module
  * Enhanced AFK management and filtering capabilities
  * Streamlined prefix management and improved cache handling
  * Enhanced cog loading process and improved performance monitoring
  * Replaced custom logging methods with loguru for consistency
  * Simplified `get_recent_cases` method and updated documentation
* **Documentation**: Updated guides and references
  * Updated command syntax in migration and development documentation
  * Updated validation command in AGENTS.md for consistency
  * Standardized command usage across documentation
  * Updated lifecycle and setup documentation for clarity
  * Removed outdated installation links and updated database installation references
* **CI/CD**: Enhanced workflows and automation
  * Optimized cache management in CI workflows
  * Updated workflows with improved permissions and error handling
  * Added checks for Cloudflare API token in preview deployment
* **Test Organization**: Reorganized tests from `tests/unit/` and `tests/integration/` to domain-specific directories
  * Core permission system tests moved to `tests/core/`
  * Database tests consolidated in `tests/database/` with comprehensive model coverage
  * Service layer tests organized in `tests/services/` with error handler and HTTP client tests
  * Shared utility tests moved to `tests/shared/` for config and version management
  * Module integration tests organized in `tests/modules/`
* **Test Fixtures**: Improved fixture organization with better separation of concerns
  * Consolidated test constants and sample data fixtures
  * Enhanced validation utilities for test data integrity
  * Improved PGlite process management and cleanup
* Database controller error handling and logging improvements
* Documentation updates for debugging, testing fixtures, and versioning

### Fixed

* **Validation**: Improved rule validation system
  * Added support for large file exceptions in rule validation
  * Enhanced error handling and frontmatter validation in rule files
  * Fixed pre-commit hook entry for cursor validation
* **Documentation**: Fixed command syntax and references
  * Updated command syntax in migration and development documentation
  * Fixed validation command in AGENTS.md for consistency
  * Updated related links in database management documentation
  * Fixed database installation link in configuration documentation
* **Testing**: Enhanced test reliability and accuracy
  * Enhanced error handling in database migration tests
  * Improved database model relationship tests and error handler assertions
  * Updated URL assertion in error extractor tests for accuracy
  * Enhanced logging tests to verify handler behavior
* **Configuration**: Fixed configuration and validation issues
  * Enhanced exception handling for VSCode settings parsing
  * Updated markdownlint configuration format
  * Specified exception types for improved error handling in validation and linting
* **TLDR Module**: Resolved cache directory path to avoid permission issues
* **Workflows**: Fixed CI/CD workflow issues
  * Updated permissions and error handling in docs workflow
  * Added checks for Cloudflare API token in preview deployment
  * Removed unnecessary exception handling for subprocess errors
* **Harmful Commands**: Fixed edge cases in harmful command detection
* **GitHub Badge**: Adjusted GitHub release badge boolean parameter
* **Base Cog**: Enhanced error handling and logging

### Removed

* **Legacy Files**: Cleaned up deprecated and outdated files
  * Removed `.trivyignore` file for deprecated vulnerability tracking
  * Removed FORCE_MIGRATE references from Docker and database documentation
  * Removed example Docker Compose override file
* **Legacy Test Structure**: Removed `tests/unit/` and `tests/integration/` directories in favor of domain-based organization
* **Deprecated Fixtures**: Removed `tests/fixtures/pglite_fixtures.py` and `tests/fixtures/test_data_fixtures.py` in favor of reorganized fixture structure

### Security

* Enhanced error handling and exception type specification for improved security posture

## [0.1.0-rc.5] - 2025-12-22

### Added

* `owner_id` to bot configuration and banner
* Type reporting options for unknown variables and parameters in `pyproject.toml`
* Rich representation for `BaseModel`
* Utility functions for configuration checks in documentation scripts
* Database initialization state inspection
* Unified CLI entry point with comprehensive command groups for `tux`, `test`, `docs`, `dev`, `db`, and `config`
* Git blame ignore configuration for formatting commits
* Comprehensive error handling system with test registry and configuration
* Documentation workflow for automated builds and deployment
* Enhanced CI workflow scripts and updated action versions
* Security policy improvements with main policy link
* Communication service improvements with DM embed user reference updates
* Regex pattern standardization and new pattern additions
* Exception handling improvements with language input sanitization
* Info command handling and documentation improvements
* Dependency updates for Pillow and MkDocs Material
* CI workflow improvements with shfmt flag updates
* **Database System Migration**: Complete migration from Prisma to SQLModel (SQLAlchemy + Pydantic)
  * SQLModel ORM implementation with async PostgreSQL support
  * Database controllers with BaseController pattern
  * DatabaseCoordinator facade for centralized access
  * Alembic migration system with PostgreSQL enum support
  * Connection pooling with retry logic and health checks
* **CLI Framework Migration**: Migrated from Click to Typer for improved type safety and developer experience
* **Type Checker Migration**: Switched from pyright to basedpyright for enhanced type checking
* **Source Layout Migration**: Reorganized from flat layout (tux/) to src layout (src/tux/) following Python packaging best practices
* **Configuration System**: Modular configuration management with multi-format support (TOML, YAML, JSON), priority-based loading, and pydantic-settings validation
* **Plugin System**: Modular plugin architecture for extending functionality without modifying core code
* **Task Monitoring**: Background task monitoring and management system
* **Activity Rotation**: Dynamic bot activity rotation with placeholder substitution
* **Cloudflare Workers Integration**: Documentation deployment via Cloudflare Workers with Wrangler CLI
* **Database Testing**: py-pglite integration for in-memory PostgreSQL testing
* **Plugins**: Deepfry (image manipulation), Flag Remover (flag emoji removal), Support Notifier (support channel notifications), Harmful Commands (detection and warning for potentially harmful shell commands), Fact (fun facts system)

### Changed

* Refactored and improved error handling across all CLI scripts (main, database, documentation, development, tests)
* Enhanced terminal output formatting with indent guides and improved utility functions
* Modularized coverage command and browser handling
* Improved table listing with progress indication and better query structure
* Streamlined bot execution flow and startup process
* Updated documentation build and serve scripts with better error handling and configuration checks
* Restructured development checks with a new `Check` class
* Updated `wrangler` deployment scripts with improved argument handling and error checks
* **Package Manager Migration**: Migrated from Poetry to uv for faster dependency resolution
* **Project Structure**: Reorganized from flat layout (tux/) to src layout (src/tux/) with clear separation: `core/`, `database/`, `services/`, `modules/`, `plugins/`, `ui/`, `shared/`, `help/`
* **Documentation Structure**: Reorganized documentation from `developer-guide/` and `admin-guide/` to `developer/concepts/` with subdirectories (`core/`, `handlers/`, `tasks/`, `ui/`, `wrappers/`, `database/`) and `admin/` structure
* **Help System**: Refactored help command with separated components, improved pagination, and interactive navigation
* **Bot Lifecycle**: Streamlined initialization process with dedicated setup services
* **Database Controllers**: Improved session management with instance expunging and lazy loading
* **Command Suggestions**: Enhanced accuracy with qualified name prioritization and alias support
* **Logging Configuration**: Simplified to console-only logging, removed file logging configuration
* Code formatting to 88 character line length
* Pre-commit hooks and package version updates
* Documentation workflow components renamed for clarity
* Communication DM embed user reference updates
* Regex variable naming standardization with new patterns
* CI workflow scripts enhanced with updated action versions
* Info command handling and documentation improvements

### Fixed

* Log level for prefix override in `prefix_manager` changed to trace
* Configuration file validation paths
* `KeyboardInterrupt` handling across database, coverage, and HTML report generation scripts
* Error message clarity in database version function and coverage reports
* Docker installation guide and storage requirements in documentation
* CLI entry point organization
* Graceful handling of `RuntimeError` and `SystemExit` in main execution flow
* Error message truncation issues
* AFK member ID deletion logic
* Moderation logging references
* Help command emoji additions for new categories
* SQLAlchemy verbose logging
* Communication DM embed user reference updates
* CI workflow shfmt flag issues
* Exception handling for language input sanitization
* Security policy link additions
* Command usage references to include dynamic prefix
* Hardcoded loading emoji removal
* Expired tempban checker log level adjustments

### Removed

* Legacy CLI scripts in favor of the unified Typer-based CLI
* **Poetry**: Removed Poetry package manager in favor of uv
* **Prisma**: Removed Prisma client in favor of SQLModel for better Python integration
* **Click CLI**: Removed Click framework in favor of Typer
* **pyright**: Removed pyright in favor of basedpyright
* **Legacy Permission System**: ConditionChecker and hardcoded permission levels replaced with database-driven system
* **File Logging**: Removed file logging configuration and related methods in favor of console-only logging
* **Note Database Table**: Removed unused Note model and table
* **Legacy Config Management**: Removed old config management.py and wizard.py files
* **Deprecated Migration Commands**: Removed migrate_deploy and migrate_format commands from DatabaseCLI
* **Legacy Database Methods**: Removed deprecated methods from BaseController
* **Legacy CLI Scripts**: Removed old CLI architecture in favor of Click-based scripts
* **Adminer Theme**: Removed custom CSS theme for Adminer
* **ASCII Art Module**: Removed separate ASCII art module, integrated into banner system
* **Various Documentation Files**: Reorganized and removed outdated documentation files during documentation restructuring

### Security

* Updated database nuke command with enhanced security prompts and confirmation requirements
* Improved validation for configuration file paths and environment variables

## [0.1.0-rc.4] - 2025-06-15

### Added

* Comprehensive test suite additions
* Multi-platform Docker builds
* Enhanced error handling for code execution
* Sentry integration with global Discord library version tagging
* Specific API error classes for better error handling
* Codecov integration for coverage tracking

### Changed

* CI/Docker workflow improvements
* Dockerfile reorganization and optimization for better security and performance
* Enhanced dev and docker CLI with new commands and options

### Fixed

* Codecov integration fixes and upload improvements
* CI workflow fixes for database tests and coverage reporting
* ShellCheck warnings in CI workflows
* Pre-commit hooks configuration updates

## [0.1.0-rc.3] - 2025-05-13

### Added

* Wolfram Alpha integration for math/science queries
* TuxApp orchestration system for lifecycle management

### Changed

* Enhanced moderation cases command with aliases

### Fixed

* Poll reaction handling fixes (remove user reaction if it doesn't meet poll criteria)
* InfluxDB logger improvements (update logger for starboard to use correct fields)
* AFK command responses made ephemeral
* TLDR output formatting improvements

## [0.1.0-rc.2] - 2025-04-29

### Added

* Comprehensive documentation improvements
* CLI documentation enhancements
* Docker development guide
* Dynamic version fetching using importlib.metadata
* API reference generation
* Developer guides (core concepts, handlers, tasks, UI, wrappers, database patterns)
* User documentation (feature guides and command references)
* Admin documentation (configuration and management guides)
* Self-hosting guides (installation and deployment instructions)

### Changed

* Status roles enhancements and logging (improved initialization, better logging)
* Documentation structure updates and navigation improvements
* Contributing guide enhancements

### Fixed

* Dockerfile cleanup and optimization
* Documentation formatting and indentation fixes

## [0.1.0-rc.1] - 2025-04-19

### Added

* Status roles feature (initial commit March 23, merged April 19)
* Dynamic versioning system
* Extensions/plugin system foundation
* Docker workflow improvements

### Changed

* Final integration of features developed before rc.1

### Fixed

* Docker workflow fixes
* Status roles logging improvements
* Version serialization formatting fixes

## [0.0.0] - 2023-11-28

### Added

Core Infrastructure

* **Bot Framework**: Complete Discord bot built on discord.py with hybrid command support (slash and prefix commands)
* **Hot Reload System**: File watching with watchdog for automatic cog reloading during development with dependency tracking
* **Error Handling**: Comprehensive error handling system with error extractors, formatters, command suggestions, and Sentry integration
* **Sentry Integration**: Comprehensive error tracking with cog, context management, handlers, tracing, and utilities
* **Environment Management**: Centralized environment configuration utilities
* **Prefix Management**: Dynamic prefix management with database-backed configuration
* **Custom Context**: Enhanced command context with additional utilities
* **Type Converters**: Custom type converters for Discord entities
* **Command Flags**: Flag-based command argument system

Database System (Prisma-based)

* **Prisma Integration**: Database ORM using Prisma with PostgreSQL support
* **Database Controllers**: Controller pattern with BaseController for centralized database management
* **Database Models**: Guild, GuildConfig, Case, AFK, Reminder, Snippet, Levels, Starboard, StarboardMessage
* **Database Client**: Singleton DatabaseClient for centralized database operations

Permission System (Legacy)

* **Hardcoded Permissions**: Permission system with hardcoded permission levels
* **ConditionChecker**: Legacy permission checking system
* **Role-Based Permissions**: Basic role-based permission checks

Moderation System

* **Case Management**: Comprehensive case system with viewing, searching, and modification capabilities
* **Ban/Kick**: Ban and kick commands with reason support
* **Warn**: Warning system with case tracking
* **Timeout**: Temporary timeout/mute functionality
* **Tempban**: Temporary ban with expiration handling (September 4, 2024)
* **Jail/Unjail**: Jail system with dedicated channel support
* **Purge**: Bulk message deletion with Discord API limits handling
* **Slowmode**: Channel slowmode management
* **Report**: User reporting system with modal forms
* **Poll Ban/Unban**: Poll restriction system
* **Snippet Ban/Unban**: Snippet restriction system
* **Clear AFK**: Administrative AFK status clearing

Utility Commands

* **AFK System**: AFK status management with expiration times and automatic cleanup
* **Self-Timeout**: User-initiated timeout command with confirmation dialogs
* **RemindMe**: Reminder system with database persistence
* **Ping**: Bot latency and uptime display
* **Poll**: Poll creation with reaction-based voting
* **Snippets**: Complete snippet management system with CRUD operations, aliases, locking, and search
* **Encode/Decode**: Text encoding and decoding utilities
* **Timezones**: Timezone conversion utilities
* **Wiki**: Wikipedia search integration
* **Emoji Management**: Centralized emoji management system for application emojis

Information Commands

* **Info**: Comprehensive information commands for Discord entities (members, channels, roles, emojis, guilds)
* **Avatar**: User avatar display
* **Member Count**: Server statistics (total members, humans, bots)
* **Help System**: Enhanced help command with interactive UI components, navigation, and category organization

Level System

* **XP and Levels**: User leveling system with XP tracking
* **Level Commands**: Administrative commands for managing levels and XP
* **Level Display**: User level information display
* **Blacklist Functionality**: Ability to blacklist users from gaining XP

Feature Modules

* **Starboard**: Message starboard system with configurable thresholds
* **Status Roles**: Automatic role assignment based on user status (March 23, 2025)
* **Bookmarks**: Message bookmarking system (April 9, 2024)
* **Temp VC**: Temporary voice channel creation (April 9, 2024)
* **GIF Limiter**: Rate limiting for GIF messages with per-user and per-channel limits (September 22, 2024)
* **InfluxDB Logger**: Metrics logging to InfluxDB (March 14, 2025)
* **Event Handler**: Discord event handling system

Tools

* **Code Execution**: Run code in multiple languages with Wandbox and Godbolt integration
* **TLDR** (April 2024): Quick command documentation lookup
* **XKCD** (June 2024): XKCD comic integration

Fun Commands

* **Random**: Random number and choice generation
* **Cowsay**: ASCII art generation with customizable options

Admin Commands

* **Dev**: Development utilities including cog loading/unloading/reloading
* **Eval**: Code evaluation with permission checks

Plugins

* **Role Count**: Role counting with emoji support
* **TTY Roles**: Terminal/editor role management
* **Git**: GitHub integration commands
* **Mail**: Mail system
* **Mock**: Text mocking utility

CLI Tools (Click-based)

* **Click CLI**: Command-line interface built with Click (April 6, 2025)
* **Semantic Versioning**: Dynamic version management utilities with build metadata generation
* **Bot Commands**: `tux start`, `tux version`
* **Development Commands**: `dev lint`, `dev format`, `dev type-check`, `dev lint-docstring`, `dev docstring-coverage`, `dev pre-commit`, `dev all`
* **Database Commands**: `db init`, `db dev`, `db push`, `db status`, `db new`, `db health`, `db schema`, `db queries`
* **Testing Commands**: `tests all`, `tests quick`, `tests plain`, `tests parallel`, `tests html`, `tests coverage`, `tests benchmark`
* **Documentation Commands**: `docs serve`, `docs build`
* **Config Commands**: `config generate`

Documentation

* **MkDocs Material**: Initial documentation site setup with Material theme (July 31, 2024)

Testing

* **Test Framework**: Comprehensive pytest setup with async support and coverage reporting
* **Test Markers**: Unit, integration, slow, database, and async test markers
* **Coverage Reporting**: Multiple coverage formats

CI/CD

* **GitHub Actions**: CI/CD workflows for testing, linting, type checking, and Docker builds
* **Pre-commit Hooks**: Automated code quality checks
* **Docker Builds**: Multi-platform Docker builds

Monitoring & Logging

* **Structured Logging**: Loguru-based structured logging with console output

UI Components

* **Embed System**: Comprehensive embed creation utilities with type-safe embed types
* **Button Components**: Reusable button components
* **Banner System**: Banner creation and formatting utilities
* **Modals**: Modal form system including report modals
* **Views**: Interactive view system with confirmation dialogs and TLDR views

HTTP & API Integration

* **HTTP Client**: Custom async HTTP client wrapper with retry logic and error handling
* **API Wrappers**: Wrappers for GitHub, Godbolt, TLDR, Wandbox, and XKCD APIs

Utilities

* **Custom Exceptions**: Comprehensive exception hierarchy for error handling
* **Version Management**: Dynamic version management using importlib.metadata
* **Regex Patterns**: Common regex patterns for validation
* **Shared Functions**: Utility functions for common operations

Docker & Deployment

* **Docker Compose**: Development environment with PostgreSQL and Adminer
* **Adminer Integration**: Database administration interface with auto-login functionality
* **Non-root User**: Security improvements with non-root containers
* **Health Checks**: Container health monitoring

### Changed

* **Case Creation**: Enhanced with thread-safe case numbering using locking mechanism to prevent race conditions

### Fixed

* **Database Operations**: Fixed race conditions in case numbering and reminder deletion
* **Level System**: Fixed XP reset issues when database errors occur
* **Reminder System**: Fixed reminders not deleting from database if DMs are closed
* **AFK System**: Fixed race conditions in AFK status removal
* **Help Command**: Prevented unauthorized interactions
* **Moderation**: Fixed ban check logic and enabled banning non-server users
* **Poll System**: Fixed reaction removal issues
* **Snippet System**: Fixed reply mention behavior
* **Code Execution**: Fixed handling for various programming languages
* **Config System**: Fixed crashes when configuration files are outdated
* **CI/CD**: Fixed type checking and Codecov uploads

### Removed

* **File Logging**: Removed file logging configuration and related methods in favor of console-only logging (October 6, 2025)
* **Supabase Client**: Removed Supabase client in favor of direct PostgreSQL connection (March 28, 2024)
* **ASCII Art Module**: Removed separate ASCII art module, integrated into banner system (August 2025)
* **Ghost Ping Detection**: Removed ghost ping notification feature (April 9, 2024)
* **Requirements.txt**: Removed in favor of pyproject.toml for dependency management (March 26, 2024)
* **Adminer Theme**: Removed custom CSS theme for Adminer (November 10, 2025)
* **Various Documentation Files**: Reorganized and removed outdated documentation files during documentation restructuring (September-November 2025)

### Security

* **Sentry Integration**: Enhanced error reporting and monitoring
* **Non-root Containers**: Docker containers run as non-root user

[Unreleased]: https://github.com/allthingslinux/tux/compare/v0.1.0-rc.5...HEAD
[0.1.0-rc.5]: https://github.com/allthingslinux/tux/compare/v0.1.0-rc.4...v0.1.0-rc.5
[0.1.0-rc.4]: https://github.com/allthingslinux/tux/compare/v0.1.0-rc.3...v0.1.0-rc.4
[0.1.0-rc.3]: https://github.com/allthingslinux/tux/compare/v0.1.0-rc.2...v0.1.0-rc.3
[0.1.0-rc.2]: https://github.com/allthingslinux/tux/compare/v0.1.0-rc.1...v0.1.0-rc.2
[0.1.0-rc.1]: https://github.com/allthingslinux/tux/compare/v0.0.0...v0.1.0-rc.1
[0.0.0]: https://github.com/allthingslinux/tux/releases/tag/v0.0.0
