# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Core Infrastructure

* **Bot Framework**: Complete Discord bot built on discord.py with hybrid command support (slash and prefix commands)
* **Application Lifecycle**: TuxApp orchestration system for managing bot lifecycle, initialization, and graceful shutdown
* **Hot Reload System**: File watching with watchdog for automatic cog reloading during development with dependency tracking
* **Plugin System**: Modular plugin architecture for extending functionality without modifying core code
* **Error Handling**: Comprehensive error handling system with error extractors, formatters, command suggestions, and Sentry integration
* **Environment Management**: Centralized environment configuration utilities
* **Task Monitoring**: Background task monitoring and management system
* **Prefix Management**: Dynamic prefix management with database-backed configuration
* **Custom Context**: Enhanced command context with additional utilities
* **Type Converters**: Custom type converters for Discord entities
* **Command Flags**: Flag-based command argument system
* **Setup Services**: Modular setup services for bot, cogs, database, and permissions with orchestrator

#### Database System

* **SQLModel Integration**: Type-safe database ORM using SQLModel (SQLAlchemy + Pydantic) with async PostgreSQL support
* **Database Controllers**: Controller pattern with BaseController and specialized controllers for CRUD operations, pagination, bulk operations, and transactions
* **DatabaseCoordinator**: Centralized facade for accessing all model-specific controllers
* **Migration System**: Alembic-powered schema management with PostgreSQL-specific enum support
* **Connection Pooling**: Async connection pooling with retry logic and health checks
* **Database Models**: Guild, GuildConfig, Case, AFK, Reminder, Snippet, Levels, Starboard, StarboardMessage, PermissionRank, PermissionCommand

#### Permission System

* **Dynamic Permissions**: Database-driven permission management with configurable ranks (0-100)
* **Permission Decorators**: Flexible permission checking decorators for commands
* **Role-Based Permissions**: Role-to-rank assignment system

#### Configuration System

* **Multi-Format Config**: Support for TOML, YAML, and JSON configuration files with pydantic-settings validation
* **Config Generators**: Automatic config file generation for TOML, YAML, and JSON formats
* **Config Loaders**: Priority-based configuration loading system with environment variable support
* **Config Commands**: Interactive configuration system with Components V2 UI for guild settings, permission ranks, and log channels
* **Config Dashboard**: Interactive dashboard with pagination and command discovery
* **Environment Variables**: Comprehensive .env support with python-dotenv integration
* **Config Generation**: CLI command to generate example configuration files

#### Moderation System

* **Moderation Services**: Service layer architecture with case service, communication service, execution service, factory pattern, and moderation coordinator
* **Case Management**: Comprehensive case system with viewing, searching, and modification capabilities
* **Ban/Kick**: Ban and kick commands with reason support
* **Warn**: Warning system with case tracking
* **Timeout**: Temporary timeout/mute functionality
* **Tempban**: Temporary ban with expiration handling
* **Jail/Unjail**: Jail system with dedicated channel support
* **Purge**: Bulk message deletion with Discord API limits handling
* **Slowmode**: Channel slowmode management
* **Report**: User reporting system with modal forms
* **Poll Ban/Unban**: Poll restriction system
* **Snippet Ban/Unban**: Snippet restriction system
* **Clear AFK**: Administrative AFK status clearing

#### Utility Commands

* **AFK System**: AFK status management with expiration times and automatic cleanup
* **Self-Timeout**: User-initiated timeout command with confirmation dialogs
* **RemindMe**: Reminder system with database persistence
* **Ping**: Bot latency and uptime display
* **Poll**: Poll creation with reaction-based voting
* **Snippets**: Complete snippet management system with CRUD operations, aliases, locking, and search
* **Encode/Decode**: Text encoding and decoding utilities
* **Timezones**: Timezone conversion utilities
* **Wiki**: Wikipedia search integration

#### Information Commands

* **Info**: Comprehensive information commands for Discord entities (members, channels, roles, emojis, guilds)
* **Avatar**: User avatar display
* **Member Count**: Server statistics (total members, humans, bots)

#### Level System

* **XP and Levels**: User leveling system with XP tracking
* **Level Commands**: Administrative commands for managing levels and XP
* **Level Display**: User level information display

#### Feature Modules

