# Project Structure

This document outlines the structure of the Discord bot project to help you navigate and understand where different components are located.

## Root Directory

- **.git/** - Contains Git configuration and history.
- **.github/** - Contains GitHub related files including workflows for CI/CD.
  - **workflows/**
    - **dependency-review.yml** - Workflow for dependency review.
    - **linting.yml** - Workflow for linting the codebase.
- **.gitignore** - Specifies intentionally untracked files to ignore.
- **.mise.toml** - Configuration file for Mise, a tool to manage tooling environment.
- **.pre-commit-config.yaml** - Configuration for pre-commit hooks.
- **CODE_OF_CONDUCT.md** - The code of conduct for contributors.
- **LICENSE.md** - Project license information.
- **README.md** - A brief description of the project and how to set it up.

## Configuration Files

- **config/**
  - **settings.json** - JSON file containing configuration parameters.

## Documentation

- **docs/** - Contains documentation files for the project.
  - **CLI.md** - CLI usage guidelines.
  - **COG_STANDARDS.md** - Standards for cog development.
  - **EMBED_STANDARDS.md** - Standards for embed styles.
  - **EMBED_USAGE.md** - Guidelines on how to use embeds.
  - **EVENT_STANDARDS.md** - Event handling standards.
  - **PROJECT_STRUCTURE.md** - Overview of the project structure.

## Example Files

- **examples/** - Contains sample code and usage examples.

## Type Checking Configuration

- **mypy.ini** - Configuration for MyPy, a static type checker.

## Dependency Management

- **poetry.lock** - Lock file for Poetry to ensure reproducible installs.

## Database Schema

- **prisma/**
  - **database.db** - SQLite database file.
  - **schema.prisma** - Prisma schema for database modeling.

## Python Project and Dependency Management

- **pyproject.toml** - Specifies project dependencies and configurations.

## Test Files

- **tests/** - Contains test scripts and testing resources.

## Temporary Files

- **tmp/** - Temporary files generated during runtime or testing.

## Core Bot Functionality

- **tux/**
  - **cog_loader.py** - Handles the loading of Cogs.
  - **cogs/** - Directory containing various categories of bot commands.
    - **admin/**, **guild/**, **logging/**, **misc/**, **moderation/**, **utility/** - Cogs organized by functionality.
  - **database/**
    - **client.py** - Database connection management.
    - **controllers/** - Database controllers for different entities.
  - **main.py** - Entry point of the Discord bot.
  - **utils/** - Utility scripts and helper functions.

## System Service Configuration

- **tux.service** - Systemd service unit file to run the bot as a service.

## Docker Configuration

- **docker-compose.yml** - Docker Compose configuration file to manage container deployment.


```
tux
├─ .git
├─ .github
│  └─ workflows
│     ├─ dependency-review.yml
│     └─ linting.yml
├─ .gitignore
├─ .mise.toml
├─ .pre-commit-config.yaml
├─ CODE_OF_CONDUCT.md
├─ LICENSE.md
├─ README.md
├─ config
│  └─ settings.json
├─ docs
│  ├─ CLI.md
│  ├─ COG_STANDARDS.md
│  ├─ EMBED_STANDARDS.md
│  ├─ EMBED_USAGE.md
│  ├─ EVENT_STANDARDS.md
│  └─ resources
│     ├─ image.png
├─ examples
├─ mypy.ini
├─ poetry.lock
├─ prisma
│  ├─ database.db
│  └─ schema.prisma
├─ pyproject.toml
├─ tests
├─ tmp
├─ tux
│  ├─ cog_loader.py
│  ├─ cogs
│  │  ├─ admin
│  │  │  ├─ sync.py
│  │  ├─ error_handler.py
│  │  ├─ guild
│  │  │  └─ roles.py
│  │  ├─ logging
│  │  │  ├─ commands.py
│  │  │  ├─ guild.py
│  │  │  ├─ member.py
│  │  │  ├─ mod.py
│  │  │  └─ voice.py
│  │  ├─ misc
│  │  │  ├─ temp_vc.py
│  │  │  └─ tty_roles.py
│  │  ├─ moderation
│  │  │  ├─ ban.py
│  │  │  ├─ kick.py
│  │  │  ├─ purge.py
│  │  │  ├─ slowmode.py
│  │  │  ├─ unban.py
│  │  │  └─ warn.py
│  │  └─ utility
│  │     ├─ avatar.py
│  │     ├─ guide.py
│  │     ├─ info.py
│  │     ├─ membercount.py
│  │     ├─ ping.py
│  │     ├─ poll.py
│  │     ├─ report.py
│  │     ├─ rolecount.py
│  │     └─ tldr.py
│  ├─ database
│  │  ├─ client.py
│  │  └─ controllers
│  │     ├─ __init__.py
│  │     ├─ infractions.py
│  │     ├─ notes.py
│  │     ├─ reminders.py
│  │     ├─ roles.py
│  │     ├─ snippets.py
│  │     └─ users.py
│  ├─ main.py
│  └─ utils
│     ├─ activities.py
│     ├─ console.py
│     ├─ constants.py
│     ├─ embeds.py
│     ├─ functions.py
│     └─ sentry.py
├─ tux.service
├─ docker-compose.yml
```