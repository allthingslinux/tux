---
title: Togglesnippetlock
description: Lock or unlock a snippet to control editing permissions
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - snippets
  - admin
---

# Togglesnippetlock

The `togglesnippetlock` command allows moderators to protect important snippets from being edited or deleted by their original owners. When a snippet is locked, only moderators (Rank 3+) can modify its content, settings, or delete it from the server.

This is primarily used to secure official server documentation, standard responses, or frequently used community templates.

## Syntax

The `togglesnippetlock` command is available as a prefix command:

**Prefix Command:**

```text
$togglesnippetlock <name>
```

**Aliases:**

- `tsl`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | STRING | Yes | The name of the snippet to lock or unlock. |

## Usage Examples

### Locking a Resource

Protect a server guide from unauthorized changes.

```text
$togglesnippetlock guide
```

### Unlocking for Maintenance

Allow the owner to update their snippet again.

```text
$togglesnippetlock guide
```

## Response

The bot confirms the new status of the snippet:
`✅ Snippet "guide" has been locked.` or `✅ Snippet "guide" has been unlocked.`

## Permissions

### User Permissions

- **Rank 3 (Moderator) or higher:** Required to use this command.

!!! info "Permission System"
    Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Behavior Notes

- **Persistence:** The lock status is stored permanently in the database.
- **Visual Feedback:** Locked snippets appear with a 🔒 icon in the `$snippets` list.

## Related Commands

- [`$editsnippet`](editsnippet.md) - Modify a snippet after unlocking.
- [`$snippetinfo`](snippetinfo.md) - Verify the lock status and view other metadata.
