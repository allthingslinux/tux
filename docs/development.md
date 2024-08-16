# Development Guide

## Introduction

This document is intended to provide a guide for developers who want to contribute to the development of the project. It is assumed that the reader has a basic understanding of the project and its goals and has a working knowledge of the tools and technologies used in the project.

## Getting Started

To get started with the development of the project, you will need to have the following tools and technologies installed on your system:

- Python 3.12
- [Poetry](https://python-poetry.org/docs/)
- Optional: [Docker](https://docs.docker.com/get-docker/) if you want to run the bot in a container.
- Optional: [Docker Compose](https://docs.docker.com/compose/install/) if you want to define the container environment in a `docker-compose.yml` file.
- Optional: [Just](https://github.com/casey/just/) if you want to use the Justfile for easy CLI commands.

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