# Guild Setup

Per-server configuration using the config wizard and commands.

## Config Wizard

The easiest way to set up your server:

```text
/config wizard
```

Interactive setup for:

1. Moderation channels (log channel, jail channel)
2. Jail system (jail role)
3. Starboard (channel, emoji, threshold)
4. XP roles
5. Basic settings

## Manual Configuration

Use `/config` commands to configure individual settings.

## Guild-Specific Settings

Each Discord server can configure:

- Command prefix
- Log channels (mod actions, events)
- Jail role and channel
- Starboard channel and threshold
- Permission rank assignments

## Database Storage

Guild configuration is stored in the database, not config files.

Use commands to manage:

- `/config` - View settings
- `/config wizard` - Interactive setup
- `/config role assign` - Set up permissions

## Related

- **[Config Commands](../../user-guide/commands/config.md)**
- **[Permissions](permissions.md)**

---

*Full documentation in progress. Run `/config wizard` for guided setup.*