* **Starboard**: Message starboard system with configurable thresholds
* **Status Roles**: Automatic role assignment based on user status
* **Bookmarks**: Message bookmarking system
* **Temp VC**: Temporary voice channel creation
* **GIF Limiter**: Rate limiting for GIF messages with per-user and per-channel limits
* **InfluxDB Logger**: Metrics logging to InfluxDB
* **Activity Rotation**: Dynamic bot activity rotation with placeholder substitution
* **Event Handler**: Discord event handling system

#### Tools

* **Code Execution**: Run code in multiple languages with Wandbox and Godbolt integration
* **TLDR**: Quick command documentation lookup
* **Wolfram Alpha**: Math and science query integration

#### Fun Commands

* **Random**: Random number and choice generation
* **XKCD**: XKCD comic integration

#### Admin Commands

* **Dev**: Development utilities including cog loading/unloading/reloading
* **Eval**: Code evaluation with permission checks

#### Plugins

* **Fact**: Fun facts system
* **Deepfry**: Image manipulation
* **Role Count**: Role counting with emoji support
* **TTY Roles**: Terminal/editor role management
* **Harmful Commands**: Detection and warning for potentially harmful shell commands
* **Support Notifier**: Support channel notification system
* **Git**: GitHub integration commands
* **Mail**: Mail system
* **Flag Remover**: Flag emoji removal utility
* **Mock**: Text mocking utility

#### CLI Tools

* **Typer CLI**: Comprehensive command-line interface built with Typer
* **Semantic Versioning**: Dynamic version management utilities with build metadata generation
* **Bot Commands**: `tux start`, `tux version`
* **Development Commands**: `dev lint`, `dev format`, `dev type-check`, `dev lint-docstring`, `dev docstring-coverage`, `dev pre-commit`, `dev all`
* **Database Commands**: `db init`, `db dev`, `db push`, `db status`, `db new`, `db health`, `db schema`, `db queries`
* **Docker Commands**: `docker up`, `docker down`, `docker build`, `docker logs`, `docker ps`, `docker shell`, `docker health`, `docker config`
* **Testing Commands**: `tests all`, `tests quick`, `tests plain`, `tests parallel`, `tests html`, `tests coverage`, `tests benchmark`
* **Documentation Commands**: `docs serve`, `docs build`
* **Config Commands**: `config generate`

#### Documentation

* **MkDocs Material**: Comprehensive documentation site with API reference generation
* **API Reference**: Complete codebase documentation
* **Components V2 Documentation**: Comprehensive rules documentation for Discord.py Components V2
* **Cloudflare Workers Integration**: Documentation deployment via Cloudflare Workers with Wrangler CLI

#### Testing

* **Test Framework**: Comprehensive pytest setup with async support and coverage reporting
* **Test Markers**: Unit, integration, slow, database, and async test markers
* **Coverage Reporting**: Multiple coverage formats with Codecov integration

#### CI/CD

* **GitHub Actions**: CI/CD workflows for testing, linting, type checking, and Docker builds
* **Pre-commit Hooks**: Automated code quality checks
* **Docker Builds**: Multi-platform Docker builds
* **Codecov Integration**: Coverage tracking

#### Monitoring & Logging

* **Sentry Integration**: Comprehensive Sentry integration with cog, context management, handlers, tracing, and utilities
* **Structured Logging**: Loguru-based structured logging with console output
* **Performance Monitoring**: Sentry transaction tracking for database operations and command execution
* **Error Context**: Enhanced error reporting with stack traces, user context, and performance metrics

#### UI Components

* **Embed System**: Comprehensive embed creation utilities with type-safe embed types
* **Button Components**: Reusable button components
* **Banner System**: Banner creation and formatting utilities
* **Modals**: Modal form system including report modals
* **Views**: Interactive view system with confirmation dialogs and TLDR views
* **Config UI**: Interactive configuration UI with dashboard, pagination, command discovery, and callbacks

#### HTTP & API Integration

* **HTTP Client**: Custom async HTTP client wrapper with retry logic and error handling
* **API Wrappers**: Wrappers for GitHub, Godbolt, TLDR, Wandbox, and XKCD APIs
* **Emoji Manager**: Centralized emoji management system for application emojis

#### Utilities

* **Custom Exceptions**: Comprehensive exception hierarchy for error handling
* **Version Management**: Dynamic version management using importlib.metadata
* **Regex Patterns**: Common regex patterns for validation
* **Shared Functions**: Utility functions for common operations

#### Docker & Deployment

