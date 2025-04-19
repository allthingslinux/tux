# Contributing to Tux

Thank you for your interest in contributing to Tux! This guide will help you get started with contributing to the project.

## Development Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/allthingslinux/tux.git
   cd tux
   ```

2. **Set Up Development Environment**

   ```bash
   # Using Poetry (recommended)
   poetry env use 3.13
   poetry install
   
   # Set up pre-commit hooks
   poetry run pre-commit install
   ```

3. **Configure Environment**

   ```bash
   # Copy example environment file
   cp .env.example .env
   ```

   Edit .env with your own values for:

   - DEV_BOT_TOKEN
   - DEV_DATABASE_URL
   - PROD_BOT_TOKEN
   - PROD_DATABASE_URL

4. **Database Setup**

   ```bash
   # Generate Prisma client
   poetry run tux db generate

   # Push the db
   poetry run tux db push
   ```

## Development Workflow

1. **Create a New Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Write clean, documented code
   - Add tests for new features
   - Update documentation as needed

3. **Run Tests**

   ```bash
   poetry run pytest
   ```

4. **Format and Lint**

   ```bash
   # Format code
   poetry run ruff format .
   
   # Run linter
   poetry run ruff check .
   ```

5. **Commit Your Changes**

   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/) format:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `refactor:` for code refactoring
   - `test:` for adding tests
   - `chore:` for maintenance tasks

6. **Submit a Pull Request**
   - Push your branch to GitHub
   - Create a Pull Request with a clear description
   - Link any related issues

## Code Style Guidelines

1. **Python Style**
   - Follow PEP 8 guidelines
   - Use type hints
   - Maximum line length: 88 characters
   - Use docstrings for all public functions/classes

2. **Documentation**
   - Keep docstrings up to date
   - Add examples for complex functionality
   - Update relevant documentation files

3. **Testing**
   - Write unit tests for new features
   - Maintain test coverage
   - Use meaningful test names

## Pull Request Guidelines

1. **Before Submitting**
   - Ensure all tests pass
   - Run formatters and linters
   - Update documentation
   - Test your changes locally

2. **PR Description**
   - Clearly describe the changes
   - Link related issues
   - Include screenshots for UI changes
   - List any breaking changes

3. **Review Process**
   - Address review comments promptly
   - Keep the PR focused and small
   - Be open to feedback

## Getting Help

- Join our [Discord server](https://discord.gg/your-server) for help
- Check existing issues and discussions
- Read our [Architecture Overview](architecture.md)

## Code of Conduct

Please read and follow our [Code of Conduct](../../CODE_OF_CONDUCT.md). We expect all contributors to:

- Be respectful and inclusive
- Accept constructive criticism
- Focus on what is best for the community
- Show empathy towards others

## License

By contributing to Tux, you agree that your contributions will be licensed under the project's license.
