---
title: Contributing
description: How to contribute to Tux—setup, workflow, pull requests, and where to find detailed guides.
tags:
  - developer-guide
  - contributing
---

# Contributing to Tux

Thank you for your interest in contributing to Tux. This guide covers setup, workflow, and how to submit changes. For deeper dives, see [Git best practices](best-practices/git.md), [branch naming](best-practices/branch-naming.md), and [Code review](best-practices/code-review.md).

We welcome contributions of all kinds: bug fixes, features, and documentation improvements.

## Contributing Workflows

Tux supports both organization members and external contributors.

### Organization Members

- Clone the main repository: `git clone https://github.com/allthingslinux/tux.git && cd tux`
- Create feature branches in the main repo and push to `origin`

### External Contributors

- [Fork](https://github.com/allthingslinux/tux/fork) the repository (Fork button → choose your account; you can leave "Copy the `main` branch only" checked).
- Clone your fork: `git clone https://github.com/yourusername/tux.git && cd tux`
- Add `upstream` and verify:

  ```bash
  git remote add upstream https://github.com/allthingslinux/tux.git
  git remote -v
  ```

- Push branches to your fork (`origin`) and open pull requests to `allthingslinux/tux`

For step-by-step walkthroughs, see [Development Setup](tutorials/development-setup.md) and [First Contribution](tutorials/first-contribution.md).

## Prerequisites

- **Linux development environment** (WSL if on Windows)
- **Git** — [install](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- **Python 3.13+** — [mise](https://mise.jdx.dev/) or [pyenv](https://github.com/pyenv/pyenv) recommended. Verify with `python --version`.
- **[uv](https://docs.astral.sh/uv/) — [install](https://docs.astral.sh/uv/getting-started/installation/)** — `curl -LsSf https://astral.sh/uv/install.sh | sh`, then `uv --version`
- **PostgreSQL** — local or remote (e.g. [Supabase](https://supabase.com) free tier)
- **Discord bot token** — [Discord Developer Portal](https://discord.com/developers/applications) or [Bot Token Configuration](../selfhost/config/bot-token.md)
- **A Discord server with the bot added**
- *(Optional)* **Docker & Docker Compose v2** — [install](https://docs.docker.com/engine/install/)

!!! tip "Adding the bot to your server"
    In the Discord Developer Portal: **OAuth2** → **URL Generator** → select the `bot` scope, set permissions, then open the generated URL to add the bot.

## Development Setup

1. **Clone** the main repo or your fork (and add `upstream` for forks; see above).

2. **Install and hooks:**

   ```bash
   # Optional: pin Python 3.13.x for the project
   uv python pin 3.13.5

   uv sync
   uv run pre-commit install
   ```

3. **Config:**

   ```bash
   uv run config generate
   cp .env.example .env
   cp config/config.json.example config/config.json
   ```

   Edit `.env` with at least:

   - `BOT_TOKEN`
   - Database — choose one:

     **Option 1: Individual PostgreSQL variables (recommended)**

     ```bash
     POSTGRES_HOST=localhost
     POSTGRES_PORT=5432
     POSTGRES_DB=tuxdb
     POSTGRES_USER=tuxuser
     POSTGRES_PASSWORD=your_secure_password_here
     ```

     **Option 2: Database URL override**

     ```bash
     DATABASE_URL=postgresql://user:password@host:port/db_name
     ```

   Edit `config/config.json`: set `USER_IDS.BOT_OWNER_ID` to your Discord user ID (required for owner-only commands).

   [Find your ID](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID). Tweak other options as needed. Regenerate examples: `uv run config generate`.

4. **Database:** If using local Docker: `docker compose up -d tux-postgres` (or `tux-adminer` for a web UI at `http://localhost:8080`). Then:

   ```bash
   uv run db init
   # or, to apply pending migrations only: uv run db push
   ```

   Migrations create the tables; the bot also runs them on first start. Skip the Docker step if you use a remote or managed Postgres.

5. **Run the bot (optional, to verify):** `uv run tux start --debug`. The bot hot-reloads on code changes. Run `$dev ct` (replace `$` with your prefix) to sync slash commands when you add or change them.

More detail: [Development Setup](tutorials/development-setup.md) and [First Contribution](tutorials/first-contribution.md).

## Development Workflow

### Branching

Tux uses **trunk-based development**: a single `main` branch that stays production-ready. Changes go through feature branches that merge into `main`.

**Lifecycle:** Create → Develop → Merge → Delete. Keep branches short-lived (about 1–3 days), merge to `main` frequently, and ensure `main` stays deployable. See [Branch naming](best-practices/branch-naming.md) and [Git best practices](best-practices/git.md).

### 1. Create a branch

From `main`, create a branch using our [branch naming conventions](best-practices/branch-naming.md):

```bash
git checkout main
git pull origin main   # or: git pull upstream main (forks)
git checkout -b feat/your-feature   # or fix/, docs/, hotfix/, etc.
```

**Keeping your branch updated:** Regularly pull `origin main` or `upstream main`, then rebase your feature branch on `main` before opening or updating a PR. See [Rebasing](best-practices/git.md#rebasing).

### 2. Implement changes

- **Code:** [Numpy-style](https://numpydoc.readthedocs.io/en/latest/format.html) docstrings, `Type | None` (not `Optional`), and type hints. See [Git best practices](best-practices/git.md) and [Code review](best-practices/code-review.md).
- **Docs:** Update `docs/content/` when behavior or APIs change.
- **CHANGELOG:** For user-facing changes, add entries under `[Unreleased]` using [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) categories: `Added`, `Changed`, `Fixed`, `Removed`, `Security`. Example:

  ```markdown
  ## [Unreleased]

  ### Added
  - New command for user profiles

  ### Fixed
  - Resolved connection timeout issue
  ```

- **Database:** After editing models: `uv run db new "short description"` then `uv run db dev`.
- **Tests:** `uv run test quick` during development; `uv run test all` before opening a PR.

### 3. Quality checks

```bash
uv run dev all        # format, lint, type-check
uv run dev pre-commit # full pre-commit suite
```

Individual commands: `uv run dev format`, `uv run dev lint-fix`, `uv run dev type-check`.

Pre-commit runs: JSON/TOML validation, Ruff format/lint, import sorting, basedpyright, pydoclint, gitleaks, and conventional-commit validation.

### 4. Commit

Use [Conventional Commits](https://www.conventionalcommits.org/):

```text
<type>[scope]: <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`. Use lowercase, imperative mood, &lt;120 characters, no trailing period. See [Commit conventions](best-practices/git.md#commit-conventions).

Examples:

```bash
git commit -m "feat(commands): add user profile command"

# With body (for larger changes):
git commit -m "feat: implement user role system

- Add role-based permissions
- Create role assignment commands
- Update permission checks in modules"
```

### 5. Push and open a pull request

- **Members:** `git push origin feat/your-feature`
- **Forks:** `git push origin feat/your-feature`

On GitHub: base = `allthingslinux/tux` and branch = `main`. For forks, head = your fork and compare = your feature branch. You can use the "Compare & pull request" prompt or your fork’s "Contribute" → "Open a pull request".

**PR title:** `[module/area] Brief description` (e.g. `[auth] Add OAuth2 login`, `[database] Optimize user query`).

Link issues with `Closes #123` and explain *why* the change is needed. Keep branches short-lived and [rebase on main](best-practices/git.md#rebasing) before opening or updating a PR.

## Pull Request Process

1. **Checks:** CI must pass. Run locally: `uv run test all`, `uv run dev all`, and `uv run db dev` when migrations change. Ensure type hints and docstrings for public APIs, and update CHANGELOG for user-facing changes.
2. **Review:** Maintainers will review. PRs are discussions—be prepared to explain or adjust. Reviewers check code quality, architecture, testing, and documentation. See [Code review best practices](best-practices/code-review.md).
3. **Merge:** After approval and green CI, the PR is merged and the branch is removed. Changelog versioning and GitHub releases are handled by maintainers; when a version tag is pushed (e.g. `v0.2.0`), the changelog is bumped and a release is created.

## Key resources

| Topic | Doc |
|-------|-----|
| Git, commits, rebasing, pre-commit | [Git best practices](best-practices/git.md) |
| Branch names and types | [Branch naming](best-practices/branch-naming.md) |
| PR checklist and review | [Code review](best-practices/code-review.md) |
| Step-by-step setup | [Development Setup](tutorials/development-setup.md) |
| First-time contributor path | [First Contribution](tutorials/first-contribution.md) |
| CLI (`tux`, `db`, `dev`, `test`, `config`, `docs`) | [CLI reference](../reference/cli.md) |
| Cursor rules and commands | [Creating Cursor rules](guides/creating-cursor-rules.md), [Creating Cursor commands](guides/creating-cursor-commands.md) |

## Troubleshooting

- **Pre-commit / lint / type errors:** `uv run dev format`, `uv run dev lint-fix`, `uv run dev type-check`
- **Merge conflicts:** `git merge --abort` to cancel; or resolve, then `git add` and `git commit` (or `git mergetool`). Prefer rebasing on `main` when possible; see [Rebasing](best-practices/git.md#rebasing).
- **Lost commits:** `git reflog`, then `git checkout <commit-hash>` to restore.
- **Stashing work in progress:** `git stash push -m "wip: short description"` and `git stash pop`.
- **Undoing changes:** uncommitted file `git checkout -- <file>`; undo last commit but keep changes `git reset --soft HEAD~1`; undo last commit and discard `git reset --hard HEAD~1`.

## Getting help

- [Tux documentation](https://tux.atl.dev)
- [Issues](https://github.com/allthingslinux/tux/issues)
- [Discord](https://discord.gg/gpmSjcjQxg) — ask in a development channel

## Code of Conduct and License

- [Code of Conduct](https://github.com/allthingslinux/tux/blob/main/.github/CODE_OF_CONDUCT.md) — be respectful, constructive, and inclusive.
- [License (GPL-3.0)](https://github.com/allthingslinux/tux/blob/main/LICENSE) — by contributing, you agree your contributions are licensed under the same terms.
