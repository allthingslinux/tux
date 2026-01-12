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
$cs <name> <content>
```

**Aliases:**

You can also use these aliases instead of `createsnippet`:

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

Save a block of code with Markdown formatting.

```text
$createsnippet example ```python\nprint('Hello World')\n```
```

### Create an Alias

Create a shortcut `h` for the `hello` snippet.

```text
$createsnippet h hello
```

## Constraints

- **Names:** Must be alphanumeric (can include dashes) and follow the server's length limits
- **Uniqueness:** Snippet names must be unique within the server
- **Alias creation:** If the `content` exactly matches an existing snippet's name, an alias pointing to that snippet is automatically created instead of a new snippet
- **Permissions:** Your ability to create snippets may be restricted based on server configuration (check with `$snippetinfo` or ask a moderator)

## Error Handling

### Name Already Exists

**When it occurs:** If you try to create a snippet with a name that is already in use.

**What happens:** The bot sends an error message indicating the name is taken.

**Solutions:**

- Choose a different name for your snippet
- Use `$snippets` to check existing snippet names
- If you own the existing snippet, use `$editsnippet` to modify it instead

## Related Commands

- [`$snippet`](snippet.md) - Retrieve and use your newly created snippet
- [`$editsnippet`](editsnippet.md) - Modify an existing snippet's content
- [`$snippets`](snippets.md) - Browse all snippets to check for name conflicts
