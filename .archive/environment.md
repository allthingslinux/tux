# Getting Started

This guide will help you get started with setting up your development environment for Tux, and getting the bot running on your local machine.

## Prerequisites

- Python 3.13.2+
- Poetry 2.0.1+

## Installation

1. Clone the repository

```bash
git clone https://github.com/allthingslinux/tux.git && cd tux
```

2. Set and activate the virtual environment

```bash
poetry env use 3.13
```

> Learn more about managing and activating virtual environments here: <https://python-poetry.org/docs/managing-environments/>

3. Install dependencies

```bash
poetry install --with dev, docs
```

4. Install the pre-commit hooks

We use pre-commit to ensure code quality, secrets protection, and more.

```bash
poetry run pre-commit install
```

5. Set up the environment variables

```bash
cp .env.example .env
```

6. Set up the configuration settings

```bash
cp config/settings.yml.example config/settings.yml
```

7. Generate the Prisma client

```bash
poetry run db-generate
```

8. Push the database schema to the database

```bash
poetry run db-push
```

9. Run the bot

```bash
poetry run start
```

10. Sync the bot command tree

Assuming your bot prefix is `$`, you can sync the command tree in Discord with the following command:

```bash
$dev sync
```
