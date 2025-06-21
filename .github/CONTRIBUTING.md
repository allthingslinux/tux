# Contributing to Tux

Thank you for your interest in contributing to Tux! This guide details how to set up your environment, follow the development workflow, and submit your contributions.

We welcome contributions of all kinds, from bug fixes and feature implementations to documentation improvements.

## Prerequisites

Before you start, ensure you have:

* Git

* [Python](https://www.python.org/) (3.13+ recommended)
  * If you don't have Python installed, we suggest using something like [mise](https://mise.jdx.dev/) or [pyenv](https://github.com/pyenv/pyenv) to manage your Python installations.
  
* [Poetry](https://python-poetry.org/docs/) (1.2+ recommended)
  * If you don't have Poetry installed, you can use one of the official methods. We recommend using the official installer:

    ```bash
    # Linux, macOS, Windows (WSL)
    curl -sSL https://install.python-poetry.org | python3 -

    # After installation and ensuring Poetry is in your PATH, you can verify it by running:
    poetry --version
    ```

* A PostgreSQL Database (local or remote)
  * We personally use Supabase for our database needs, but any PostgreSQL database will work. Supabase provides a generous free tier and can be set up in minutes.

* (Typically) A Discord bot token

* (Optional) Docker & Docker Compose v2

## Development Setup

Follow these steps to set up your local development environment. For more comprehensive details, refer to the main [DEVELOPER.md](https://github.com/allthingslinux/tux/blob/main/DEVELOPER.md) guide.

1. **Fork and clone the repository**

    If you do not have direct write access to the `allthingslinux/tux` repository, you'll need to create your own copy (a "fork") on GitHub first. This allows you to make changes in your own workspace before proposing them to the main project via a Pull Request.

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

2. **Install Dependencies with Poetry**

    Ensure Poetry is installed and configured to use the correct Python version (e.g., 3.13.5).

    ```bash
    # Create a virtual environment
    poetry env use 3.13.5

    # Install project dependencies and dev tools
    poetry install

    # Install pre-commit hooks for quality checks
    poetry run pre-commit install
    ```

3. **Configure Environment Variables**

    Copy the example environment file and fill in your details.

    `cp .env.example .env`

    Edit `.env` and provide at least:

    * `DEV_BOT_TOKEN`: Your Discord bot token for development.

    * `DEV_DATABASE_URL`: Connection string for your development PostgreSQL database.

      * Example: `postgresql://user:pass@host:port/db_name`

4. **Configure Bot Settings**

    Copy the example settings file.

    `cp config/settings.yml.example config/settings.yml`

    Review `config/settings.yml` and customize it.

    **Crucially, add your Discord User ID to the `BOT_OWNER` list.**

5. **Initialize Development Database**

    Push the Prisma schema to your development database. This also generates the Prisma client.

    ```bash
    # Use --dev or rely on the default development mode
    poetry run tux --dev db push
    ```

## Development Workflow

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

    Regularly sync your local `main` branch with the upstream repository:

    ```bash
    # Switch to main branch
    git checkout main

    # Fetch and merge upstream changes
    git pull upstream main

    # Update your fork on GitHub (optional)
    git push origin main
    ```

    To update your feature branch with the latest changes:

    ```bash
    # Option 1: Merge main into your feature branch
    git checkout feature/your-feature-name
    git merge main

    # Option 2: Rebase your feature branch on main (cleaner history)
    git checkout feature/your-feature-name
    git rebase main
    ```

2. **Implement Changes**
    * Write clear, concise, and well-documented code.
      * Use [Numpy style](https://numpydoc.readthedocs.io/en/latest/format.html) for docstrings.
      * Use type hints extensively.
    * Update relevant documentation (`docs/content/`) if necessary.
    * Test your changes thoroughly.

3. **Run Quality Checks**

    Use the `tux` CLI to format, lint, and type-check your code. Running these locally ensures faster feedback before committing.

    ```bash
    # Format code using Ruff
    poetry run tux dev format

    # Lint code using Ruff
    poetry run tux dev lint-fix

    # Type-check code using Pyright
    poetry run tux dev type-check

    # Run all pre-commit checks (includes formatting, linting, etc.)
    poetry run tux dev pre-commit
    ```

    Fix any issues reported by these tools.

4. **Commit Your Changes**

    Stage your changes and write a meaningful commit message following the [Conventional Commits](https://www.conventionalcommits.org/) specification.

    ```bash
    git add .
    git commit -m "feat(command): add user profile command"
    # or
    git commit -m "fix(command): fix database connection error"
    # or
    git commit -m "docs(readme): update contribution guidelines"
    ```

5. **Push and Create a Pull Request**
    * Push your feature branch to your fork on GitHub.

    `git push origin feature/your-descriptive-feature-name`

    * Navigate to the [Tux repository](https://github.com/allthingslinux/tux) on GitHub.
    * GitHub often shows a prompt to create a Pull Request from your recently pushed branch. You can also navigate to your fork (`https://github.com/yourusername/tux`) and click the "Contribute" button, then "Open a pull request".
    * Ensure the base repository is `allthingslinux/tux` and the base branch is `main` (or the appropriate target branch).
    * Ensure the head repository is your fork and the compare branch is your feature branch.
    * Provide a clear title and description for your PR, linking any relevant issues (e.g., `Closes #123`). Explain *why* the changes are being made.
    * Click "Create pull request".

## Pull Request Process

1. **Checks:** Ensure your PR passes all automated checks (CI/CD pipeline).
2. **Review:** Project maintainers will review your PR. Be responsive to feedback and make necessary changes.
    * Pull requests are discussions. Be prepared to explain your changes or make adjustments based on feedback.
    * Don't be discouraged if changes are requested or if a PR isn't merged; the feedback process helps improve the project.
3. **Merge:** Once approved and checks pass, your PR will be merged.

## Getting Help

* Check the main [DEVELOPER.md](https://github.com/allthingslinux/tux/blob/main/DEVELOPER.md) guide for more in-depth information.
* Review existing [Issues](https://github.com/allthingslinux/tux/issues).
* Join the **atl.dev** [Discord server](https://discord.gg/gpmSjcjQxg) and ask in a relevant development channel.

## Code of Conduct

All contributors are expected to adhere to the project's [Code of Conduct](https://github.com/allthingslinux/tux/blob/main/.github/CODE_OF_CONDUCT.md). Be respectful, constructive, and inclusive.

## License

By contributing to Tux, you agree that your contributions will be licensed under the [GNU General Public License v3.0](https://github.com/allthingslinux/tux/blob/main/LICENSE).
