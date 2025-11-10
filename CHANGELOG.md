# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

*

## [0.1.0] - 2025-11-11

### Added

* **Documentation**: Comprehensive developer and user guides with step-by-step setup instructions, API references, and CLI tools
* **Error Handling**: New centralized error handler cog with Sentry integration for both prefix and slash commands
* **Setup Services**: Modular bot initialization system with BaseSetupService, BotSetupService, CogSetupService, DatabaseSetupService, PermissionSetupService, and BotSetupOrchestrator
* **Dynamic Permission System**: Database-driven permission management replacing hardcoded levels with configurable ranks (0-100)
* **Configuration Management**: New config cog with interactive setup wizard for guild onboarding, permission ranks, and log channels
* **Hot Reload**: File watching system for automatic cog reloading with debounced reload mechanism
* **Hybrid Commands**: Support for both prefix and slash command usage across multiple cogs
* **Help System**: Paginated help embeds with improved command navigation and subcommand display
* **Info Commands**: Enhanced information commands supporting Discord entities (members, channels, roles, emojis, etc.)
* **Member Count**: New command displaying server statistics (total members, humans, bots)
* **Activity Management**: Dynamic activity rotation with placeholder substitution for bot statistics
* **Onboarding Wizard**: Interactive setup process for new guilds with permission initialization and channel selection
* **Type Annotations**: Comprehensive type hints added throughout codebase for better IDE support
* **Integration Tests**: Expanded test coverage for permission system and database operations

### Changed

* **CLI Tools**: Migrated from Click to Typer for improved command-line interface
* **Plugin System**: Refactored extensions to modular plugin architecture
* **Bot Lifecycle**: Streamlined initialization process with dedicated setup task creation
* **Cog Loading**: Enhanced eligibility checks and priority-based loading system
* **Database Controllers**: Improved session management with instance expunging after operations
* **Case Creation**: Thread-safe case numbering with locking mechanism to prevent race conditions
* **Command Suggestions**: Enhanced accuracy with qualified name prioritization
* **Logging Configuration**: Simplified setup with console-only logging and removed deprecated file logging
* **PostgreSQL Config**: Overhauled configuration with detailed documentation and removed Tux-specific optimizations

### Fixed

* **RuntimeError Handling**: Removed RuntimeError from exception handling in TuxApp for better error specificity
* **Context Handling**: Improved permission decorator to handle both function and method calls
* **Embed Creation**: Standardized response formatting across commands
* **Image Handling**: Streamlined deepfry command to require attachment input
* **Type Ignore Comments**: Updated type checking suppressions for better compatibility

### Removed

* **Legacy Permission System**: ConditionChecker and hardcoded permission levels
* **Deprecated Commands**: migrate_deploy and migrate_format from DatabaseCLI
* **Unused Modules**: substitutions.py and Random cog
* **File Logging**: Removed file logging configuration and related methods
* **Hard-coded Poll Channel**: Removed channel-specific poll functionality
* **Guild Blacklist/Whitelist**: Removed unused controllers from DatabaseCoordinator

### Security

* **Sentry Integration**: Enhanced error reporting and monitoring capabilities
