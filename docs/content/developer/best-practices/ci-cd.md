---
title: CI/CD Best Practices
description: CI/CD best practices for Tux development, including pipeline architecture, change detection strategy, and quality assurance.
tags:
  - developer-guide
  - best-practices
  - ci-cd
---

# CI/CD Best Practices

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

## Overview

Tux uses GitHub Actions for a comprehensive CI/CD pipeline that ensures code quality, security, and reliable deployments. The pipeline includes:

- **Quality Gates**: Linting, type checking, formatting
- **Testing**: Unit, integration, and end-to-end tests with coverage
- **Security**: Vulnerability scanning, secret detection, dependency analysis
- **Containerization**: Docker builds with security scanning
- **Documentation**: Automated docs building and deployment
- **Releases**: Automated changelog generation and publishing

## Pipeline Architecture

### Change Detection Strategy

Tux uses intelligent change detection to run only necessary jobs, reducing CI time and costs:

```yaml
# File-based job triggering
jobs:
  changes:
    outputs:
      python: ${{ steps.python_changes.outputs.any_changed }}
      markdown: ${{ steps.markdown_changes.outputs.any_changed }}
      docker: ${{ steps.docker_changes.outputs.any_changed }}
```

**Benefits:**

- Faster feedback loops
- Reduced resource usage
- Targeted testing based on changes

### Concurrency Management

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

**Best Practices:**

- Cancel redundant runs on the same branch
- Prevent resource conflicts
- Allow workflow dispatch for manual triggers

## Quality Assurance

### Code Quality Checks

Tux runs comprehensive quality checks using multiple tools:

```yaml
# Quality gates with reviewdog integration
jobs:
  quality:
    steps:
      - name: Type Check
        uses: ./.github/actions/action-basedpyright
      - name: Lint
        run: uv run ruff check
      - name: Format
        run: uv run ruff format --check
```

**Tools Used:**

- **basedpyright**: Static type checking
- **ruff**: Fast Python linter and formatter
- **reviewdog**: GitHub-integrated reporting

### Testing Strategy

Tux implements a three-tier testing approach:

```yaml
# Comprehensive test coverage
jobs:
  unit:
    # Fast, isolated unit tests
  integration:
    # Database and service integration tests
  e2e:
    # Full system behavior tests
```

**Testing Principles:**

- **py-pglite** for self-contained database testing
- **80% coverage threshold** across all test types
- **Parallel execution** for faster feedback
- **Artifact storage** for coverage reports

### Custom Actions

Tux uses custom composite actions for consistency:

```yaml
# Python environment setup
- uses: ./.github/actions/setup-python
  with:
    python-version: ${{ env.PYTHON_VERSION }}
    enable-cache: true

# Test environment creation
- uses: ./.github/actions/create-test-env
  with:
    bot-token: test_token_for_ci
```

## Security Integration

### Multi-Layer Security

Tux implements security at multiple levels:

```yaml
# Security scanning jobs
jobs:
  codeql:
    # Static application security testing (SAST)
  dependencies:
    # Dependency vulnerability scanning
  python:
    # Python package security audit
```

**Security Tools:**

- **CodeQL**: GitHub's semantic code analysis
- **Docker Scout**: Container vulnerability scanning and policy evaluation
- **Safety**: Python dependency security
- **Gitleaks**: Secret detection

### Automated Security Gates

```yaml
# Security gates with appropriate permissions
permissions:
  security-events: write  # For CodeQL
  packages: read         # For dependency access
```

## Containerization Strategy

### Docker Build Pipeline

Tux uses advanced Docker workflows:

```yaml
# Multi-stage build with security scanning
jobs:
  build:
    steps:
      - name: Build & Push
        uses: docker/build-push-action@v6
        with:
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            VERSION=${{ steps.version.outputs.version }}
            GIT_SHA=${{ github.sha }}
```

**Docker Best Practices:**

- **Multi-stage builds** for smaller images
- **Build caching** with GitHub Actions cache
- **Security scanning** with Docker Scout (compare against production for PRs)
- **Metadata labeling** with OCI standards

### Registry Management

```yaml
# Automated cleanup
- name: Clean Old Images
  uses: actions/delete-package-versions@v5
  with:
    min-versions-to-keep: 15
    delete-only-untagged-versions: true
```

## Documentation Automation

### Zensical Pipeline

Tux automates documentation deployment:

```yaml
# Documentation build and validation
jobs:
  build:
    steps:
      - name: Build Documentation
        run: uv run zensical build --strict
      - name: Check Links
        run: npm install -g markdown-link-check
```

**Documentation Features:**

- **Cloudflare Workers** deployment
- **Link validation** to prevent broken references
- **Preview deployments** for pull requests
- **Strict mode** to catch errors

## Release Management

### Automated Releases

Tux uses semantic versioning with automated releases:

```yaml
# Release on tag push
on:
  push:
    tags: [v*]

jobs:
  create:
    steps:
      - name: Generate Changelog
        run: git log --pretty=format:"- %s" "${PREVIOUS_TAG}..HEAD"
      - name: Create Release
        uses: softprops/action-gh-release@v2
```

**Release Features:**

- **Conventional commits** for changelog generation
- **Semantic versioning** tags
- **Automated Docker publishing**
- **GitHub releases** with changelogs

## Performance Optimization

### Build Caching

```yaml
# Multi-layer caching strategy
- name: Setup Python
  uses: ./.github/actions/setup-python
  with:
    enable-cache: true

- name: Build
  uses: docker/build-push-action@v6
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### Parallel Execution

```yaml
# Matrix builds for multiple Python versions
strategy:
  matrix:
    python-version: [3.13.8]
  fail-fast: false
