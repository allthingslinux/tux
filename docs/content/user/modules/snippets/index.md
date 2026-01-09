---
title: Snippets
description: Create and manage code snippets and aliases for quick access
tags:
  - user-guide
  - modules
  - snippets
icon: lucide/square-pen
---

# Snippets

The Snippets module allows you to create, manage, and use code snippets in your Discord server. Snippets are reusable pieces of text or code that can be quickly accessed by name, and you can create aliases to point to existing snippets.

Snippets are useful for storing frequently used code, text, or responses that you want to quickly access. You can create snippets with custom names, create aliases that point to existing snippets, and manage your snippet library.

Snippets are server-specific and can be locked by moderators to prevent unauthorized editing.

## Commands

| Command | Description | Documentation |
|---------|-------------|---------------|
| `$createsnippet` | Create a new snippet or alias | [Details](createsnippet.md) |
| `$snippet` | View and use a snippet | [Details](snippet.md) |
| `$snippets` | List all available snippets | [Details](snippets.md) |
| `$snippetinfo` | Get detailed information about a snippet | [Details](snippetinfo.md) |
| `$editsnippet` | Edit an existing snippet | [Details](editsnippet.md) |
| `$deletesnippet` | Delete a snippet | [Details](deletesnippet.md) |
| `$togglesnippetlock` | Lock or unlock a snippet | [Details](togglesnippetlock.md) |

**Aliases:**

- `$createsnippet` → `$cs`
- `$snippet` → `$s`
- `$snippets` → `$ls`
- `$snippetinfo` → `$si`
- `$editsnippet` → `$es`
- `$deletesnippet` → `$ds`
- `$togglesnippetlock` → `$tsl`

## Common Use Cases

### Creating Code Snippets

Store frequently used code blocks or canned responses for quick access.

**Steps:**

1. Use the `$createsnippet` command with a unique name and the content.
2. Access your snippet anytime using the `$snippet` command.

**Example:**

```text
$createsnippet python-example print('Hello, World!')
$snippet python-example
```

### Creating Aliases

Create shortcuts to existing snippets to make them easier to remember or faster to type.

**Steps:**

1. Use the `$createsnippet` command.
2. Provide a new name and the name of the existing snippet as the content.

**Example:**

```text
$createsnippet short-name python-example
```

### Managing Snippets

Organize, review, and protect your snippet library.

**Steps:**

1. List all snippets with `$snippets`.
2. Check metadata (creator, date, lock status) with `$snippetinfo`.
3. Protect important snippets using `$togglesnippetlock`.

**Example:**

```text
$snippets
$snippetinfo python-example
$togglesnippetlock python-example
```

## Permissions

### Bot Permissions

Tux requires the following permissions for this module:

- **Send Messages** - Required for command responses
- **Embed Links** - Required for rich snippet displays
- **Manage Messages** - Required for locking and managing snippet responses

### User Permissions

Snippet commands are available to all users by default, but snippet creation and editing may be restricted to specific permission ranks based on server configuration.

!!! tip "Permission System"
    Tux uses a dynamic permission system. Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Related Documentation

- [Permission Configuration](../../../admin/config/commands.md)
- [Admin Configuration Guide](../../../admin/config/index.md)
