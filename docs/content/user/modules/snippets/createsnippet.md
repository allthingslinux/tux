---
title: Createsnippet
description: Create new snippets or aliases
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - snippets
---

# Createsnippet

The `createsnippet` command allows users to add new reusable content to the server's snippet library. You can create a direct snippet by providing a name and content, or you can create an **alias** by providing the name of an existing snippet as the content.

## Syntax

The `createsnippet` command is available as a prefix command:

**Prefix Command:**

```text
$createsnippet <name> <content>
```

**Aliases:**

- `cs`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | STRING | Yes | The desired name for the snippet (Alphanumeric and dashes). |
| `content` | STRING | Yes | The text/code to save, or the name of an existing snippet to create an alias. |

## Usage Examples

### Create a New Snippet

Save a text response for quick use.

```text
$createsnippet hello Hello! Welcome to our server's community.
```

### Create a Code Snippet

Save a block of code with markdown formatting.

```text
$createsnippet example ```python\nprint('Hello World')\n```
```

### Create an Alias

Create a shortcut `h` for the `hello` snippet.

```text
$createsnippet h hello
```

## Constraints

- **Names:** Must be alphanumeric (can include dashes) and follow the server's length limits.
- **Uniqueness:** Snippet names must be unique within the server.
- **Duplicates:** If the `content` matches an existing snippet's name, an alias is automatically created.

## Error Handling

### Error: Name Already Exists

**When it occurs:** If you try to create a snippet with a name that is already in use.

**Error message:**

```text
Snippet with this name already exists.
```

## Related Commands

- [`$snippet`](snippet.md) - Retrieve and use your newly created snippet.
- [`$editsnippet`](editsnippet.md) - Modify an existing snippet's content.
