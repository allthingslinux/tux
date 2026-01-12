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
$si <name>
```

**Aliases:**

You can also use these aliases instead of `snippetinfo`:

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

## Response Format

When executed, Tux returns a rich info embed containing:

- **Snippet name** - The unique identifier displayed in the title
- **Creator** - The user who first created the snippet (shown as a mention, or ID if user not found)
- **Created at** - The date and time the snippet was added (formatted as Discord timestamp)
- **Uses** - Total number of times this snippet has been called (includes uses through aliases)
- **Lock status** - Whether the snippet is locked (restricts edits to moderators only)
- **Content/Alias** - Shows the snippet content (truncated if long) or indicates if it's an alias pointing to another snippet
- **Aliases** - Lists any aliases that point to this snippet (if viewing a target snippet, not an alias)

## Related Commands

- [`$snippet`](snippet.md) - View the full content of the snippet
- [`$snippets`](snippets.md) - See a summary of all snippets
- [`$editsnippet`](editsnippet.md) - Modify the snippet if you have permission
