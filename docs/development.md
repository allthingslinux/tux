# Development Guide

## Introduction

This document is intended to provide a guide for developers who want to contribute to the development of the project.

It is assumed that the reader has a basic understanding of the project and its goals as well as the tools and technologies used in the project.

## Getting Started

To get started with the development of the project, refer to the installation instructions in the project [README](../README.md).

## Installation

To install the project on your system, follow these steps:

TODO: Add installation steps for development environment

## Development Workflow

The development workflow for the project is as follows:

TODO: Add development workflow for the project

## Project Structure

The project is structured as follows:

### Source Code

- `tux/`: The main package containing the bot code.
  - `cogs/`: The cogs directory containing categorized hybrid, prefix and slash commands/command groups. See [Cogs Primer](#cogs-primer) for more information.
  - `database/`: The database directory containing the database client and controllers. See [Database Primer](#database-primer) for more information.
  - `handlers/`: The handlers directory containing the event handlers for the bot. See [Handlers Primer](#handlers-primer) for more information.
    - `activity.py`: The activity module containing the activity handlers for the bot.
    - `error.py`: The error module containing the error handlers for the bot.
    - `event.py`: The event module containing the event handlers for the bot.
  - `ui/`: The UI directory containing the user interface components for the bot. See [UI Primer](#ui-primer) for more information.
  - `utils/`: The utils directory containing utility functions and classes used throughout the bot. See [Utils Primer](#utils-primer) for more information.
    - `checks.py`: The checks module containing the check functions for the bot.
    - `constants.py`: The constants module containing the constants and config/env variables used throughout the bot.
    - `embeds.py`: The embeds module containing the embed classes for the bot.
    - `flags.py`: The flags module containing the command flag arguments for the bot.
    - `functions.py`: The functions module containing the utility functions for the bot.
  - `wrappers/`: The wrappers directory containing the wrappers for external APIs and services. See [Wrappers Primer](#wrappers-primer) for more information.
  - `main.py`: The main entry point for the bot.
  - `bot.py`: The bot class definition.
  - `cog_loader.py`: The cog loader class definition.
  - `help.py`: The help command class definition.

### Configuration

- `.env.example`: The example environment file containing the environment variables required for the bot.
- `config/`: The config directory containing the configuration files for the bot.
  - `settings.json`: The settings file containing the bot settings and configuration.

### Documentation

- `docs/`: The documentation directory containing the project documentation.
- `CONTRIBUTING.md`: The contributing guidelines for the project.
- `README.md`: The project README file containing the project overview and installation instructions.
- `mkdocs.yml`: The MkDocs configuration file containing the project documentation settings.
- `SECURITY.md`: The security policy for the project.
- `LICENSE.md`: The license file containing the project license information.

### Development

- `pyproject.toml`: The Poetry configuration file containing the project metadata and dependencies for the bot.
- `Dockerfile`: The Dockerfile containing the container configuration for the bot.
- `docker-compose.yml`: The Docker Compose file containing the container environment configuration for the bot.
- `justfile`: The Justfile containing the development commands for the bot.
- `.gitignore`: The Git ignore file containing the files and directories to be ignored by Git.

### CI/CD

- `.pre-commit-config.yaml`: The pre-commit configuration file containing the pre-commit hooks for the bot.
- `.github/workflows/`: The GitHub Actions directory containing the CI/CD workflows for the bot.
- `renovate.json`: The Renovate configuration file containing the dependency update settings for the bot.

## Cogs Primer

There comes a point in your bot’s development when you want to organize a collection of commands, listeners, and some state into one class. Cogs allow you to do just that.

It should be noted that cogs are typically used alongside with Extensions.

An extension at its core is a python file with an entry point called setup. This setup function must be a Python coroutine. It takes a single parameter of the Bot that loads the extension.

With regards to Tux, we typically define one cog per extension. This allows us to keep our code organized and modular.

Furthermore, we have a `CogLoader` class that loads our cogs (technically, extensions) from the `cogs` directory and registers them with the bot at startup.

### Cog Essentials

- Each cog is a Python class that subclasses commands.Cog.
- Every regular command or "prefix" is marked with the `@commands.command()` decorator.
- Every app or "slash" command is marked with the `@app_commands.command()` decorator.
- Every hybrid command is marked with the `@commands.hybrid_command()` decorator.
- Every listener is marked with the `@commands.Cog.listener()` decorator.

tl;dr - Extensions are imported "modules", cogs are classes that are subclasses of `commands.Cog`.

Referance:

- [discord.py - Cogs](https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html)
- [discord.py - Extensions](https://discordpy.readthedocs.io/en/stable/ext/commands/extensions.html)

## Database Primer

TODO: Add database primer

## Handlers Primer

TODO: Add handlers primer

## UI Primer

TODO: Add UI primer

## Utils Primer

TODO: Add utils primer

## Wrappers Primer

TODO: Add wrappers primer
