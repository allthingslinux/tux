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
- **Quality Assurance**: All PRs must pass CI checks before auto-merge, waits 7 days after release for stability, uses semantic commits, and includes changelogs in PR descriptions

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
        ":separateMultipleMajorReleases",
        "customManagers:githubActionsVersions",
        "security:openssf-scorecard"
    ],
    "schedule": ["before 4am on Monday"],
    "timezone": "America/New_York",
    "dependencyDashboard": true,
    "dependencyDashboardOSVVulnerabilitySummary": "unresolved",
    "platformAutomerge": true,
    "rebaseWhen": "conflicted",
    "semanticCommitScope": "deps",
    "nix": {
        "enabled": true
    }
}
```

**Presets Explained**:

- **`config:best-practices`**: Includes recommended settings, Docker digest pinning, GitHub Actions digest pinning, config migration, dev dependency pinning, and abandonment detection
- **`:semanticCommits`**: Uses conventional commits format (`chore(deps): update ...`)
- **`:separateMultipleMajorReleases`**: Separates sequential major versions (v1→v2, v2→v3 as separate PRs)
- **`customManagers:githubActionsVersions`**: Detects and updates `_VERSION` environment variables in GitHub Actions workflows
- **`security:openssf-scorecard`**: Adds OpenSSF security score badges to PRs for GitHub-hosted packages

**Key Settings**:

- Runs weekly on Monday mornings before 4am ET
- Uses America/New_York timezone for scheduling
- Dependency dashboard shows unresolved OSV vulnerabilities
- Nix flake support explicitly enabled (beta feature)

### Enabled Managers

Renovate monitors these file types:

| Manager | Files Monitored | Purpose |
|---------|----------------|---------|
| `github-actions` | `.github/workflows/*.yml` | GitHub Actions workflow dependencies |
| `pep621` | `pyproject.toml`, `uv.lock` | Python dependencies and lock file |
| `docker-compose` | `compose.yaml` | Docker Compose service images |
| `dockerfile` | `Containerfile` | Dockerfile base images and dependencies |
| `custom.regex` | `.python-version` | Python version (via custom regex manager) |
| `devcontainer` | `.devcontainer/devcontainer.json` | Dev container images and features |
| `pre-commit` | `.pre-commit-config.yaml` | Pre-commit hook versions |
| `nix` | `flake.nix`, `flake.lock` | Nix flake inputs and lock file |

### PR Limits and Behavior

| Setting | Value | Description |
|---------|-------|-------------|
| `prConcurrentLimit` | `0` | No limit (unlimited open PRs) |
| `prHourlyLimit` | `0` | No limit (unlimited PRs per hour) |
| `prCreation` | `not-pending` | Creates PR when CI is not pending (waits up to 24h for status via `prNotPendingHours`) |
| `platformAutomerge` | `true` | Uses GitHub's native auto-merge |
| `rebaseWhen` | `conflicted` | Rebases PRs only when conflicted (more efficient) |
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

Renovate detects security updates via OSV, labels them with `deps: security`, and requires manual review (no auto-merge).

### Update Strategy

| Setting | Value | Description |
|---------|-------|-------------|
| `separateMinorPatch` | `false` | Minor and patch updates are combined |
| `separateMajorMinor` | `true` | Major updates are separated |
| `updateNotScheduled` | `true` | Allows updates outside schedule for urgent fixes |
| `rangeStrategy` | `update-lockfile` | Updates lock file when version ranges change (pep621 only) |
| `constraints.python` | `>=3.13.2,<3.14` | Constrained to Python 3.13.x |
| `constraints.postgres` | `<=17` | PostgreSQL version constraint |

## Package Rules

### Update Type Rules

| Update Type | Grouping | Auto-merge | Release Age | Labels |
|-------------|----------|------------|-------------|--------|
| **Patch** | Grouped | ✅ Branch | 7 days | `deps: patch` |
| **Minor** | Grouped | ✅ Branch | 7 days | `deps: minor` |
| **Major** | Grouped | 🚩 Manual | — | `deps: major`, `deps: needs-review`, `breaking` |

**Notes**: Minor updates exclude `0.x.x` versions (unstable). Major updates require manual review and are marked with `breaking` label.

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
| **types** | `types-*`, `type-*`, `typing-*`, `@types/*`, `*-types`, `*-stub(s)` (e.g. `annotated-types`, `asyncpg-stubs`) | ✅ Branch | `deps: types` | Monthly |
| **actions** | All GitHub Actions | ✅ Branch | `deps: github-actions` | Weekly |
| **docker** | Docker Compose + Dockerfile dependencies | ✅ Branch | `deps: docker` | Weekly |
| **python runtime** | `requires-python` (pep621), `.python-version`, workflows, Dockerfile | See below | `deps: python` | Weekly |
| **nix** | All Nix flake inputs | ✅ Branch | `deps: nix` | Weekly |

### Critical Runtime Dependencies

These packages are critical to Tux's core functionality. Major version updates require manual review to ensure compatibility and test breaking changes. All critical packages are grouped together in PRs.

**Critical Packages**: `discord-py`, `sqlmodel`, `sqlalchemy`, `pydantic`, `pydantic-settings`, `alembic`, `alembic-postgresql-enum`, `alembic-utils`, `asyncpg`, `psycopg`

| Update Type | Auto-merge | Priority | Labels | Notes |
|-------------|------------|----------|--------|-------|
| **All** | Inherits from global rules | `10` | `deps: critical` | 7 day wait, grouped together |

Critical packages inherit behavior from global update type rules (patch/minor auto-merge, major needs review).

### Special Cases

| Package/Manager | Update Type | Auto-merge | Priority | Labels | Notes |
|----------------|-------------|------------|----------|--------|-------|
| `uv` | All | 🚩 Manual | `5` | `deps: docker`, `deps: needs-review` | Package manager, requires review |
| `zensical` | All | 🚩 Manual | — | `deps: docs`, `deps: needs-review` | Documentation tool, monthly schedule |
| **Python runtime** | Patch | ✅ Branch | `10` | `deps: python` | Auto-merge after 3 days |
| **Python runtime** | Minor/Major | 🚩 Manual | `10` | `deps: python`, `deps: needs-review`, `breaking` | Requires review |

**Python runtime**: Groups `requires-python` in `pyproject.toml` (pep621), `.python-version`, `PYTHON_VERSION` in workflows, and Dockerfile Python version. All update together in one PR.

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

Automatically maintains lock files weekly with auto-merge enabled:

- **`uv.lock`**: Python dependency lock file
- **`flake.lock`**: Nix flake lock file

Lock file maintenance creates a PR and auto-merges when CI passes.

## PR Configuration

```json5
{
    "fetchChangeLogs": "pr",
    "commitBodyTable": true,
    "prBodyColumns": [
        "Package",
        "Update",
        "Type",
        "Change",
        "Age",
        "Confidence",
        "References"
    ],
    "suppressNotifications": ["prIgnoreNotification"]
}
```

**PR Features**:

- **Changelogs**: Fetched and displayed in PR body
- **Commit Body Table**: Structured table in commit messages
- **Age Badge**: Shows how old the release is (🟢 >7 days, 🟡 3-7 days, 🔴 <3 days)
- **Confidence Badge**: Merge confidence score (🟢 High, 🟡 Medium, 🔴 Low)
- **Suppressed Notifications**: No notifications when PRs are ignored/closed

## Workflow

1. **Weekly Schedule**: Runs every Monday before 4am ET (most updates)
2. **Monthly Schedule**: Type stubs and documentation tools run on the first of the month at 4am ET
3. **PR Creation**: Creates PRs when CI is not pending (waits up to 24h for status)
4. **Branch Automerge**: Auto-merges PRs when CI passes (no human review needed)
5. **PR Automerge**: PRs are created for all updates; branch automerge merges them when CI passes
6. **Manual Review**: Major updates, Python minor/major, uv, and Zensical require manual review
7. **Grouping**: Related dependencies grouped to reduce noise
8. **Stability Waiting**: Waits 7 days after release before automerging (3 days for Python patches)
9. **Digest Pinning**: All Docker images and GitHub Actions pinned to commit digests for security
10. **Breaking Labels**: All major updates automatically labeled as `breaking`

## PR Examples

### Critical Dependencies (Major)

- **Title**: `chore(deps): update critical`
- **Labels**: `deps: critical`, `deps: needs-review`
- **Behavior**: All critical packages grouped together, requires manual review

### Critical Dependencies (Minor/Patch)

- **Title**: `chore(deps): update critical`
- **Labels**: `deps: critical`
- **Behavior**: All critical packages grouped together, auto-merged after 7 days

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

### Nix Flake Inputs

- **Title**: `chore(deps): update nix`
- **Labels**: `deps: nix`
- **Behavior**: All Nix flake inputs grouped together, auto-merged

### Lock File Updates

- **Title**: `chore(deps): lock file maintenance`
- **Labels**: None (default)
- **Behavior**: Updates `uv.lock` and `flake.lock`, auto-merged, weekly schedule

## PR Labels

| Label | Description |
|-------|-------------|
| `deps: patch` | Patch updates (grouped) |
| `deps: minor` | Minor updates (grouped) |
| `deps: major` | Major updates (grouped) |
| `breaking` | Major version updates (potentially breaking changes) |
| `deps: security` | Security/vulnerability updates |
| `deps: critical` | Critical runtime dependencies (discord-py, sqlmodel, pydantic, etc.) |
| `deps: dev` | Development dependencies (ruff, basedpyright, yamllint, etc.) |
| `deps: test` | Test dependencies (pytest, pytest-*, py-pglite) |
| `deps: docs` | Documentation dependencies (zensical) |
| `deps: types` | Type stubs (types-*, annotated-types, asyncpg-stubs) |
| `deps: github-actions` | GitHub Actions updates |
| `deps: docker` | Docker-related updates (images, compose, containers) |
| `deps: python` | Python version updates (.python-version, workflows, Dockerfile) |
| `deps: nix` | Nix flake inputs |
| `deps: needs-review` | Requires manual review before merging |

## Security Features

Tux's Renovate configuration includes comprehensive security measures:

### Vulnerability Detection

- **GitHub Vulnerability Alerts**: Native GitHub security advisories
- **OSV Vulnerability Alerts**: Open Source Vulnerabilities database (broader coverage)
- **Dashboard Summary**: Unresolved vulnerabilities shown in dependency dashboard
- **Security Labels**: All vulnerability PRs labeled with `deps: security`
- **Manual Review**: Security updates never auto-merge (always require review)

### Digest Pinning

- **Docker Images**: All Docker images pinned to SHA256 digests (prevents tag hijacking)
- **GitHub Actions**: All actions pinned to commit SHA digests (prevents supply chain attacks)
- **Automatic Updates**: Digests updated when tags change

### Release Stability

- **7-Day Minimum Age**: Waits 7 days before automerging updates (lets community find issues)
- **Python Patch**: 3-day minimum for Python patch updates (faster security fixes)
- **Abandonment Detection**: Warns when packages haven't released in 1 year
- **OpenSSF Scorecard**: Shows security scores for GitHub-hosted packages

### Example Pinned Dependencies

**Before Renovate:**

```yaml
image: postgres:17-alpine
uses: actions/checkout@v5
```

**After Renovate:**

```yaml
image: postgres:17-alpine@sha256:abc123...
uses: actions/checkout@abc123def456...abc123def456 # v5
```

## Monitoring

The dependency dashboard issue provides:

- Overview of all pending updates
- Unresolved OSV vulnerabilities
- Update status and approval workflow
- Links to open PRs
- Ability to request immediate updates (bypassing schedule)

## Related Documentation

- **[SBOM](./sbom.md)** - Software Bill of Materials with all dependencies
- **[Versioning](./versioning.md)** - Version management and semantic versioning

## Noise Reduction Strategy

Tux's configuration implements advanced noise reduction:

### Branch automerge (no human review)

These updates create PRs that are auto-merged when CI passes:

- ✅ Patch updates (after 7 days)
- ✅ Minor updates (after 7 days)
- ✅ Critical packages (after 7 days, inherits patch/minor behavior)
- ✅ Python patch updates (after 3 days)
- ✅ Dev tools
- ✅ Test dependencies
- ✅ Type stubs (monthly)
- ✅ GitHub Actions
- ✅ Docker images
- ✅ Nix inputs
- ✅ Lock file maintenance

**Result**: PRs are created for all updates; they are auto-merged when CI passes. You only need to review PRs that require manual review or when CI fails.

### Rate limiting

- **No PR limit** (`prConcurrentLimit: 0`, `prHourlyLimit: 0`): Unlimited concurrent and hourly PRs
- **PR creation**: PRs created when CI is not pending (waits up to 24h for status)

### Smart scheduling

- **Weekly**: Most updates (Monday 4am ET, outside work hours)
- **Monthly**: Low-priority updates (types, docs - 1st of month, 4am ET)
- **Urgent**: Security updates bypass schedule

### Expected weekly noise

- **Best case**: Most PRs auto-merge when CI passes; few need human review
- **Typical case**: 1-2 PRs require manual review (major updates, uv, zensical)
- **Worst case**: Many PRs when many major updates or failing CI need attention

## Advanced Features

### Custom Version Detection

Renovate detects and updates version variables in GitHub Actions workflows:

```yaml
env:
  # renovate: datasource=python-version depName=python
  PYTHON_VERSION: 3.13.8
```

**Custom Manager for `.python-version`**:

Renovate also tracks the `.python-version` file using a custom regex manager:

```json5
{
    "customType": "regex",
    "managerFilePatterns": ["/^\\.python-version$/"],
    "matchStrings": ["(?<currentValue>\\d+\\.\\d+\\.\\d+)"],
    "datasourceTemplate": "python-version",
    "depNameTemplate": "python",
    "versioningTemplate": "pep440"
}
```

This ensures `requires-python` (pep621), `.python-version`, `PYTHON_VERSION` in workflows, and Dockerfile Python versions all update together in one PR.

### Automated Fixes

Includes community-sourced workarounds for known package issues:

- Alpine edge build prevention
- Docker versioning quirks
- Package-specific compatibility handling

## Resources

- **[Renovate Documentation](https://docs.renovatebot.com/)** - Official Renovate documentation
- **[Renovate Presets](https://docs.renovatebot.com/presets-config/)** - Available configuration presets
- **[Renovate GitHub App](https://github.com/apps/renovate)** - Install Renovate GitHub App
- **[OpenSSF Scorecard](https://securityscorecards.dev/)** - Security scorecard information
- **[OSV Database](https://osv.dev/)** - Open Source Vulnerabilities database
