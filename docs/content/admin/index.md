---
title: Admin Guide
tags:
  - admin-guide
icon: material/shield-outline
---

# Admin Guide

Welcome to the Tux Admin Guide! This guide covers everything you need to know to configure and manage Tux on your Discord server.

## Quick Start

1. **Invite Tux** to your server with appropriate permissions
2. **Configure permissions** using `/config ranks init` to set up the permission system
3. **Set up logging** using `/config logs` to configure audit and moderation logs
4. **Configure features** like jail, starboard, and other modules as needed

## Configuration Overview

Tux uses a unified configuration dashboard accessible via `/config` or `/config overview`. The dashboard provides an interactive interface for managing all server settings.

### Main Configuration Areas

- **[Ranks](./config/ranks.md)** - Set up permission ranks (0-10) for access control
- **[Roles](./config/roles.md)** - Map Discord roles to permission ranks
- **[Commands](./config/commands.md)** - Configure which permission rank is required for each command
- **[Logs](./config/logs.md)** - Configure audit log and moderation log channels
- **[Jail](./config/jail.md)** - Set up jail channel and role for moderation

## Permission System

Tux uses a database-driven permission system that allows each server to customize who can use which commands. The system is based on:

- **Permission Ranks** - Numeric hierarchy (0-10) where higher numbers mean more permissions
- **Role Assignments** - Map Discord roles to permission ranks
- **Command Permissions** - Set required rank for each command per-server

See the [Permission System](../../developer/concepts/core/permission-system.md) for technical details.

## Configuration Dashboard

The configuration dashboard (`/config`) provides a visual interface for managing all server settings. You can:

- View and edit permission ranks
- Assign roles to permission ranks
- Configure command permissions
- Set up logging channels
- Configure jail settings
- And more!

## Getting Help

- **User Commands**: See the [User Guide](../../user/index.md) for command documentation
- **Troubleshooting**: Check the [Troubleshooting Guide](../../support/troubleshooting/admin.md) for common issues
- **FAQ**: Visit the [Admin FAQ](../../faq/admins.md) for frequently asked questions

## Next Steps

1. **[Set Up Permissions](./config/ranks.md)** - Initialize permission ranks for your server
2. **[Configure Logging](./config/logs.md)** - Set up audit and moderation logs
3. **[Assign Roles](./config/roles.md)** - Map Discord roles to permission ranks
4. **[Configure Commands](./config/commands.md)** - Set permission requirements for commands
