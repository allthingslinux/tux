---
title: Renovate Configuration
tags:
  - renovate
  - dependencies
  - ci-cd
---

# Renovate Configuration

Renovate is an automated dependency update tool that helps keep Tux's dependencies up-to-date, secure, and maintainable. This document explains Renovate's purpose and documents Tux's actual configuration.

## What is Renovate?

Renovate automatically scans dependencies in `pyproject.toml`, `uv.lock`, Dockerfiles, GitHub Actions, and other files, monitors package registries for updates, and creates pull requests. It groups related updates together and can automatically merge PRs that pass CI checks.

## Purpose in Tux

Renovate helps maintain Tux by:

- **Security Updates**: Automatically detects OSV vulnerabilities, labels security PRs, and shows unresolved vulnerabilities in the dependency dashboard
- **Dependency Maintenance**: Keeps dependencies current with weekly scheduled updates, grouped PRs to reduce noise, and automatic lock file maintenance
- **Quality Assurance**: All PRs must pass CI checks before auto-merge, waits 14 days after release for stability, uses semantic commits, and includes changelogs in PR descriptions

## Configuration File

The Renovate configuration is located at `.github/renovate.json5` and uses JSON5 format (allowing comments).

## Base Configuration

### Presets and Core Settings

```json5
{
    "$schema": "https://docs.renovatebot.com/renovate-schema.json",
    "extends": [
        "config:best-practices",
        ":semanticCommits",
        ":separateMultipleMajorReleases"
    ],
    "schedule": ["before 4am on Monday"],
    "timezone": "America/New_York",
    "dependencyDashboard": true,
    "dependencyDashboardOSVVulnerabilitySummary": "unresolved"
}
```

**Key Settings**:

- Uses Renovate's best practices preset with semantic commits
- Separates multiple major releases into individual PRs
- Runs weekly on Monday mornings before 4am ET
- Dependency dashboard shows unresolved OSV vulnerabilities

### Enabled Managers

Renovate monitors: `github-actions`, `pep621` (Python dependencies), `docker-compose`, `dockerfile`, `custom.regex`, `devcontainer`, `pre-commit`, and `nix` files.

### PR Limits and Behavior

| Setting | Value | Description |
|---------|-------|-------------|
| `prConcurrentLimit` | `3` | Maximum open PRs at once |
| `prHourlyLimit` | `2` | Maximum PRs created per hour |
| `prCreation` | `not-pending` | Waits 24 hours after CI completes before creating PR |
| `platformAutomerge` | `true` | Uses GitHub's native auto-merge |
| `rebaseWhen` | `auto` | Automatically rebases PRs when base branch updates |
| `recreateWhen` | `auto` | Recreates PRs when needed |

### Vulnerability Alerts

```json5
{
    "osvVulnerabilityAlerts": true,
    "vulnerabilityAlerts": {
        "enabled": true,
        "labels": ["deps: security"],
        "automerge": false
    }
}
```

Security updates are detected via OSV, labeled with `deps: security`, and require manual review (no auto-merge).

### Update Strategy

| Setting | Value | Description |
|---------|-------|-------------|
| `separateMinorPatch` | `false` | Minor and patch updates are combined |
| `separateMajorMinor` | `true` | Major updates are separated |
| `updateNotScheduled` | `true` | Allows updates outside schedule for urgent fixes |
| `rangeStrategy` | `update-lockfile` | Updates lock file when version ranges change |
| `constraints.python` | `>=3.13.2,<3.14` | Constrained to Python 3.13.x |

## Package Rules

### Update Type Rules

| Update Type | Grouping | Auto-merge | Release Age | Labels |
|-------------|----------|------------|-------------|--------|
| **Patch** | Grouped | ✅ Branch | 14 days | `deps: patch` |
| **Minor** | Grouped | ✅ Branch | 14 days | `deps: minor` |
| **Major** | Grouped | 🚩 Manual | — | `deps: major`, `deps: needs-review` |

**Notes**: Minor updates exclude `0.x.x` versions (unstable). Major updates require manual review.

### Dependency Group Rules

| Group | Auto-merge | Priority | Labels | Schedule |
|-------|------------|----------|--------|----------|
| `dev` | ✅ Branch | `-1` | `deps: dev` | Weekly |
| `test` | ✅ Branch | `-1` | `deps: test` | Weekly |
| `docs` | 🚩 Manual | — | `deps: docs`, `deps: needs-review` | Monthly |
| `types` | ✅ Branch | `-2` | `deps: types` | Monthly |

### Specific Package Groups

| Group Name | Packages | Auto-merge | Labels | Schedule |
|------------|----------|------------|--------|----------|
| **dev** | `pre-commit`, `ruff`, `basedpyright`, `yamllint`, `yamlfix`, `pydoclint`, `docstr-coverage`, `pydantic-settings-export` | ✅ Branch | `deps: dev` | Weekly |
| **test** | All packages in `test` dependency group (pytest, pytest-*, py-pglite) | ✅ Branch | `deps: test` | Weekly |
| **docs** | `zensical` | 🚩 Manual | `deps: docs`, `deps: needs-review` | Monthly |
| **types** | `/^types-/`, `annotated-types`, `asyncpg-stubs` | ✅ Branch | `deps: types` | Monthly |

### Critical Runtime Dependencies

These packages are critical to Tux's core functionality. Major version updates require manual review to ensure compatibility and test breaking changes. All critical packages are grouped together in PRs.

