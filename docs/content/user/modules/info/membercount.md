---
title: Membercount
description: View comprehensive member statistics for the server
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - info
  - guild
---

# Membercount

The `membercount` command provides a quick and informative breakdown of the current server population. It allows users and administrators to instantly see how many human users versus automated bots are in the server, providing a clear picture of the community's size and composition.

## Syntax

The `membercount` command can be used in two ways:

**Slash Command:**

```text
/membercount
```

**Prefix Command:**

```text
$membercount
$mc
$members
```

**Aliases:**

You can also use these aliases instead of `membercount`:

- `mc`
- `members`

## Usage Examples

### View Global Stats

Display the total, human, and bot counts for the current server.

```text
/membercount
```

## Response

When executed, the bot displays an informational embed with three main fields:

- **Members:** The total number of accounts in the guild.
- **Humans:** The number of unique human users in the guild.
- **Bots:** The number of automated bot accounts in the guild.

## Permissions

### Bot Permissions

Tux requires the following permissions to execute this command:

- **Embed Links** - To display the counts in a neat format.

### User Permissions

This command is available to all users.

## Related Commands

- [`/info`](info.md) - For detailed information about the server or specific members.
