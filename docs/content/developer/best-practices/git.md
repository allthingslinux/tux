---
title: Git Best Practices
description: Git best practices for Tux development, including branching strategy, commit conventions, and workflow automation.
tags:
  - developer-guide
  - best-practices
  - git
---

# Git Best Practices

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

## Contributing Workflows

Tux supports contributions from organization members and external contributors.

### Organization Members

Work directly with the main repository:

```bash
git clone https://github.com/allthingslinux/tux.git
cd tux
git checkout main && git pull origin main
git checkout -b feature/your-feature-name
# ... make changes and commits ...
git push origin feature/your-feature-name
# Create PR via GitHub interface
```

### External Contributors

Work with a fork:

```bash
# Fork repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/tux.git
cd tux
git remote add upstream https://github.com/allthingslinux/tux.git
git checkout main && git pull upstream main
git checkout -b feature/your-feature-name
# ... make changes and commits ...
git push origin feature/your-feature-name
# Create PR from fork to upstream main
```

## Branching Strategy

Tux uses trunk-based development with a single main branch that is always production-ready.

### Main Branch

- **`main`** - The single source of truth, always deployable to production
- All changes flow through feature branches that merge directly to main
- Continuous integration ensures main stays in a deployable state

### Feature Branches

```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/brief-description

# Example
git checkout -b feature/add-user-authentication
```

### Branch Lifecycle

1. **Create**: Branch from main for new features/fixes
2. **Develop**: Make changes, run tests, ensure quality
3. **Merge**: Use squash merge or fast-forward to keep history clean
4. **Delete**: Remove branch after successful merge

### Branch Naming Convention

See our [branch naming](./branch-naming.md) conventions.

## Commit Conventions

Tux uses [Conventional Commits](https://conventionalcommits.org/) for consistent commit messages.

### Format

```text
<type>[scope]: <description>
```

### Types

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

### Rules

- Lowercase type, max 120 chars, no trailing period
- Start with lowercase, use imperative mood

### Examples

```bash
feat: add user authentication system
fix: resolve memory leak in message handler
refactor(database): optimize query performance
test: add integration tests for Discord commands
```

## Development Workflow

### Setup

```bash
git clone https://github.com/allthingslinux/tux.git
cd tux
uv sync
cp .env.example .env
cp config/config.toml.example config/config.toml
```

### Development

```bash
git checkout main && git pull origin main  # or upstream for forks
git checkout -b feature/your-feature-name
# ... edit code ...
uv run dev all      # Run quality checks
uv run test quick   # Run tests
git push origin feature/your-feature-name
```

**Key Principles:**

- Short-lived branches (1-3 days max)
- Merge to main daily
- Keep main always deployable

### Database Changes

```bash
# Modify models, then:
uv run db new "description"
uv run db dev
```

### Commit

```bash
uv run dev pre-commit  # Quality checks
uv run test all        # Full test suite
git commit -m "feat: add user preferences system"
```

## Pre-commit Hooks

Tux uses comprehensive pre-commit hooks to maintain code quality. All hooks run automatically on commit.

### Quality Checks

- **JSON/TOML validation**: Ensures config files are valid
- **Code formatting**: Ruff handles Python formatting
- **Import sorting**: Maintains consistent import order
- **Type checking**: basedpyright validates types
- **Linting**: Ruff catches code issues
- **Docstring validation**: pydoclint ensures proper documentation
- **Secret scanning**: gitleaks prevents credential leaks
- **Commit message validation**: commitlint enforces conventional commits using `.commitlintrc.json` configuration

### Commitlint Configuration

The `.commitlintrc.json` file defines strict rules for conventional commit messages:

**Type Rules:**

- Must use allowed types: `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`, `style`, `test`
- Types must be lowercase, 1-15 characters
- Type cannot be empty

**Scope Rules (Optional):**

- Must be lowercase, 1-20 characters
- Used for grouping related changes (e.g., `feat(auth)`, `fix(database)`)

**Subject Rules:**

- Cannot be empty, max 120 characters
- No trailing period, no exclamation marks
- Cannot start with sentence case, start case, pascal case, or upper case
- Must start with lowercase and use imperative mood

**Header Rules:**

- Minimum 10 characters, maximum 120 characters
- Must be trimmed (no leading/trailing whitespace)

**Body Rules (Optional):**

- Must have leading blank line if present
- Maximum line length 120 characters

**Footer Rules (Optional):**

- Must have leading blank line if present
- Maximum line length 120 characters

### Running Checks

```bash
# Run all pre-commit checks
uv run dev pre-commit

# Run individual checks
uv run dev lint          # Code quality
uv run dev format        # Code formatting
uv run dev type-check    # Type validation
```

## Pull Request Process

### Creating a PR

1. Push branch to remote
2. Create PR with title format: `[module/area] Brief description`
3. Include context, changes, and testing notes

### Requirements

- All tests pass (`uv run test all`)
- Code quality checks pass (`uv run dev all`)
- Database migrations tested (`uv run db dev`)
- Documentation updated if needed
- Type hints and docstrings complete

### Title Examples

```text
[auth] Add OAuth2 login system
[database] Optimize user query performance
[ui] Improve embed styling for mobile
```

## Code Review Guidelines

### Reviewer Checklist

**Code Quality:**

- Follows Python standards and type hints
- Functions focused with descriptive names
- No unused imports/variables

**Architecture:**

- Follows existing patterns
- Proper database transactions and error handling
- Security considerations addressed

**Testing:**

- Unit/integration tests for new features
- Edge cases covered, existing tests pass

**Documentation:**

- Docstrings for public APIs
- Complex logic commented

### Review Process

1. Automated CI checks must pass
2. Review architecture and approach first
3. Detailed line-by-line code review
4. Verify test coverage
5. Minimum one maintainer approval

## Git Hygiene

### Commit History

Write meaningful messages following conventional commits:

```bash
git commit -m "feat: implement user role system

- Add role-based permissions
- Create role assignment commands
- Update permission checks in modules"
```

❌ Avoid: "fix bug", "update"
✅ Use: "fix: resolve null pointer in user lookup"

### Rebasing

Keep branches current with main:

```bash
git fetch origin  # or upstream for forks
git rebase origin/main
# Resolve conflicts, then:
git rebase --continue
git push origin feature/branch --force-with-lease
```

Rebase before PRs, avoid on shared branches.

### Quick Commands

```bash
git stash push -m "wip: description"  # Save work
git stash pop                         # Restore work
git checkout -- file.py               # Undo uncommitted changes
git reset --soft HEAD~1               # Undo last commit (keep changes)
```

## Troubleshooting

### Common Issues

**Pre-commit hooks fail:**

```bash
uv run dev lint        # Check issues
uv run dev type-check  # Type validation
uv run dev format      # Fix formatting
```

**Merge conflicts:**

```bash
git merge --abort      # Start over
git mergetool          # Use merge tool
git commit             # Complete after resolving
```

**Lost commits:**

```bash
git reflog             # Find lost commits
git checkout <hash>    # Restore commit
```

### Getting Help

- Check existing PRs for patterns
- Review commit history examples
- Ask in [Discord](https://discord.gg/gpmSjcjQxg)
- Review documentation workflows

## Resources

- [Conventional Commits](https://conventionalcommits.org/)
- [Git Documentation](https://git-scm.com/doc)
- [Pre-commit Documentation](https://pre-commit.com/)
- [Trunk-Based Development](https://trunkbaseddevelopment.com/)
