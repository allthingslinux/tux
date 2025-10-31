---
title: Git Best Practices
---

Git best practices for Tux development, including branching strategy, commit conventions, and workflow automation.

## Contributing Workflows

Tux is an open source project that supports contributions from both organization members and external contributors. The workflow differs slightly based on your access level.

### Organization Members

If you're a member of the All Things Linux GitHub organization, you can work directly with the main repository.

```bash
# Clone the main repository
git clone https://github.com/allthingslinux/tux.git
cd tux

# Create feature branch directly in main repo
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# ... make changes and commits ...

# Push branch to main repository
git push origin feature/your-feature-name

# Create pull request through GitHub interface
```

### External Contributors

If you're contributing from outside the organization, you'll need to work with a fork of the repository.

```bash
# Fork the repository on GitHub (click "Fork" button)

# Clone your fork
git clone https://github.com/YOUR_USERNAME/tux.git
cd tux

# Add upstream remote
git remote add upstream https://github.com/allthingslinux/tux.git

# Create feature branch
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name

# ... make changes and commits ...

# Push to your fork
git push origin feature/your-feature-name

# Create pull request from your fork to upstream main
# Go to https://github.com/allthingslinux/tux/pulls and click "New Pull Request"
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

- **Features**: `feature/description` (e.g., `feature/add-user-authentication`)
- **Bug fixes**: `fix/issue-description` (e.g., `fix/database-connection-leak`)
- **Hotfixes**: `hotfix/critical-issue` (e.g., `hotfix/security-vulnerability`)
- **Documentation**: `docs/update-api-docs` (e.g., `docs/update-cli-reference`)

## Commit Conventions

Tux uses [Conventional Commits](https://conventionalcommits.org/) for consistent, machine-readable commit messages.

### Format

```text
<type>[scope]: <description>

[optional body]

[optional footer]
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

- **Lowercase type**: Always use lowercase (e.g., `feat`, not `Feat`)
- **Max 120 characters**: Keep subject line under 120 characters
- **No period at end**: Don't end subject with period
- **Start with lowercase**: Subject starts with lowercase letter
- **Use imperative mood**: Write as command (e.g., "add", not "added")

### Examples

```bash
feat: add user authentication system
fix: resolve memory leak in message handler
docs: update API documentation for new endpoints
refactor(database): optimize query performance
perf: improve caching strategy for user sessions
test: add integration tests for Discord commands
```

## Development Workflow

### 1. Setup

```bash
# Clone repository
git clone https://github.com/allthingslinux/tux.git
cd tux

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
cp config/config.toml.example config/config.toml
```

### 2. Development

```bash
# Create feature branch from main
git checkout main

# Organization members
git pull origin main

# External contributors
git pull upstream main

git checkout -b feature/your-feature-name

# Make changes in small, frequent commits
# ... edit code ...

# Run development checks frequently
uv run dev all

# Run tests after each logical change
uv run test quick

# Push branch early and often
git push origin feature/your-feature-name
```

**Key Principles:**

- Keep branches short-lived (1-3 days maximum)
- Merge to main at least daily
- Use feature flags for incomplete work
- Ensure main stays deployable at all times

### 3. Database Changes

```bash
# Modify models
# ... edit database models ...

# Generate migration
uv run db new "add user preferences table"

# Apply migration
uv run db dev
```

### 4. Commit

```bash
# Run pre-commit checks
uv run dev pre-commit

# Run full test suite
uv run test all

# Commit with conventional format
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
- **Commit message validation**: commitlint enforces conventional commits

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

1. **Push your branch**: Push feature branch to remote
2. **Create PR**: Use GitHub interface or CLI
3. **Title format**: `[module/area] Brief description`
4. **Description**: Include context, changes, and testing notes

### PR Requirements

- [ ] All tests pass (`uv run test all`)
- [ ] Code quality checks pass (`uv run dev all`)
- [ ] Database migrations tested (`uv run db dev`)
- [ ] Documentation updated if needed
- [ ] Type hints complete and accurate
- [ ] Docstrings added for public APIs

### PR Title Examples

```text
[auth] Add OAuth2 login system
[database] Optimize user query performance
[ui] Improve embed styling for mobile
[docs] Update CLI command reference
```

## Code Review Guidelines

### Reviewer Checklist

#### Code Quality

- [ ] Code follows Python standards (PEP 8)
- [ ] Type hints are complete and accurate
- [ ] Functions are small and focused (single responsibility)
- [ ] Variables and functions have descriptive names
- [ ] No unused imports or variables

#### Architecture

- [ ] Changes follow existing patterns
- [ ] Database operations use proper transactions
- [ ] Error handling is appropriate
- [ ] Security considerations addressed

#### Testing

- [ ] Unit tests added for new functionality
- [ ] Integration tests added for complex features
- [ ] Edge cases covered
- [ ] Existing tests still pass

#### Documentation

- [ ] Public APIs have docstrings
- [ ] Complex logic is commented
- [ ] Documentation updated if needed

### Review Process

1. **Automated checks**: CI must pass all quality gates
2. **Initial review**: Focus on architecture and approach
3. **Detailed review**: Examine code line-by-line
4. **Testing review**: Verify test coverage and scenarios
5. **Approval**: Minimum one maintainer approval required

## Git Hygiene

### Commit History

```bash
# Write meaningful commit messages
git commit -m "feat: implement user role system

- Add role-based permissions
- Create role assignment commands
- Update permission checks in modules"

# Avoid generic messages
❌ git commit -m "fix bug"
❌ git commit -m "update"
✅ git commit -m "fix: resolve null pointer in user lookup"
```

### Rebasing

```bash
# Keep branch up to date with main
git checkout feature/your-branch

# For organization members
git fetch origin
git rebase origin/main

# For external contributors
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

- Before creating a pull request
- When main has moved significantly ahead
- To keep your branch current with latest changes

**Avoid rebasing public branches that others are working on.**

### Stashing

```bash
# Save work in progress
git stash push -m "wip: user auth"

# Apply saved work
git stash pop
```

### Undoing Changes

```bash
# Undo uncommitted changes
git checkout -- file.py

# Undo last commit (keeping changes)
git reset --soft HEAD~1

# Undo last commit (discarding changes)
git reset --hard HEAD~1
```

## Troubleshooting

### Common Issues

#### Pre-commit hooks fail

```bash
# Run hooks manually to see issues
uv run dev lint
uv run dev type-check

# Fix formatting issues
uv run dev format
```

#### Merge conflicts

```bash
# Abort merge and start fresh
git merge --abort

# Use mergetool
git mergetool

# After resolving, complete merge
git commit
```

#### Lost commits

```bash
# Find lost commits
git reflog

# Restore from reflog
git checkout <commit-hash>
```

### Getting Help

- Check existing PRs for patterns
- Review commit history for examples
- Ask in our [Discord server](https://discord.gg/gpmSjcjQxg)
- Check documentation for specific workflows

## Resources

- [Conventional Commits](https://conventionalcommits.org/)
- [Git Documentation](https://git-scm.com/doc)
- [Pre-commit Documentation](https://pre-commit.com/)
- [Trunk-Based Development](https://trunkbaseddevelopment.com/)
