# Cursor Rules & Commands

The Tux project uses Cursor's rules and commands system to provide AI-assisted development with project-specific patterns and workflows.

## Overview

This directory contains:

- **Rules** (`.mdc` files) - Project-specific coding patterns and standards
- **Commands** (`.md` files) - Reusable workflows and task automation

Rules are automatically applied by Cursor based on file patterns, while commands are invoked manually with the `/` prefix in Cursor chat.

## Structure

### Rules

Rules are organized by domain in `.cursor/rules/`:

- **`core/`** - Core project rules (tech stack, dependencies)
- **`database/`** - Database layer patterns (models, migrations, controllers, services, queries)
- **`modules/`** - Discord bot modules (cogs, commands, events, permissions, interactions)
- **`testing/`** - Testing patterns (pytest, fixtures, markers, coverage, async)
- **`docs/`** - Documentation rules (Zensical, writing standards, structure)
- **`security/`** - Security patterns (secrets, validation, dependencies)
- **`error-handling/`** - Error handling (patterns, logging, Sentry, user feedback)
- **`ui/`** - UI components (Discord Components V2)
- **`meta/`** - System documentation (Cursor rules/commands specifications)

### Commands

Commands are organized by category in `.cursor/commands/`:

- **`code-quality/`** - Code quality workflows (lint, refactor, review)
- **`testing/`** - Testing workflows (run tests, coverage, integration)
- **`database/`** - Database workflows (migration, health, reset)
- **`discord/`** - Discord bot workflows (create module, test command, sync)
- **`security/`** - Security workflows (security review)
- **`debugging/`** - Debugging workflows (debug issues)
- **`error-handling/`** - Error handling workflows (add error handling)
- **`documentation/`** - Documentation workflows (generate, update, serve)
- **`development/`** - Development workflows (setup, docker)

## Usage

Rules are automatically applied by Cursor:

- **Always Apply** - Rules with `alwaysApply: true` are active in every chat
- **File-Scoped** - Rules with `globs` patterns apply when editing matching files
- **Intelligent** - Rules with `description` are selected by Cursor based on context

Commands are invoked manually:

1. Type `/` in Cursor chat
2. Select command from autocomplete list
3. Command executes with current context

Example: `/lint` runs the linting workflow

## Quick Reference

See [rules/rules.mdc](rules/rules.mdc) for a complete catalog of all rules and commands.

## Contributing

See the developer documentation for comprehensive guides on creating and maintaining rules/commands:

- [Creating Cursor Rules Guide](../docs/content/developer/guides/creating-cursor-rules.md)
- [Creating Cursor Commands Guide](../docs/content/developer/guides/creating-cursor-commands.md)

## Resources

- [Cursor Rules Documentation](https://cursor.com/docs/context/rules)
- [Cursor Commands Documentation](https://cursor.com/docs/agent/chat/commands)
- [AGENTS.md](../AGENTS.md)
