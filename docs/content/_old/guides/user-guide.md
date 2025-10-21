# User Guide

Welcome to Tux! This guide covers everything you need to know as a server member or moderator using
Tux.

## Getting Started

### Installation

Tux is designed to be invited to your Discord server by server administrators. If you're a server
admin looking to add Tux:

1. **Invite Tux** to your server using the official invite link
2. **Configure permissions** - Tux needs appropriate permissions for moderation features
3. **Set up channels** - Configure logging and jail channels if desired
4. **Test basic commands** - Try `!help` or `/help` to verify Tux is working

### First Steps

Once Tux is in your server:

1. **Check the help command**: Use `!help` or `/help` to see available commands
2. **Set your prefix**: Use `!config prefix <new_prefix>` to change the command prefix
3. **Configure moderation**: Set up logging channels and moderation settings
4. **Explore features**: Try out the various command categories

## Commands

Tux supports both slash commands (`/command`) and traditional prefix commands (`!command`). Most
commands are available in both formats.

### Moderation Commands

**Basic Moderation:**

- `/ban <user> --reason <reason>` - Ban a user from the server
- `/kick <user> --reason <reason>` - Kick a user from the server  
- `/warn <user> --reason <reason>` - Issue a warning to a user
- `/timeout <user> --duration <time> --reason <reason>` - Timeout a user
- `/tempban <user> --duration <time> --reason <reason>` - Temporary ban
- `/jail <user> --reason <reason>` - Jail a user (requires jail role setup)

**Moderation Management:**

- `/unjail <user>` - Remove jail from user
- `/untimeout <user>` - Remove timeout from user
- `/unban <user>` - Unban a user
- `/clearafk <user>` - Clear AFK status from user

**Special Bans:**

- `/snippetban <user> --reason <reason>` - Ban from using snippets
- `/snippetunban <user>` - Remove snippet ban
- `/pollban <user> --reason <reason>` - Ban from creating polls
- `/pollunban <user>` - Remove poll ban

**Case Management:**

- `/cases [case_number]` - View cases (specific case or list all)
- `/cases view [number]` - View case details
- `/cases modify <case_number> --reason <new_reason>` - Modify a case

**Bulk Moderation:**

- `/purge <amount>` - Delete multiple messages
- `/slowmode <seconds>` - Set channel slowmode
- `/report <user> <reason>` - Report a user

### Information Commands

**Server Information:**

- `/membercount` - Display server member count
- `/avatar [user]` - Show user's avatar

**Bot Information:**

- `/ping` - Check bot latency

### Utility Commands

**General Utilities:**

- `/afk [message]` - Set your AFK status
- `/remindme <time> <message>` - Set a reminder
- `/poll <question> [options]` - Create a poll
- `/timezones` - Timezone utilities
- `/self_timeout <duration>` - Timeout yourself

**Text Utilities:**

- `/encode_decode <encode|decode> <text>` - Encode/decode base64

**Tools:**

- `/run <code>` - Execute code (if permitted)
- `/wolfram <query>` - Query Wolfram Alpha
- `/tldr <command>` - Get command documentation

### Fun Commands

**Entertainment:**

- `/fact` - Get a random fact

### Admin Commands

**Server Management:**

- `/config logs set <Public|Private>` - Configure logging
- `/config channels set` - Configure channels
- `/config prefix set <prefix>` - Change command prefix

**Permission Management:**

- Permission management through role-based system

## Features

### Snippets

**Text Snippets:**

- Store frequently used text snippets
- Quick access with simple commands
- Server-specific snippet storage

**Commands:**

- `!createsnippet <name> <content>` - Create a snippet
- `!<name>` - Use a snippet (dynamic command)
- `!listsnippets` - List all snippets
- `!deletesnippet <name>` - Delete a snippet
- `!editsnippet <name> <content>` - Edit a snippet
- `!snippetinfo <name>` - Get snippet information

## System Features

### Permission System

Tux uses a flexible permission system with role-based access control:

**Permission Levels:**

- Commands use decorators like `@require_moderator()` and `@require_junior_mod()`
- Permission levels are managed through Discord roles
- Server administrators can configure custom permission hierarchies

