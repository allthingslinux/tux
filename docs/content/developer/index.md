---
title: Developer Guide
icon: material/folder-search-outline
description: Index of developer documentation—contributing, tutorials, concepts, best practices, and reference.
tags:
  - developer-guide
---

# Developer Guide

Documentation for developing and contributing to Tux: setup, architecture, patterns, and tooling.

---

## Contributing

**[Contributing to Tux](contributing.md)** — Setup, workflow, pull requests, and where to find Git, branch naming, and code review guidance.

---

## Tutorials

**[Tutorials](tutorials/index.md)** — Step-by-step guides:

| Topic | Description |
|-------|-------------|
| [Development Setup](tutorials/development-setup.md) | Environment and first run |
| [First Contribution](tutorials/first-contribution.md) | End-to-end first PR |
| [Creating Your First Cog](tutorials/creating-first-cog.md) | Module and cog structure |
| [Creating Your First Command](tutorials/creating-first-command.md) | Commands and invocation |
| [Creating Your First Migration](tutorials/creating-first-migration.md) | Database schema changes |
| [Database Integration](tutorials/database-integration.md) | Using the database in code |
| [Project Structure](tutorials/project-structure.md) | Layout and conventions |
| [Testing Setup](tutorials/testing-setup.md) | Running and writing tests |

---

## Guides

**[Guides](guides/index.md)** — How-to and tooling:

| Topic | Description |
|-------|-------------|
| [Components V2](guides/components-v2.md) | Discord.py Components V2 (buttons, views, modals) |
| [Creating Cursor Rules](guides/creating-cursor-rules.md) | Cursor rules for the project |
| [Creating Cursor Commands](guides/creating-cursor-commands.md) | Cursor slash commands |
| [Docker Images](guides/docker-images.md) | Building and using Docker images |
| [Extending the CLI](guides/extending-cli.md) | Adding CLI commands |

---

## Concepts

**[Concepts](concepts/index.md)** — Architecture and internals:

| Area | Contents |
|------|----------|
| [Core](concepts/core/index.md) | App, bot, cogs, lifecycle, modules, permissions, plugins, logging |
| [Database](concepts/database/index.md) | Architecture, service, models, controllers, migrations, testing, utilities |
| [UI](concepts/ui/index.md) | Buttons, components, embeds, modals, views |
| [Handlers](concepts/handlers/index.md) | Hot-reload and event handling |
| [Services](concepts/services/index.md) | Service layer |
| [Shared](concepts/shared/index.md) | Shared utilities and config |
| [Tasks](concepts/tasks/index.md) | Task monitor and background work |
| [Wrappers](concepts/wrappers/index.md) | Wrappers and helpers |

---

## Best Practices

**[Best Practices](best-practices/index.md)** — Conventions and patterns:

| Topic | Description |
|-------|-------------|
| [Git](best-practices/git.md) | Commits, rebasing, pre-commit, PRs |
| [Branch Naming](best-practices/branch-naming.md) | Branch name format and types |
| [Code Review](best-practices/code-review.md) | Review checklist and conduct |
| [CI/CD](best-practices/ci-cd.md) | Pipelines and automation |
| [Async](best-practices/async.md) | Async/await usage |
| [Error Handling](best-practices/error-handling.md) | Exceptions and recovery |
| [Logging](best-practices/logging.md) | Logging with loguru |
| [Caching](best-practices/caching.md) | Caching strategies |
| [Sentry](best-practices/sentry/index.md) | Instrumentation, sampling, metrics, spans |
| [Testing](best-practices/testing/index.md) | Unit, integration, e2e, fixtures |
| [Debugging](best-practices/debugging.md) | Debug workflow |
| [Documentation](best-practices/docs.md) | Doc and Zensical practices |
| [Namespace](best-practices/namespace.md) | Naming and structure |

---

## Reference

| Resource | Description |
|----------|-------------|
| [CLI](../reference/cli.md) | `tux`, `db`, `dev`, `test`, `config`, `docs` |
| [Environment Variables](../reference/env.md) | `.env` and configuration |
| [Versioning](../reference/versioning.md) | Versions and releases |
| [Renovate](../reference/renovate.md) | Dependency updates |
