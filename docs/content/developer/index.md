---
title: Developer Guide
icon: material/folder-search-outline
tags:
  - developer-guide
---

# Developer Guide

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

This section contains documentation for developers working with Tux.

## Quick Start

If you don't need detailed instructions, you can get started quickly by following these steps.

### Prerequisites

- Linux development environment (WSL if on Windows)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [Docker](https://docs.docker.com/engine/install/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (the Tux development tool)
- A Discord bot token (create one at the [Discord Developer Portal](https://discord.com/developers/applications) or check our [Bot Token Configuration guide](../selfhost/config/bot-token.md))
- A Discord server that has the bot added to it

!!! tip
    Don't know how to add a bot to your server? Go to the OAuth2 tab, scroll down to the URL Generator, select the "bot" scope, then scroll down and set the permissions you want the bot to have. Open the generated URL to add the bot.

### 1. **Clone the repository**

```bash
git clone https://github.com/allthingslinux/tux.git && cd tux
```

!!! warning
    If you plan to contribute changes back to the main repository, make sure to fork the repository first and clone your fork instead (replace allthingslinux with your GitHub username). Then add the main repository as an upstream remote:
    <!-- markdownlint-disable MD046 -->
    ```bash
    git remote add upstream https://github.com/allthingslinux/tux.git
    ```

### 3. **Set up the development environment**

```bash
# Install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

```bash
# Generate and edit configuration files
uv run config generate
cp .env.example .env && cp config/config.toml.example config/config.toml
```

### 4. **Edit configuration files**

Edit the `.env` and `config/config.toml` files in your favorite text editor to set up your development environment.

At a minimum, you should set the `BOT_TOKEN` in `.env` to your Discord bot token, and also the `BOT_OWNER_ID` to your Discord user ID so you can use owner-only commands. ([See this guide if you need help finding your Discord user ID](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID)).

If you want to set a custom database url (e.g. for managed services like supabase), set the variables for that. If you want to set a custom password or other database settings for the Docker database, set those and it will automatically apply to the Docker database on first run.

### 5. **Start the database**

**If you aren't using the self-hosted database, skip this step.**

If you want a web UI at `http://localhost:8080` for managing the database, replace `tux-postgres` with `tux-adminer` in the `docker compose up -d` command below.

```bash
# Setup database
docker compose up -d tux-postgres
```

The database should automatically migrate with all required tables on first bot start.

### 6. **Run the bot**

The bot hot-reloads on code changes, so no need to restart it manually. For some things like config changes and state-based components, you may need to restart the bot.

```bash
uv run tux start --debug
```

Once you are done, run `$dev ct` (replace `$` with your prefix if you changed it) to register slash commands. You will need to run this whenever you add or change slash commands, more specifically slash command signatures.

This will also let you confirm that the bot is running and that you have set your bot owner ID correctly.

### 7. **Develop, run, lint, and test**

This is a simple explanation of the development workflow.

```bash
# Develop, run, lint, and test
git checkout -b feature/your-feature-name
# ... make changes ...
uv run dev all
git commit -m "feat(command): add new command"
# ... repeat until you are ready ...
git push origin feature/your-feature-name
```
