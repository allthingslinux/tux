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

- **Snippet owner:** Can edit their own snippets by default
- **Moderators:** Can edit any snippet regardless of ownership
- **Locked snippets:** Only moderators (rank 3+) can edit snippets that have been locked

## Error Handling

### Snippet is Locked

**When it occurs:** When a non-moderator attempts to edit a snippet that has been locked.

**What happens:** The bot sends an error message indicating the snippet is locked.

**Solutions:**

- Contact a moderator to unlock the snippet if you believe it needs an update
- Use `$snippetinfo` to check the lock status before attempting to edit
- If you're a moderator, use `$togglesnippetlock` to unlock it first

## Related Commands

- [`$createsnippet`](createsnippet.md) - Create the initial snippet
- [`$togglesnippetlock`](togglesnippetlock.md) - Lock or unlock a snippet to prevent edits
- [`$snippetinfo`](snippetinfo.md) - Check snippet details and lock status before editing
