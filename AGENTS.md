# AGENTS.md

**Tux** is an all-in-one open source Discord bot for the [All Things Linux](https://allthingslinux.org) community.

**Stack:** Python 3.13.2+ • discord.py • PostgreSQL • SQLModel • uv • Docker

## Quick reference

| Task | Command |
|------|---------|
| Install deps | `uv sync` |
| Config examples | `uv run config generate` |
| DB + migrate | `uv run db init` / `uv run db dev` |
| Quality | `uv run dev all` |
| Tests | `uv run test quick` / `uv run test all` |
| Run bot | `uv run tux start` |
| Validate Cursor content | `uv run ai validate-rules` |

## Cursor rules and commands

Project standards live in `.cursor/rules/*.mdc` and workflows in `.cursor/commands/`.

- **Catalog:** [.cursor/rules/rules.mdc](.cursor/rules/rules.mdc)
- **Overview:** [.cursor/README.md](.cursor/README.md)

```bash
uv run ai validate-rules
```

**Docs:** [Creating Cursor Rules](docs/content/developer/guides/creating-cursor-rules.md) · [Creating Cursor Commands](docs/content/developer/guides/creating-cursor-commands.md)

> Domain-specific detail (database, testing, modules, security, docs) is in `.cursor/rules/`, not repeated here.

## Detailed instructions

| Topic | File |
|-------|------|
| Setup and repository layout | [.agents/setup.md](.agents/setup.md) |
| CLI commands (dev, test, db, docs, troubleshooting) | [.agents/commands.md](.agents/commands.md) |
| Workflow, Docker Compose, commits, PRs | [.agents/workflow.md](.agents/workflow.md) |
| Standards summary, patterns, cache, security | [.agents/patterns.md](.agents/patterns.md) |

## Resources

- **Docs:** <https://tux.atl.dev>
- **Issues:** <https://github.com/allthingslinux/tux/issues>
- **Discord:** <https://discord.gg/gpmSjcjQxg>
- **Repo:** <https://github.com/allthingslinux/tux>