**Permission Management:**

- Use `!permission` commands (prefix only) for configuration
- Requires Administrator permissions in Discord
- Supports custom permission levels and role assignments

**Command Restrictions:**

- Commands have built-in permission requirements
- Server administrators can configure additional restrictions
- Permission system integrates with Discord's role hierarchy

### Moderation Tools

**Case System:**

- All moderation actions create numbered cases
- Cases include timestamps, reasons, and moderator information
- Cases can be edited or deleted by moderators
- View user's moderation history with `/cases`

**Logging:**

- Configure a log channel to track all moderation actions
- Automatic logging of bans, kicks, warnings, and timeouts
- Message deletion and bulk moderation logging

**Jail System:**

- Alternative to timeouts using role-based restrictions
- Requires setup of jail role and jail channel
- Users can be jailed temporarily or permanently

### Levels & XP System

**How It Works:**

- Users gain XP by participating in chat
- XP is awarded based on message activity
- Level up notifications can be enabled/disabled
- Leaderboards show top users by XP

**Commands:**

- `/level [user]` - Check level and XP
- `/levels set <user> <level>` - Set user's level (admin only)

### Starboard

**Feature:**

- Messages with enough ⭐ reactions get posted to starboard
- Configurable through server configuration
- Prevents self-starring and duplicate entries

### Configuration

**Basic Settings:**

```bash
/config prefix set ?         # Set your preferred command prefix
/config logs set Public      # Configure where logs are sent
```

**Optional Configuration:**

- **Jail Role/Channel**: For jail-based moderation
- **Permission Levels**: Set up permission levels for your staff

### Environment Variables

Server administrators may need to configure these environment variables:

**Required:**

- `DISCORD_TOKEN` - Your Discord bot token
- `POSTGRES_HOST` - Database host
- `POSTGRES_DB` - Database name
- `POSTGRES_USER` - Database username  
- `POSTGRES_PASSWORD` - Database password

**Optional:**

- `DATABASE_URL` - Complete database URL override
- `DEBUG` - Enable debug mode (true/false)

### Channel Configuration

**Log Channel:**

```text
/config log_channel #mod-logs
```

**Jail Channel:**

```text
/config jail_channel #jail
/config jail_role @Jailed
```

**Starboard:**

```text
/config starboard_channel #starboard
/config starboard_threshold 5
```

## Troubleshooting

### Common Issues

**Bot Not Responding:**

1. Check if bot is online and has proper permissions
2. Verify the command prefix with `/prefix`
3. Ensure the bot can read/send messages in the channel

**Commands Not Working:**

1. Check your permission level with `/permissions`
2. Verify command syntax with `/help <command>`
3. Check if command is blacklisted for your role

**Moderation Issues:**

1. Ensure bot has appropriate moderation permissions
2. Check role hierarchy - bot role must be above target user
3. Verify log channel permissions

### Getting Help

**In-Server Help:**

- Use `/help` for command list
- Use `/help <command>` for specific command help
- Check with server admin for bot status

**External Support:**

- Join the official support Discord server
- Check the FAQ for common questions
- Report bugs on GitHub

## Best Practices

### For Server Owners

1. **Set Clear Permissions**: Define who can use moderation commands
2. **Configure Logging**: Always set up a mod log channel
3. **Train Your Staff**: Ensure moderators understand the case system
4. **Regular Maintenance**: Periodically review and clean up old cases

### For Moderators

1. **Always Provide Reasons**: Include clear reasons for all moderation actions
2. **Use Appropriate Actions**: Match punishment severity to the offense
3. **Document Everything**: The case system helps track user behavior
4. **Communicate**: Coordinate with other moderators on ongoing issues

### For Users

1. **Read Server Rules**: Understand your server's specific guidelines
2. **Use Commands Appropriately**: Don't spam or misuse bot features
3. **Report Issues**: Help moderators by reporting problems
4. **Be Patient**: Some commands may have cooldowns or restrictions

This guide covers the essential features of Tux. For more detailed technical information, see the
developer documentation or join our support server for assistance.
