---
title: Snippetinfo
description: View metadata and statistics for a snippet
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - snippets
---

# Snippetinfo

The `snippetinfo` command provides detailed background information about a specific snippet. It's used to identify who created a snippet, how often it’s used, and its current configuration (such as whether it's an alias or if it’s locked).

## Syntax

The `snippetinfo` command is available as a prefix command:

**Prefix Command:**

```text
$snippetinfo <name>
```

**Aliases:**

- `si`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | STRING | Yes | The name of the snippet you want to inspect. |

## Usage Examples

### Inspect a Snippet

Get the statistics for the `guide` snippet.

```text
$snippetinfo guide
```

## Response

When executed, Tux returns a rich info embed containing:

- **Title:** The snippet name.
- **Creator:** The user who first created the snippet.
- **Created At:** The date and time the snippet was added.
- **Uses:** Total number of times this snippet (or an alias pointing to it) has been called.
- **Lock Status:** Whether the snippet is locked (Restricts edits to moderators).
- **Alias Status:** If it's an alias, it shows which target snippet it points to.

## Related Commands

- [`$snippet`](snippet.md) - View the content described in the info embed.
- [`$snippets`](snippets.md) - See a summary of all snippets.