**Critical Packages**: `discord-py`, `sqlmodel`, `sqlalchemy`, `pydantic`, `pydantic-settings`, `alembic`, `alembic-postgresql-enum`, `alembic-utils`, `asyncpg`, `psycopg`

| Update Type | Auto-merge | Priority | Labels | Notes |
|-------------|------------|----------|--------|-------|
| **Major** | 🚩 Manual | `10` | `deps: critical`, `deps: needs-review` | All critical packages grouped together |
| **Minor/Patch** | ✅ Branch | `5` | `deps: critical` | 14 day wait, all critical packages grouped together |

### Special Cases

| Package/Manager | Update Type | Auto-merge | Priority | Labels | Notes |
|----------------|-------------|------------|----------|--------|-------|
| `basedpyright` | Minor/Patch | ✅ Branch | — | `deps: dev` | Pinned package (`==1.29.5`), individual PR |
| `zensical` | All | 🚩 Manual | — | `deps: docs`, `deps: needs-review` | Individual PR, monthly schedule |
| GitHub Actions | All | ✅ Branch | — | `deps: github-actions` | Grouped as "actions" |
| Docker Compose | All | ✅ Branch | — | `deps: docker` | Grouped as "docker-compose" |
| Dockerfile | All | ✅ Branch | — | `deps: docker` | Grouped as "dockerfile" |
| Python (Dockerfile) | Patch/Minor (`3.13.x`) | ✅ Branch | `5` | `deps: python`, `deps: docker` | Within version series |
| Python (Dockerfile) | Major | 🚩 Manual | `10` | `deps: python`, `deps: docker`, `deps: needs-review` | Individual PR |
| Python (Dockerfile) | Minor (outside `3.13.x`) | 🚩 Manual | `8` | `deps: python`, `deps: docker`, `deps: needs-review` | Individual PR |

### Lock File Maintenance

```json5
{
    "lockFileMaintenance": {
        "enabled": true,
        "automerge": true,
        "schedule": ["before 4am on Monday"]
    }
}
```

Automatically maintains `uv.lock` file weekly with auto-merge enabled.

## PR Configuration

```json5
{
    "fetchChangeLogs": "pr",
    "commitBodyTable": true,
    "prBodyColumns": ["Package", "Update", "Type", "Change", "References"],
    "suppressNotifications": ["prIgnoreNotification"]
}
```

PRs include changelogs, commit body tables, custom columns, and suppressed ignore notifications.

## Workflow

1. **Weekly Schedule**: Runs every Monday before 4am ET (most updates)
2. **Monthly Schedule**: Types and docs updates run on the first of the month at 4am ET
3. **PR Creation**: Creates PRs after CI checks complete (24 hour wait)
4. **Auto-merge**: Automatically merges PRs that pass CI (for enabled rules) using branch automerge
5. **Manual Review**: Major updates, critical dependencies, and zensical updates require manual review
6. **Grouping**: Related dependencies are grouped to reduce PR noise

## PR Examples

### Critical Dependencies (Major)

- **Title**: `chore(deps): update critical`
- **Labels**: `deps: critical`, `deps: needs-review`
- **Behavior**: All critical packages grouped together, requires manual review

### Critical Dependencies (Minor/Patch)

- **Title**: `chore(deps): update critical`
- **Labels**: `deps: critical`
- **Behavior**: All critical packages grouped together, auto-merged after 14 days

### General Updates

- **Title**: `chore(deps): update patch` / `chore(deps): update minor` / `chore(deps): update major`
- **Labels**: `deps: patch` / `deps: minor` / `deps: major` (+ `deps: needs-review` for major)
- **Behavior**: Grouped by update type, auto-merged for patch/minor, manual review for major

### Development Dependencies

- **Title**: `chore(deps): update dev`
- **Labels**: `deps: dev`
- **Behavior**: All dev tools grouped together, auto-merged

### Test Dependencies

- **Title**: `chore(deps): update test`
- **Labels**: `deps: test`
- **Behavior**: All test packages grouped together, auto-merged

### Documentation

- **Title**: `chore(deps): update docs`
- **Labels**: `deps: docs`, `deps: needs-review`
- **Behavior**: Individual PR for zensical, requires manual review, monthly schedule

### Type Stubs

- **Title**: `chore(deps): update types`
- **Labels**: `deps: types`
- **Behavior**: All type stubs grouped together, auto-merged, monthly schedule

## PR Labels

| Label | Description |
|-------|-------------|
| `deps: patch` | Patch updates |
| `deps: minor` | Minor updates |
| `deps: major` | Major updates |
| `deps: security` | Security updates |
| `deps: critical` | Critical runtime dependencies |
| `deps: dev` | Development dependencies |
| `deps: test` | Test dependencies |
| `deps: docs` | Documentation dependencies |
| `deps: types` | Type stubs |
| `deps: github-actions` | GitHub Actions updates |
| `deps: docker` | Docker-related updates |
| `deps: python` | Python version updates |
| `deps: needs-review` | Requires manual review |

## Monitoring

The dependency dashboard issue provides an overview of all dependencies, unresolved OSV vulnerabilities, update status, and links to open PRs.

## Related Documentation

- **[SBOM](./sbom.md)** - Software Bill of Materials with all dependencies
- **[Versioning](./versioning.md)** - Version management and semantic versioning

## Resources

- **[Renovate Documentation](https://docs.renovatebot.com/)** - Official Renovate documentation
- **[Renovate Presets](https://docs.renovatebot.com/presets-config/)** - Available configuration presets
- **[Renovate GitHub App](https://github.com/apps/renovate)** - Install Renovate GitHub App
