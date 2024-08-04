# Project Documentation 

This document outlines the essential commands and workflows needed for the installation, development, and management of this project. Each section provides relevant commands and instructions for specific tasks.

## Table of Contents

- [Project Documentation](#project-documentation)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Development](#development)
  - [Docker](#docker)
  - [Linting](#linting)
  - [Linting and Formatting](#linting-and-formatting)
  - [Git](#git)

## Installation

To install necessary dependencies and set up the environment, use the following commands:

```sh
# Install dependencies with Poetry.
poetry install

# Activate the virtual environment.
poetry shell

# Install pre-commit hooks.
poetry pre-commit install
```

## Development

For running the application and executing tests, use these commands:

```sh
# Run the application with Poetry.
poetry run python tux/main.py
```

## Docker

To run the application using Docker, use the following command:

```sh
# Run the application with Docker.
docker compose up --build -d
```

## Linting

Utilize these commands to run all pre-commit hooks or specific ones:

```sh
# Run all pre-commit hooks.
poetry run pre-commit run --all-files

# Run a specific pre-commit hook.
poetry run pre-commit run <hook_id>
```

## Linting and Formatting

Commands for linting and formatting files are as follows:

```sh
# Lint all files in the current directory.
poetry run ruff check

# Lint all files in the current directory and fix any fixable errors.
poetry run ruff check --fix

# Lint all files in the current directory and re-lint on changes.
poetry run ruff check --watch

# Format all files in the current directory.
poetry run ruff format .
```

## Git

Common Git commands for repository management are listed below:

```sh
# Create a new branch.
git checkout -b <branch_name>

# Switch to an existing branch.
git checkout <branch_name>

# Pull changes from the remote repository.
git pull

# Delete a branch.
git branch -d <branch_name>

# Check the status of the repository.
git status

# Show changes between commits, commit and working tree, etc.
git diff

# Show commit logs.
git log

# Show remote repositories.
git remote -v

# Add a remote repository.
git remote add origin <repository_url>

# Add all files to the staging area.
git add .

# Commit changes with a message.
git commit -m "Your commit message"

# Push changes to the remote repository.
git push
```