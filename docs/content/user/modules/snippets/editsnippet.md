---
title: Editsnippet
description: Modify the content of an existing snippet
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - snippets
---

# Editsnippet

The `editsnippet` command allows owners or moderators to update the content of a previously created snippet. This ensures that documentation and canned responses remain accurate and up-to-date without needing to delete and recreate the snippet.

## Syntax

The `editsnippet` command is available as a prefix command:

**Prefix Command:**

```text
$editsnippet <name> <new_content>
```

**Aliases:**

- `es`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | STRING | Yes | The name of the snippet to edit. |
| `new_content` | STRING | Yes | The updated text or code. |

## Usage Examples

### Update Content

Change the text of the `hello` snippet.

```text
$editsnippet hello Welcome back to the updated community!
```

## Permissions

### User Permissions

- **Snippet Owner:** Can edit their own snippets by default.
- **Moderators:** Can edit any snippet.
- **Locked Snippets:** Only moderators (rank 3+) can edit snippets that have been locked.

## Error Handling

### Error: Snippet is Locked

**When it occurs:** When a non-moderator attempts to edit a snippet that has the lock enabled.

**Solution:** Contact a moderator to unlock the snippet if you believe it needs an update.

## Related Commands

- [`$createsnippet`](createsnippet.md) - Create the initial snippet.
- [`$togglesnippetlock`](togglesnippetlock.md) - Lock or unlock a snippet to prevent edits.
