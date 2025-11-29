---
title: Branch Naming Conventions
tags:
  - developer-guide
  - best-practices
  - git
---

# Branch Naming Conventions

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

This document defines the official branch naming rules for this repository and explains why they exist.
Consistent naming across branches improves readability, traceability, and automation in CI/CD pipelines.
By following these rules, every developer can instantly recognize the purpose and context of a branch
without digging into commits or issues.

## Why It Matters

Clear branch names:

- Make it easy to identify what each branch does.
- Simplify issue tracking.
- Reduce merge confusion and human error.

## Format

Each branch name must follow this simple structure:

```text
<type>/[<issue-id>-]<short-description>
```

> The `<issue-id>` is **optional**, but encouraged when the branch relates to a tracked issue.

### Examples

```text
feat/1022-add-message-command
fix/245-handle-bot-crash
hotfix/312-fix-discord-api-error
chore/cleanup-bot-commands
docs/update-bot-readme
test/add-unit-tests-for-commands
ci/update-bot-deploy-script
release/v0.1.0
refactor/optimize-command-handler
deps/upgrade-discord-py-to-3.14
```

## Types

Allowed `<type>` values:

| Type         | Description                                    |
| ------------ | ---------------------------------------------- |
| **chore**    | Maintenance, cleanup, or configuration changes |
| **ci**       | CI/CD or build pipeline changes                |
| **deps**     | Dependency additions or updates                |
| **docs**     | Documentation updates                          |
| **feat**     | New feature or enhancement                     |
| **fix**      | Bug fix (non-critical)                         |
| **hotfix**   | Urgent production patch                        |
| **refactor** | Code restructuring without behavior change     |
| **release**  | Preparing or tagging a release                 |
| **test**     | Adding or modifying tests                      |

## Components

### `<issue-id>`

- Optional, but recommended whenever possible.
- Helps trace code changes back to specific issues or tasks.

### `<short-description>`

- Lowercase only
- Hyphen-separated words (`-`)
- Short and specific (\~50 characters max)
- Describe the change or purpose, not the implementation

## Complete Examples

```text
feat/1022-add-message-command
fix/245-handle-bot-crash
hotfix/312-fix-discord-api-error
chore/cleanup-bot-commands
docs/update-bot-readme
test/add-unit-tests-for-commands
ci/update-bot-deploy-script
release/v0.1.0
refactor/optimize-command-handler
deps/upgrade-discord-py-to-3.14
```

## Best Practices

- Keep branch names clear and descriptive — they should convey purpose at a glance, even before looking at commits.
