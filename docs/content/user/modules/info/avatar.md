---
title: Avatar
description: View user avatars in high quality
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - info
  - avatar
---

# Avatar

The `avatar` command allows you to view the profile picture (avatar) of yourself or any other member in the server. It retrieves both the server-specific avatar and the global profile avatar if available, ensuring you can see the highest quality version of their image.

## Syntax

The `avatar` command can be used in two ways:

**Slash Command:**

```text
/avatar [member:MEMBER]
```

**Prefix Command:**

```text
$avatar [member]
```

**Aliases:**

- `av`
- `pfp`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member` | MEMBER | No | The member whose avatar you want to view. Defaults to yourself. |

## Permissions

### Bot Permissions

Tux requires the following permissions to execute this command:

- **Embed Links** - To display the avatars neatly.
- **Send Messages** - To deliver the files.

### User Permissions

This command is available to all users.

## Usage Examples

### View Your Own Avatar

Quickly see your current profile pictures.

```text
/avatar
```

### View Another Member's Avatar

See the global and server-specific avatars for a specific user.

```text
/avatar member:@User
```

## Response

The bot responds by sending up to two images (as files):

1. The member's **Server Avatar** (if set).
2. The member's **Global Avatar**.

If the user has no avatar set (unlikely but possible), the bot will inform you.

## Related Commands

- [`/info`](info.md) - Get detailed account and member information.
