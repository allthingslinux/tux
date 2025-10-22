# Contributing to Tux

Help improve Tux! Contributions welcome.

## Ways to Contribute

### Code

- Fix bugs
- Add features
- Improve performance
- Write tests

### Documentation

- Fix typos/errors
- Add examples
- Clarify explanations
- Write guides

### Testing

- Report bugs
- Test new features
- Provide feedback

### Design

- Improve UI/UX
- Create assets
- Suggest improvements

## Getting Started

### Development Setup

See [Development Setup](../developer-guide/getting-started/development-setup.md).

### First Contribution

See [First Contribution Guide](../developer-guide/getting-started/first-contribution.md).

## Development Workflow

### 1. Fork and Clone

```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/tux
cd tux
```

### 2. Create Branch

```bash
git checkout -b feature/my-feature
```

**Branch prefixes:**

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Refactoring
- `test/` - Tests

### 3. Make Changes

```bash
# Install dependencies
uv sync

# Make changes...

# Run checks
uv run dev all                      # Lint, type check, test
```

### 4. Commit

Use conventional commits:

```bash
git commit -m "feat: add new command"
git commit -m "fix: resolve database issue"
git commit -m "docs: update installation guide"
```

**Types:** feat, fix, docs, refactor, test, chore

### 5. Push and Create PR

```bash
git push origin feature/my-feature
```

Open Pull Request on GitHub.

## Code Standards

### Style

- **Ruff** for linting
- **Basedpyright** for type checking
- **Numpy docstrings**
- Type hints required

```bash
# Check style
uv run dev lint
uv run dev format

# Type check
uv run dev typecheck
```

### Testing

```bash
# Run tests
uv run tests all

# With coverage
uv run tests coverage
```

## Pull Request Guidelines

### PR Title

Use conventional commits format:

```
feat: add new moderation command
fix: resolve permission check issue
docs: update deployment guide
```

### PR Description

Include:

- What changed
- Why (issue link if applicable)
- How to test
- Screenshots (if UI changes)

### Checklist

- [ ] Tests pass
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] Changelog updated (if needed)

## Code Review

- Be patient and respectful
- Respond to feedback
- Make requested changes
- Ask questions if unclear

## Community

- **Discord:** [discord.gg/gpmSjcjQxg](https://discord.gg/gpmSjcjQxg)
- **GitHub:** [github.com/allthingslinux/tux](https://github.com/allthingslinux/tux)

## License

Contributions are licensed under GPL-3.0.

---

**Thank you for contributing!** 🎉
