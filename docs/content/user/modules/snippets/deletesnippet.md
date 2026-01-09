---
title: Deletesnippet
description: Remove a snippet or alias from the library
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - snippets
---

# Deletesnippet

The `deletesnippet` command is used to permanently remove a snippet or alias from the server's database. This is used to clean up outdated content or reclaim names for new purposes.

## Syntax

The `deletesnippet` command is available as a prefix command:

**Prefix Command:**

```text
$deletesnippet <name>
```

**Aliases:**

- `ds`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | STRING | Yes | The name of the snippet to delete. |

## Usage Examples

### Delete a Snippet

Remove the `old-guide` snippet.

```text
$deletesnippet old-guide
```

## Permissions

### User Permissions

- **Snippet Owner:** Can delete their own snippets.
- **Moderators:** Can delete any snippet.
- **Locked Snippets:** Only moderators (rank 3+) can delete snippets that are currently locked.

## Behavior Notes

- **Alias Safety:** Deleting an alias will **not** delete the target snippet it points to.
- **Broken Aliases:** If you delete a target snippet, any aliases pointing to it will become "broken." The bot automatically cleans these up when a user attempts to use them.

## Related Commands

- [`$createsnippet`](createsnippet.md) - Create a new replacement snippet.
- [`$snippets`](snippets.md) - Check the list to verify deletion.
