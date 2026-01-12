---
title: Moderation
description: Comprehensive moderation tools for managing your Discord server
tags:
  - user-guide
  - modules
  - moderation
icon: lucide/shield
---

# Moderation

The Moderation module provides a comprehensive set of commands for managing your Discord server. It is essential for server administrators and moderators, offering tools for user management, case tracking, warnings, and automated moderation actions.

The module includes commands for banning, kicking, warning users, managing moderation cases, and handling various moderation scenarios. All moderation actions are logged to moderation cases, providing a complete audit trail of all actions taken in your server.

## Command Groups

This module includes the following command groups:

### Cases

The cases command group provides tools for viewing and managing moderation cases. Each moderation action creates a case, which can be viewed, edited, and referenced later.

**Commands:**

- `cases view` (aliases: `v`, `show`, `get`, `list`) - View a specific moderation case by number
- `cases search` (aliases: `filter`, `find`) - Search/filter moderation cases by criteria
- `cases modify` (aliases: `m`, `edit`, `update`) - Modify case information (status, reason)

## Commands

| Command | Description | Documentation |
|---------|-------------|---------------|
| `/ban` | Ban a member from the server | [Details](ban.md) |
| `/unban` | Unban a previously banned member | [Details](unban.md) |
| `/kick` | Remove a member from the server | [Details](kick.md) |
| `/warn` | Issue a warning to a member | [Details](warn.md) |
| `/timeout` | Timeout a member for a specified duration | [Details](timeout.md) |
| `/untimeout` | Remove a timeout from a member | [Details](untimeout.md) |
| `/jail` | Move a member to a jail channel | [Details](jail.md) |
| `/unjail` | Release a member from jail | [Details](unjail.md) |
| `/purge` | Delete multiple messages from a channel | [Details](purge.md) |
| `/slowmode` | Set slowmode for a channel | [Details](slowmode.md) |
| `/cases` | View and manage moderation cases | [Details](cases.md) |
| `/tempban` | Temporarily ban a member | [Details](tempban.md) |
| `/clearafk` | Clear AFK status from members | [Details](clearafk.md) |
| `/report` | Report a user or message | [Details](report.md) |
| `/pollban` | Ban a member from creating polls | [Details](pollban.md) |
| `/pollunban` | Unban a member from creating polls | [Details](pollunban.md) |
| `/snippetban` | Ban a member from creating snippets | [Details](snippetban.md) |
| `/snippetunban` | Unban a member from creating snippets | [Details](snippetunban.md) |

## Common Use Cases

### Handling Rule Violations

When a member violates server rules, moderators need a quick way to take action and maintain order.

**Steps:**

1. Issue a warning for first-time violations using `/warn`.
2. Use `/timeout` for repeat violations to temporarily restrict member interaction.
3. Use `/ban` for severe violations to permanently remove the member.

**Example:**

```text
/warn member:@user reason:"Spamming in general channel"
/timeout member:@user reason:"Repeat spam" duration:1h
/ban member:@user reason:"Malicious behavior"
```

### Cleaning Up Channels

Moderators often need to clean up spam messages or slow down a fast-moving conversation.

**Steps:**

1. Use `/purge` to bulk-delete recent messages.
2. Apply `/slowmode` to the channel to prevent further spamming.

**Example:**

```text
/purge limit:10
/slowmode seconds:30s
```

### Case Management

Reviewing moderation history and managing cases ensures transparency and consistency in server management.

**Steps:**

1. Use `/cases` to view the moderation log.
2. Search for specific users or moderators using `/cases search`.
3. Update case details like reasons or statuses using `/cases modify`.

**Example:**

```text
/cases
/cases view case_number:123
/cases search user:@user
/cases modify reason:"Update: User apologized" case_number:123
```

## Configuration

This module requires the following configuration:

- **Moderation Log Channel:** Channel where moderation actions are logged
- **Jail Channel:** Channel for jailed members (if using jail commands)
- **Permission Ranks:** Configure which ranks can use moderation commands

!!! info "Configuration Guide"
    For detailed configuration instructions, see the [Admin Guide](../../../admin/config/index.md).

## Permissions

### Bot Permissions

Tux requires the following permissions for this module:

- **Ban Members** - Required for ban and unban commands
- **Kick Members** - Required for kick commands
- **Manage Messages** - Required for purge and slowmode commands
- **Moderate Members** - Required for timeout commands
- **Manage Roles** - Required for jail commands (role-based jail)
- **Send Messages** - Required for command responses and logs
- **Embed Links** - Required for rich moderation embeds

### User Permissions

Users need Moderator rank (typically rank 3-5) or higher to use commands in this module.

!!! tip "Permission System"
    Tux uses a dynamic permission system. Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Related Documentation

- [Permission Configuration](../../../admin/config/commands.md)
- [Admin Configuration Guide](../../../admin/config/index.md)
- [Jail Configuration](../../../admin/config/jail.md)
- [Cases Command Group](cases.md)
