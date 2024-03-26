## Installation
`poetry install`                           # Install dependencies with Poetry.
`poetry run pre-commit install`            # Install pre-commit hooks.

## Development
`poetry run python tux/main.py`            # Run the application with Poetry.
`poetry run pytest`                        # Run all tests.

## Docker
`docker-compose up`                        # Run the application with Docker.

## Linting
`poetry run pre-commit run --all-files`    # Run all pre-commit hooks.
`poetry run pre-commit run <hook_id>`      # Run a specific pre-commit hook.

## Linting and Formatting
`poetry run ruff check`                    # Lint all files in the current directory.
`poetry run ruff check --fix`              # Lint all files in the current directory, and fix any fixable errors.
`poetry run ruff check --watch`            # Lint all files in the current directory, and re-lint on change.
`poetry run ruff check path/to/code/`      # Lint all files in `path/to/code` (and any subdirectories).
`poetry run ruff format`                   # Format all files in the current directory.
`poetry run ruff format path/to/code/`     # Lint all files in `path/to/code` (and any subdirectories).
`poetry run ruff format path/to/file.py`   # Format a single file.

## Git
`git checkout -b <branch_name>`            # Create a new branch.
`git checkout <branch_name>`               # Switch to an existing branch.
`git pull`                                 # Pull changes from the remote repository.
`git branch -d <branch_name>`              # Delete a branch.
`git status`                               # Check the status of the repository.
`git diff`                                 # Show changes between commits, commit and working tree, etc.
`git log`                                  # Show commit logs.
`git remote -v`                            # Show remote repositories.
`git remote add origin <repository_url>`   # Add a remote repository.
`git add .`                                # Add all files to the staging area.
`git commit -m "Your commit message"`      # Commit changes with a message.
`git push`                                 # Push changes to the remote repository.