* **Docker Compose**: Development environment with PostgreSQL and Adminer
* **Compose Watch**: Hot reload support for development with automatic rebuilds on file changes
* **Adminer Integration**: Database administration interface with auto-login functionality
* **Multi-stage Builds**: Optimized Containerfile (renamed from Dockerfile)
* **Non-root User**: Security improvements with non-root containers
* **Health Checks**: Container health monitoring

### Changed

* **Project Structure**: Major reorganization of source code and documentation structure
  * **Source Code**: Reorganized `src/tux/` with clear separation: `core/`, `database/`, `services/`, `modules/`, `plugins/`, `ui/`, `shared/`, `help/`
  * **Services Directory**: Created dedicated `services/` directory with subdirectories for `moderation/`, `hot_reload/`, `sentry/`, `handlers/`, `wrappers/`
  * **Modules Reorganization**: Renamed `modules/services/` to `modules/features/` for clarity
  * **Plugins Organization**: Moved plugins into `plugins/atl/` subdirectory for better organization
  * **Database Structure**: Restructured database controllers into `database/controllers/` with `base/` subdirectory for specialized controllers
  * **Documentation Structure**: Reorganized documentation from `developer-guide/` and `admin-guide/` to `developer/concepts/` with subdirectories (`core/`, `handlers/`, `tasks/`, `ui/`, `wrappers/`, `database/`) and `admin/` structure
* **Database System**: Migrated from Prisma to SQLModel (SQLAlchemy + Pydantic) for better Python integration and type safety
* **Permission System**: Replaced legacy ConditionChecker and hardcoded permission levels with database-driven dynamic permission system
* **Configuration System**: Refactored from monolithic onboarding wizard to modular configuration management system with Components V2 UI
* **Help System**: Refactored help command with separated components, improved pagination, and interactive navigation
* **Package Manager**: Migrated from Poetry to uv for faster dependency resolution and improved performance
* **CLI Tools**: Migrated from Click to Typer for improved command-line interface with better type safety
* **Plugin System**: Refactored extensions to modular plugin architecture with hot-reload support
* **Docker Configuration**: Renamed Dockerfile to Containerfile for better compatibility with Podman and other container tools
* **Bot Lifecycle**: Streamlined initialization process with dedicated setup services and orchestrator
* **Database Controllers**: Improved session management with instance expunging and lazy loading of specialized controllers
* **Case Creation**: Enhanced with thread-safe case numbering using locking mechanism to prevent race conditions
* **Command Suggestions**: Enhanced accuracy with qualified name prioritization and alias support
* **Logging Configuration**: Simplified to console-only logging, removed file logging configuration
* **Type Checking**: Switched from pyright to basedpyright for stricter type checking
* **Permission Ranks**: Updated permission rank system from legacy levels to 0-100 hierarchy, then refined to 0-10 range
* **Database Service**: Unified AsyncDatabaseService and DatabaseService into single DatabaseService for consistency

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

* **Legacy Permission System**: ConditionChecker and hardcoded permission levels replaced with database-driven system
* **File Logging**: Removed file logging configuration and related methods in favor of console-only logging
* **Prisma**: Removed Prisma client in favor of SQLModel for better Python integration
* **Supabase Client**: Removed Supabase client in favor of direct PostgreSQL connection
* **Onboarding Wizard**: Removed interactive setup wizard in favor of modular configuration system
* **Note Database Table**: Removed unused Note model and table
* **ASCII Art Module**: Removed separate ASCII art module, integrated into banner system
* **Ghost Ping Detection**: Removed ghost ping notification feature
* **Legacy Config Management**: Removed old config management.py and wizard.py files
* **Requirements.txt**: Removed in favor of pyproject.toml for dependency management
* **Deprecated Migration Commands**: Removed migrate_deploy and migrate_format commands from DatabaseCLI
* **Legacy Database Methods**: Removed deprecated methods from BaseController
* **Legacy CLI Scripts**: Removed old CLI architecture in favor of Typer-based scripts
* **Poetry**: Removed Poetry package manager in favor of uv
* **Adminer Theme**: Removed custom CSS theme for Adminer (replaced with auto-login functionality)
* **Various Documentation Files**: Reorganized and removed outdated documentation files during documentation restructuring

### Security

* **Sentry Integration**: Enhanced error reporting and monitoring
* **Non-root Containers**: Docker containers run as non-root user
* **Dependency Scanning**: Automated security scanning
* **Input Validation**: Comprehensive input validation with Pydantic models
