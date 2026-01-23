---
title: Logs
tags:
  - admin-guide
  - configuration
  - logs
icon: lucide/message-square-text
---

# Logs Configuration

Configure logging channels for audit logs and moderation logs. These channels help you track important events and moderation actions on your server.

## Overview

Tux supports multiple types of logging channels:

- **Audit Log** - Records all moderation actions (bans, kicks, timeouts, etc.)
- **Moderation Log** - Detailed logs of moderation cases and actions

Both channels use rich embeds to display information clearly and make it easy to review server activity.

## Prerequisites

- **Manage Channels** - The bot needs this to send messages to log channels
- **Send Messages** - Required for posting log entries
- **Embed Links** - Required for rich log formatting

## Configuration

### Using the Dashboard

1. Run `/config logs` or open the [Admin Configuration](index.md) and use **Logs** → **Open**.
2. **Audit Log Channel** - Choose the text channel where audit logs will be posted
3. **Moderation Log Channel** - Choose the text channel where detailed moderation logs will be posted

To clear a setting, open the dropdown and deselect the current value (or choose nothing).

### Channel Setup

1. Create dedicated log channels (e.g. `#audit-log` and `#mod-log`)
2. Ensure the bot has permission to send messages and embed links in these channels
3. Consider restricting read access to moderators and administrators
4. Use `/config logs` to assign the channels

!!! tip "Separate Channels"
    While you can use the same channel for both audit and moderation logs, using separate channels makes it easier to review different types of events.

## What Gets Logged

### Audit Log

The audit log records all moderation actions:

- Bans and unbans
- Kicks
- Timeouts and untimeouts
- Warnings
- Jail and unjail actions
- Temporary bans
- Case modifications

Each entry includes:

- Action type and target user
- Moderator who took the action
- Reason (if provided)
- Timestamp
- Case number (for reference)

### Moderation Log

The moderation log provides detailed information about moderation cases:

- Complete case details
- Case updates and modifications
- Case status changes
- Related actions and follow-ups

## Best Practices

### Channel Permissions

- **Read Access**: Restrict to moderators and administrators
- **Send Messages**: Only the bot needs this permission
- **Embed Links**: Required for rich formatting
- **View Channel History**: Allow moderators to review past logs

### Channel Organization

- Use clear, descriptive channel names (e.g. `#audit-log`, `#mod-log`)
- Pin important information or guidelines in the channel
- Consider using channel categories to organize logs

### Log Retention

- Logs are stored in the database and persist across bot restarts
- Use Discord's built-in channel history for long-term reference
- Consider using a logging bot for external log storage if needed

## Troubleshooting

### Logs Not Appearing

If logs aren't being posted:

1. Check that the log channels are configured correctly
2. Verify the bot has permission to send messages in the channels
3. Ensure the bot has "Embed Links" permission
4. Check that the channels are text channels (not voice or forum channels)

### Missing Information

If log entries are incomplete:

1. Verify the bot has all required permissions
2. Check that the target user or moderator information is available
3. Ensure the bot can access the necessary Discord API data

### Performance

Logging uses caching to improve performance:

- Guild configuration (including log channel IDs) is cached for 5 minutes
- Cache is automatically invalidated when configuration changes
- This reduces database queries and improves response times

## Related Configuration

- **[Jail Configuration](./jail.md)** - Configure jail channel and role
- **[Command Permissions](./commands.md)** - Set who can use moderation commands
- **[Permission Ranks](./ranks.md)** - Set up the permission system

## See Also

- [Moderation Module](../../user/modules/moderation/index.md) - User guide for moderation commands
- [Cases Command](../../user/modules/moderation/cases.md) - View and manage moderation cases
