---
title: Config
description: Comprehensive guild configuration and management system
tags:
  - user-guide
  - modules
  - configuration
  - admin
icon: lucide/settings
---

# Config

The Config module is the heart of Tux's customization system, allowing administrators to tailor the bot's behavior to their server's specific needs. It provides a unified interface for managing permission ranks, role assignments, command restrictions, and logging configurations.

Using a powerful dashboard-style interface and granular subcommands, administrators can quickly set up the bot and ensure that all moderation, utility, and fun features are correctly configured for their community.

## Command Groups

This module includes the following command groups:

### Config

The main `/config` group provides access to the interactive configuration dashboard and specific setting managers.

**Commands:**

- `/config overview` - View the complete configuration status of the guild
- `/config ranks` - Manage permission ranks (0-7) and their internal names
- `/config roles` - Assign Discord roles to permission ranks
- `/config commands` - Manage which ranks are required for specific commands
- `/config logs` - Configure channel assignments for various event logs

## Commands

| Command | Description | Documentation |
|---------|-------------|---------------|
| `/config overview` | Interactive guild setup dashboard | [Details](../../../admin/config/index.md) |
| `/config ranks` | Permission rank management | [Details](../../../admin/config/ranks.md) |
| `/config roles` | Role-to-rank assignments | [Details](../../../admin/config/roles.md) |
| `/config commands` | Command permission configuration | [Details](../../../admin/config/commands.md) |
| `/config logs` | Log channel configuration | [Details](../../../admin/config/logs.md) |

## Common Use Cases

### Use Case Name: Initial Bot Setup

Quickly initialize the basic permission system after adding Tux to a new server.

**Steps:**

1. Run `/config ranks init` to create the default rank structure (0-7).
2. Use `/config roles` to map your moderator and administrator roles to the appropriate ranks.
3. Review your setup with `/config overview`.

**Example:**

```text
/config ranks init
/config roles assign rank:5 role:@Moderator
```

### Use Case Name: Configuring Command Access

Restrict specific commands to certain ranks to ensure only trusted users can access sensitive features.

**Steps:**

1. Navigate to `/config commands`.
2. Select the command or module you wish to restrict.
3. Set the minimum required rank for that command.

**Example:**

```text
/config commands
```

## Permissions

### Bot Permissions

Tux requires the following permissions for this module:

- **Send Messages** - Required for command responses
- **Embed Links** - Required for the configuration dashboard
- **Manage Roles** - Required to verify role hierarchy during setup
- **Read Message History** - Required for interactive setup components

### User Permissions

Configuration commands are highly sensitive and are restricted to Server Owners and the highest configured permission ranks by default.

!!! tip "Permission System"
    Tux uses a dynamic permission system. Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Related Documentation

- [Permission Configuration](../../../admin/config/commands.md)
- [Admin Setup Guide](../../../admin/setup/index.md)
- [Module Overview](../index.md)
