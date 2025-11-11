# Contributing to Tux

Thank you for your interest in contributing to Tux! This guide details how to set up your environment, follow the development workflow, and submit your contributions.

We welcome contributions of all kinds, from bug fixes and feature implementations to documentation improvements.

## Contributing Workflows

Tux supports contributions from both organization members and external contributors. The workflow differs slightly based on your access level.

### Organization Members

If you're a member of the **All Things Linux** GitHub organization, you can work directly with the main repository:

* Clone the main repository directly
* Create feature branches in the main repository
* Push branches directly to `origin`
* Use `origin` remote for pulling updates

### External Contributors

If you're contributing from outside the organization, you'll need to work with a fork:

* Fork the repository on GitHub first
* Clone your fork to your local machine
* Add `upstream` remote pointing to the main repository
* Push branches to your fork (`origin`)
* Create pull requests from your fork to the main repository

The setup instructions below will guide you through the appropriate workflow based on your access level.

## Prerequisites

Before you start, ensure you have:

* Git

* [Python](https://www.python.org/) (3.13+ recommended)
  * If you don't have Python installed, we suggest using something like [mise](https://mise.jdx.dev/) or [pyenv](https://github.com/pyenv/pyenv) to manage your Python installations.
  
* [Uv](https://docs.astral.sh/uv/) (recommended)
  * If you don't have Uv installed, use the official installer and verify:

    ```bash
    # Linux/macOS
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Verify installation
    uv --version
    ```

* A PostgreSQL Database (local or remote)
  * We personally use Supabase for our database needs, but any PostgreSQL database will work. Supabase provides a generous free tier and can be set up in minutes.

* (Typically) A Discord bot token

* (Optional) Docker & Docker Compose v2

## Development Setup

Follow these steps to set up your local development environment. For more comprehensive details, refer to the [Tux documentation site](https://tux.atl.dev).

### For Organization Members

1. **Clone the Repository**

    Clone the main repository directly:

    ```bash
    git clone https://github.com/allthingslinux/tux.git && cd tux
    ```

2. **Install Dependencies with Uv**

    Ensure Uv is installed and using the correct Python version (project requires 3.13.x).

    ```bash
    # (Optional) Pin the Python version used by uv
    uv python pin 3.13.5

    # Create the virtual environment and install all dependencies
    uv sync

    # Install pre-commit hooks for quality checks
    uv run pre-commit install
    ```

3. **Configure Environment Variables**

    Generate example configuration files if needed, then copy and edit the environment file:

    ```bash
    # Generate example config files (creates .env.example if it doesn't exist)
    uv run config generate

    # Copy the example to create your .env file
    cp .env.example .env
    ```

    Edit `.env` and provide at least:

    * `BOT_TOKEN`: Your Discord bot token.
    * Database configuration (choose one option):

      **Option 1: Individual PostgreSQL variables (Recommended)**

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

    * `USER_IDS__BOT_OWNER_ID`: Your Discord user ID (required for bot owner permissions).

4. **Configure Bot Settings**

    Copy the example configuration file.

    ```bash
    cp config/config.toml.example config/config.toml
    ```

    Review `config/config.toml` and customize it as needed.

    **Note:** The configuration system supports TOML, YAML, and JSON formats. You can also generate example configs:

    ```bash
    uv run config generate
    ```

5. **Initialize Development Database**

    Run database migrations to set up your development database.

    ```bash
    # Initialize database with migrations (recommended for new projects)
    uv run db init

    # Or if you need to apply pending migrations
    uv run db push
    ```

### For External Contributors

1. **Fork and Clone the Repository**

    You'll need to create your own copy (a "fork") on GitHub first. This allows you to make changes in your own workspace before proposing them to the main project via a Pull Request.

    * Navigate to the [Tux repository](https://github.com/allthingslinux/tux).
    * Click the "Fork" button in the upper right corner.
    * Choose your GitHub account as the owner.
    * Optionally, uncheck "Copy the `main` branch only" if you need all branches, though usually only the default branch is needed for contributions.
    * Click "Create fork".

    Once your fork is created (e.g., `https://github.com/yourusername/tux`), clone it to your local machine:

    ```bash
    git clone https://github.com/yourusername/tux.git && cd tux
    ```

    **Configure `upstream` Remote:**

    Add the original `allthingslinux/tux` repository as a remote named `upstream`. This makes it easier to fetch changes from the main project.

    ```bash
    git remote add upstream https://github.com/allthingslinux/tux.git
    
    # Verify the remotes
    git remote -v
    ```

2. **Install Dependencies with Uv**

    Ensure Uv is installed and using the correct Python version (project requires 3.13.x).

    ```bash
    # (Optional) Pin the Python version used by uv
    uv python pin 3.13.5

    # Create the virtual environment and install all dependencies
    uv sync

    # Install pre-commit hooks for quality checks
    uv run pre-commit install
    ```

3. **Configure Environment Variables**

    Generate example configuration files if needed, then copy and edit the environment file:

    ```bash
    # Generate example config files (creates .env.example if it doesn't exist)
    uv run config generate

    # Copy the example to create your .env file
    cp .env.example .env
    ```

    Edit `.env` and provide at least:

    * `BOT_TOKEN`: Your Discord bot token.
    * Database configuration (choose one option):

      **Option 1: Individual PostgreSQL variables (Recommended)**

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

    * `USER_IDS__BOT_OWNER_ID`: Your Discord user ID (required for bot owner permissions).

4. **Configure Bot Settings**

    Copy the example configuration file.

    ```bash
    cp config/config.toml.example config/config.toml
    ```

    Review `config/config.toml` and customize it as needed.

    **Note:** The configuration system supports TOML, YAML, and JSON formats. You can also generate example configs:

    ```bash
    uv run config generate
    ```

5. **Initialize Development Database**

    Run database migrations to set up your development database.

    ```bash
    # Initialize database with migrations (recommended for new projects)
    uv run db init

    # Or if you need to apply pending migrations
    uv run db push
    ```

## Development Workflow

### Branching Strategy

Tux uses **trunk-based development** with a single `main` branch that is always production-ready. All changes flow through feature branches that merge directly to main.

**Branch Naming Conventions:**

* **Features**: `feat/description` (e.g., `feat/add-user-authentication`)
* **Bug fixes**: `fix/issue-description` (e.g., `fix/database-connection-leak`)
* **Hotfixes**: `hotfix/critical-issue` (e.g., `hotfix/security-vulnerability`)
* **Documentation**: `docs/update-section` (e.g., `docs/update-api-reference`)

**Branch Lifecycle:**

1. **Create**: Branch from main for new features/fixes
2. **Develop**: Make changes, run tests, ensure quality
3. **Merge**: Use squash merge or fast-forward to keep history clean
4. **Delete**: Remove branch after successful merge

**Key Principles:**

* Keep branches short-lived (1-3 days maximum)
* Merge to main frequently
* Ensure main stays deployable at all times

1. **Create a Feature Branch**

    Create a new branch from your local `main` branch with a descriptive name following our conventions:

    ```bash
    git checkout main

    # Create and switch to your new branch such as:
    git checkout -b feat/your-feature-name    # For new features
    git checkout -b fix/issue-description     # For bug fixes
    git checkout -b docs/update-section       # For documentation changes
    ```

    **Keeping Your Branches Updated**

    Regularly sync your local `main` branch with the repository:

    **For Organization Members:**

    ```bash
    # Switch to main branch
    git checkout main

    # Fetch and merge changes from origin
    git pull origin main
    ```

    **For External Contributors:**

    ```bash
    # Switch to main branch
    git checkout main

    # Fetch and merge upstream changes
    git pull upstream main

    # Update your fork on GitHub (optional)
    git push origin main
    ```

    To update your feature branch with the latest changes:

    **For Organization Members:**

    ```bash
    # Option 1: Merge main into your feature branch
    git checkout feature/your-feature-name
    git merge main

    # Option 2: Rebase your feature branch on main (cleaner history)
    git checkout feature/your-feature-name
    git rebase origin/main
    ```

    **For External Contributors:**

    ```bash
    # Option 1: Merge main into your feature branch
    git checkout feature/your-feature-name
    git merge main

    # Option 2: Rebase your feature branch on main (cleaner history)
    git checkout feature/your-feature-name
    git rebase upstream/main
    ```

2. **Implement Changes**
    * Write clear, concise, and well-documented code.
      * Use [Numpy style](https://numpydoc.readthedocs.io/en/latest/format.html) for docstrings.
      * Use type hints extensively (`Type | None` not `Optional[Type]`).
    * Update relevant documentation (`docs/content/`) if necessary.
    * **Update CHANGELOG.md** if your changes are user-facing:
      * Add entries to the `[Unreleased]` section
      * Use appropriate categories: `Added`, `Changed`, `Fixed`, `Removed`, `Security`
      * Follow the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format
      * Example:

        ```markdown
        ## [Unreleased]

        ### Added
        - New command for user profiles
        - Database migration system

        ### Fixed
        - Resolved connection timeout issue
        ```

    * **For Database Changes:**

      ```bash
      # Modify database models
      # ... edit models ...

      # Generate migration
      uv run db new "add user preferences table"

      # Apply migration
      uv run db dev
      ```

    * Test your changes thoroughly.
    * Run tests frequently during development:

      ```bash
      # Quick test run (no coverage)
      uv run tests quick

      # Full test suite with coverage
      uv run tests all
      ```

3. **Run Quality Checks**

    Use the `dev` CLI to format, lint, and type-check your code. Running these locally ensures faster feedback before committing.

    ```bash
    # Format code using Ruff
    uv run dev format

    # Lint code using Ruff (with auto-fix)
    uv run dev lint-fix

    # Type-check code using basedpyright
    uv run dev type-check

    # Run all development checks (formatting, linting, type-checking, etc.)
    uv run dev all

    # Run all pre-commit checks (includes formatting, linting, etc.)
    uv run dev pre-commit
    ```

    **Pre-commit Hooks:**

    Pre-commit hooks run automatically on commit and perform:

    * JSON/TOML validation for config files
    * Code formatting with Ruff
    * Import sorting
    * Type checking with basedpyright
    * Linting with Ruff
    * Docstring validation with pydoclint
    * Secret scanning with gitleaks
    * Commit message validation (conventional commits)

    Fix any issues reported by these tools.

4. **Commit Your Changes**

    Stage your changes and write a meaningful commit message following the [Conventional Commits](https://www.conventionalcommits.org/) specification.

    **Commit Format:**

    ```text
    <type>[scope]: <description>

    [optional body]

    [optional footer]
    ```

    **Commit Types:**

    | Type | Description | Example |
    |------|-------------|---------|
    | `feat` | New feature | `feat: add user authentication` |
    | `fix` | Bug fix | `fix: resolve memory leak in message handler` |
    | `docs` | Documentation | `docs: update API documentation` |
    | `style` | Code style changes | `style: format imports with ruff` |
    | `refactor` | Code refactoring | `refactor(database): optimize query performance` |
    | `perf` | Performance improvement | `perf: improve caching strategy` |
    | `test` | Tests | `test: add unit tests for config validation` |
    | `build` | Build system | `build: update Docker configuration` |
    | `ci` | CI/CD | `ci: add coverage reporting` |
    | `chore` | Maintenance | `chore: update dependencies` |
    | `revert` | Revert changes | `revert: undo authentication changes` |

    **Examples:**

    ```bash
    # Simple commit
    git commit -m "feat(command): add user profile command"

    # Commit with body (for complex changes)
    git commit -m "feat: implement user role system

    - Add role-based permissions
    - Create role assignment commands
    - Update permission checks in modules"

    # Other examples
    git commit -m "fix(command): fix database connection error"
    git commit -m "docs(readme): update contribution guidelines"
    git commit -m "chore(changelog): update unreleased section"
    ```

    **Commit Message Guidelines:**
    * Use lowercase for the type and scope
    * Keep subject line under 120 characters
    * No period at the end of the subject
    * Start with lowercase letter
    * Use imperative mood ("add" not "added")
    * Avoid generic messages like "fix bug" or "update" - be specific

5. **Push and Create a Pull Request**

    **For Organization Members:**

    * Push your feature branch to the main repository:

      ```bash
      git push origin feature/your-descriptive-feature-name
      ```

    * Navigate to the [Tux repository](https://github.com/allthingslinux/tux) on GitHub.
    * GitHub often shows a prompt to create a Pull Request from your recently pushed branch.
    * Ensure the base repository is `allthingslinux/tux` and the base branch is `main`.
    * **PR Title Format**: Use `[module/area] Brief description`
      * Examples: `[auth] Add OAuth2 login system`, `[database] Optimize user query performance`, `[ui] Improve embed styling`
    * Provide a clear title and description for your PR, linking any relevant issues (e.g., `Closes #123`). Explain *why* the changes are being made.
    * Click "Create pull request".

    **For External Contributors:**

    * Push your feature branch to your fork on GitHub:

      ```bash
      git push origin feature/your-descriptive-feature-name
      ```

    * Navigate to the [Tux repository](https://github.com/allthingslinux/tux) on GitHub.
    * GitHub often shows a prompt to create a Pull Request from your recently pushed branch. You can also navigate to your fork (`https://github.com/yourusername/tux`) and click the "Contribute" button, then "Open a pull request".
    * Ensure the base repository is `allthingslinux/tux` and the base branch is `main` (or the appropriate target branch).
    * Ensure the head repository is your fork and the compare branch is your feature branch.
    * **PR Title Format**: Use `[module/area] Brief description`
      * Examples: `[auth] Add OAuth2 login system`, `[database] Optimize user query performance`, `[ui] Improve embed styling`
    * Provide a clear title and description for your PR, linking any relevant issues (e.g., `Closes #123`). Explain *why* the changes are being made.
    * Click "Create pull request".

## Pull Request Process

1. **Checks:** Ensure your PR passes all automated checks (CI/CD pipeline).
   * All tests must pass (`uv run tests all`)
   * Code quality checks must pass (`uv run dev all`)
   * Database migrations tested (`uv run db dev`)
   * Documentation updated if applicable
   * Type hints complete and accurate
   * Docstrings added for public APIs
   * CHANGELOG.md updated for user-facing changes

2. **Review:** Project maintainers will review your PR. Be responsive to feedback and make necessary changes.
    * Pull requests are discussions. Be prepared to explain your changes or make adjustments based on feedback.
    * Don't be discouraged if changes are requested or if a PR isn't merged; the feedback process helps improve the project.
    * Reviewers will check:

      * Code quality (PEP 8, type hints, naming)
      * Architecture (follows existing patterns, proper error handling)
      * Testing (adequate coverage, edge cases)
      * Documentation (docstrings, comments, updated docs)

3. **Merge:** Once approved and checks pass, your PR will be merged.
   * After merging, maintainers will handle releases and changelog versioning automatically
   * When a version tag is pushed (e.g., `v0.2.0`), the changelog is automatically bumped and a GitHub release is created
   * Branch will be deleted after successful merge

## Git Best Practices

### Keeping Your Branch Updated

**Rebasing (Recommended for Clean History):**

**For Organization Members:**

```bash
# Keep branch up to date with main
git checkout feature/your-branch

# Fetch and rebase on origin/main
git fetch origin
git rebase origin/main

# Resolve conflicts if they occur
# ... fix conflicts ...
git add <resolved-files>
git rebase --continue

# Force push after rebase (since history changed)
git push origin feature/your-branch --force-with-lease
```

**For External Contributors:**

```bash
# Keep branch up to date with main
git checkout feature/your-branch

# Fetch and rebase on upstream/main
git fetch upstream
git rebase upstream/main

# Resolve conflicts if they occur
# ... fix conflicts ...
git add <resolved-files>
git rebase --continue

# Force push after rebase (since history changed)
git push origin feature/your-branch --force-with-lease
```

**When to Rebase:**

* Before creating a pull request
* When main has moved significantly ahead
* To keep your branch current with latest changes

**⚠️ Avoid rebasing public branches that others are working on.**

### Stashing Work in Progress

```bash
# Save work in progress
git stash push -m "wip: user auth"

# Apply saved work
git stash pop
```

### Undoing Changes

```bash
# Undo uncommitted changes to a file
git checkout -- file.py

# Undo last commit (keeping changes staged)
git reset --soft HEAD~1

# Undo last commit (discarding changes)
git reset --hard HEAD~1
```

## Troubleshooting

### Pre-commit Hooks Fail

```bash
# Run hooks manually to see issues
uv run dev lint
uv run dev type-check

# Fix formatting issues
uv run dev format
```

### Merge Conflicts

```bash
# Abort merge and start fresh
git merge --abort

# Use mergetool to resolve conflicts
git mergetool

# After resolving, complete merge
git commit
```

### Lost Commits

```bash
# Find lost commits
git reflog

# Restore from reflog
git checkout <commit-hash>
```

## Getting Help

* Check the [Tux documentation site](https://tux.atl.dev) for comprehensive guides and API reference.
* Review existing [Issues](https://github.com/allthingslinux/tux/issues).
* Join the **atl.dev** [Discord server](https://discord.gg/gpmSjcjQxg) and ask in a relevant development channel.

## Code of Conduct

All contributors are expected to adhere to the project's [Code of Conduct](https://github.com/allthingslinux/tux/blob/main/.github/CODE_OF_CONDUCT.md). Be respectful, constructive, and inclusive.

## License

By contributing to Tux, you agree that your contributions will be licensed under the [GNU General Public License v3.0](https://github.com/allthingslinux/tux/blob/main/LICENSE).
