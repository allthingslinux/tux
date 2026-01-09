---
title: Tools
description: Useful tools and integrations for enhanced functionality
tags:
  - user-guide
  - modules
  - tools
icon: lucide/wrench
---

# Tools

The Tools module provides specialized utility commands that integrate with external services and provide advanced functionality. These tools extend Tux's capabilities with features like documentation lookup and computational queries.

By offering powerful integrations, this module enhances your server's capabilities. From quick documentation lookups via TLDR pages to complex computational queries using Wolfram Alpha, these tools provide access to world-class resources directly from your Discord interface.

## Commands

| Command | Description | Documentation |
|---------|-------------|---------------|
| `/tldr` | Quick documentation lookup | [Details](tldr.md) |
| `/wolfram` | Query Wolfram Alpha | [Details](wolfram.md) |

## Common Use Cases

### Documentation Lookup

Quickly find documentation for programming languages, Linux commands, and developer tools using TLDR pages.

**Steps:**

1. Use the `/tldr` command with a command name (e.g., `git commit`).
2. Tux will fetch the most relevant documentation and display it in an easy-to-read format.

**Example:**

```text
/tldr command:git-commit
/tldr command:python-list
```

### Computational Queries

Get answers to complex computational questions, unit conversions, and mathematical plots using Wolfram Alpha.

**Steps:**

1. Use the `/wolfram` command followed by your query.
2. Review the detailed results and data visualizations provided.

**Example:**

```text
/wolfram query:"What is 2+2?"
/wolfram query:"plot sin(x)"
```

## Permissions

### Bot Permissions

Tux requires the following permissions for this module:

- **Send Messages** - Required for command responses
- **Embed Links** - Required for detailed rich results and visualizations

### User Permissions

Tool commands are available to all users by default.

!!! tip "Permission System"
    Tux uses a dynamic permission system. Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Related Documentation

- [Permission Configuration](../../../admin/config/commands.md)
- [Admin Configuration Guide](../../../admin/config/index.md)