```

## Monitoring and Maintenance

### Automated Maintenance

Tux includes automated maintenance workflows:

```yaml
# Weekly and monthly maintenance
on:
  schedule:
    - cron: 0 2 * * 0  # Weekly
    - cron: 0 3 1 * *  # Monthly
```

**Maintenance Tasks:**

- **Registry cleanup** to manage storage costs
- **Repository health checks**
- **Dependency updates** via Renovate
- **TODO tracking** from code comments

### Health Monitoring

```yaml
# Comprehensive health checks
- name: Check Large Files
- name: Check Dependencies
- name: Check Repository Size
- name: Check Registry Health
```

## Workflow Best Practices

### Workflow Organization

```yaml
# Clear workflow naming and structure
name: CI  # Descriptive but concise
on:       # Clear trigger conditions
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:  # Prevent conflicts
  group: ${{ github.workflow }}-${{ github.ref }}
```

### Environment Variables

```yaml
# Centralized configuration
env:
  PYTHON_VERSION: 3.13.8
  COVERAGE_THRESHOLD: 80
  REVIEWDOG_LEVEL: warning
```

### Permissions Management

```yaml
# Minimal required permissions
permissions:
  contents: read
  pull-requests: write  # Only for reporting
```

## Troubleshooting

### Common Issues

#### Slow CI Runs

- **Check change detection** - ensure files are properly categorized
- **Review caching** - verify cache keys are working
- **Optimize test parallelization** - balance speed vs. resource usage

#### Failed Quality Gates

- **Review linter output** - check for false positives
- **Update dependencies** - ensure tools are current
- **Check configuration** - verify tool configs match project standards

#### Deployment Failures

- **Verify secrets** - ensure all required secrets are set
- **Check environment URLs** - validate deployment targets
- **Review permissions** - ensure proper access levels

## Development Workflow

### Local Testing

```bash
# Test CI locally
uv run test quick           # Fast local testing
uv run dev all             # Full quality checks
docker compose build .     # Test Docker builds
```

### Testing with Act

[Act](https://github.com/nektos/act) allows you to run GitHub Actions workflows locally using Docker. This provides fast feedback without committing and pushing changes.

**Installation:**

```bash
# Via script (recommended)
curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Via package manager
# Arch Linux
pacman -S act
# Ubuntu/Debian
# Add COPR repo or manual download
# macOS
brew install act
```

**Prerequisites:**

- Docker Engine (act uses Docker API to run containers)
- GitHub CLI (optional, for automatic token handling)

**Basic Usage:**

```bash
# Run all workflows triggered by push event (default)
act

# Run workflows for pull request event
act pull_request

# Run specific workflow
act -W .github/workflows/ci.yml

# Run specific job
act -j unit

# List available workflows for an event
act -l pull_request
```

**Common Tux Scenarios:**

```bash
# Test CI workflow (quality checks, linting, type checking)
act -j quality

# Test testing workflows (unit, integration, E2E)
act -j unit
act -j integration
act -j e2e

# Test Docker workflow
act -W .github/workflows/docker.yml

# Test docs workflow
act -W .github/workflows/docs.yml
```

**Handling Secrets and Environment:**

```bash
# Use GitHub CLI for automatic token (recommended)
act -s GITHUB_TOKEN="$(gh auth token)"

# Or provide manually (secure input)
act -s GITHUB_TOKEN

# Skip jobs that require sensitive operations
act -e event.json  # Where event.json contains {"act": true}
```

**Event Simulation:**

Create event files to simulate different triggers:

```json
// pull_request.json - Simulate pull request
{
  "pull_request": {
    "head": {
      "ref": "feature/my-feature"
    },
    "base": {
      "ref": "main"
    }
  }
}

// push.json - Simulate push with tag
{
  "ref": "refs/tags/v1.0.0"
}
```

**Workflow Configuration:**

Skip local-only steps in production:

```yaml
- name: Deploy to production
  if: ${{ !env.ACT }}  # Skip when running with act
  run: deploy-production.sh

# Or use custom event property
- name: Deploy to production
  if: ${{ !github.event.act }}  # Skip when act: true in event
  run: deploy-production.sh
```

**Performance Tips:**

```bash
# Enable offline mode (use cached actions/images)
act --action-offline-mode

# Use specific container architecture
act --container-architecture linux/amd64

# Enable artifact server for upload/download actions
act --artifact-server-path $PWD/.artifacts
```

**Troubleshooting:**

```bash
# Enable verbose logging
act -v

# Check Docker is running
docker info

# Clean up containers after failed runs
docker system prune -f

# Update act to latest version
act --version
# If outdated: curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

**Best Practices:**

- **Use act for fast feedback** before pushing changes
- **Test workflow changes locally** before committing
- **Skip sensitive operations** with `!env.ACT` conditions
- **Keep event files** for common scenarios (PR, push, release)
- **Use offline mode** for faster subsequent runs
- **Clean up artifacts** periodically to save disk space

### Pre-commit Quality

```bash
# Ensure quality before pushing
uv run dev pre-commit      # Run all pre-commit checks
uv run test all           # Full test suite
```

## Contributing to CI/CD

### Adding New Checks

1. **Create workflow step** with appropriate conditions
2. **Add to change detection** if file-based
3. **Set proper permissions** for the job
4. **Test locally first** before committing

### Creating Custom Actions

```yaml
# Create reusable actions for common patterns
runs:
  using: composite
  steps:
    - name: Setup
      shell: bash
      run: # Setup logic
```

### Security Considerations

- **Never expose secrets** in workflow logs
- **Use read-only tokens** where possible
- **Audit third-party actions** before use
- **Regular security updates** for all dependencies

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Security Hardening for Actions](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Trunk-Based Development](https://trunkbaseddevelopment.com/)
