# Frequently Asked Questions

Common questions and answers about Tux.

## General Questions

### What is Tux?

Tux is an all-in-one Discord bot designed for the All Things Linux Discord server, but available for
any server. It provides moderation tools, utility commands, fun features, and more.

### Is Tux free to use?

Yes! Tux is completely free and open source. You can invite it to your server or self-host your own
instance.

### How do I invite Tux to my server?

Use the official invite link from our website or GitHub repository. You'll need Administrator
permissions in your Discord server.

### What permissions does Tux need?

**Basic functionality:**

- Read Messages/View Channels
- Send Messages
- Embed Links
- Read Message History

**Moderation features:**

- Kick Members
- Ban Members
- Manage Messages
- Moderate Members (for timeouts)
- Manage Roles (for jail system)

### Can I use both slash commands and prefix commands?

Yes! Tux supports hybrid commands. Most commands work with both `/command` (slash) and `!command`
(prefix) formats.

## Setup and Configuration

### How do I change the command prefix?

Use `/config prefix set <new_prefix>`. For example: `/config prefix set ?`

### How do I set up moderation logging?

Use `/config logs set Public` to configure where moderation actions are logged.

### How do I configure the permission system?

Use `!permission assign <level> <role>` to set permission levels. Available levels are configured by
server administrators.

### How do I set up the jail system?

1. Create a jail role with restricted permissions
2. Create a jail channel  
3. Configure through server admin commands

### How do I enable the starboard?

Starboard is automatically enabled when messages receive enough ⭐ reactions.

## Commands and Features

### How do I see all available commands?

Use `/help` or `!help` to see all commands. Use `/help <command>` for specific command help.

### Why can't I use certain commands?

Commands may be restricted by:

- Permission level requirements
- Role-based assignments
- Channel restrictions
- Bot permissions

Check with server administrators about your permission level.

### How do I create and use snippets?

```text
!createsnippet <name> <content>  # Create snippet
!<name>                          # Use snippet
!listsnippets                    # List all snippets
!deletesnippet <name>            # Delete snippet
```text

### How does the leveling system work?

Users gain XP by participating in chat. Use `/level` to check your level.

### How do I set reminders?

Use `/remindme <time> <message>`. Examples:

- `/remindme 1h Take a break`
- `/remindme 2d Pay bills`
- `/remindme tomorrow Meeting at 3pm`

## Moderation

### How do I ban/kick/warn users?

```text
/ban @user <reason>      # Ban user
/kick @user <reason>     # Kick user  
/warn @user <reason>     # Warn user
/timeout @user 1h <reason> # Timeout for 1 hour
```text

### How do I view moderation history?

```text
/case <number>           # View specific case
/cases @user             # View all cases for user
```text

### How do I edit or delete cases?

```text
/editcase <number> reason "New reason"  # Edit case
/deletecase <number>                    # Delete case
```text

### What's the difference between timeout and jail?

- **Timeout**: Uses Discord's built-in timeout feature (max 28 days)
- **Jail**: Uses a custom role system that you configure (unlimited duration)

### Why can't the bot moderate certain users?

The bot cannot moderate:

- Server owner
- Users with roles higher than the bot's role
- Other bots (in most cases)
- Users the bot doesn't have permission to moderate

## Troubleshooting

### The bot isn't responding to commands

1. Check if bot is online (green status)
2. Verify bot has "Send Messages" permission
3. Try both `/help` and `!help`
4. Check if you're using the correct prefix

### Commands return "Missing Permissions" error

1. Check bot's role permissions in server settings
2. Ensure bot role is above target user roles
3. Verify bot has the specific permission needed (kick, ban, etc.)

### "You don't have permission" error

1. Check with server admin about your permission level
2. Ask server admin to adjust your permissions
3. Check if the command is whitelisted for your role

### Database errors

These are usually temporary. Try the command again in a few minutes. If the issue persists, report
it on GitHub.

### Bot seems slow or unresponsive

1. Check `/ping` for latency
2. Check Discord's status page for API issues
3. Report persistent issues in our Discord server

## Self-Hosting

### Can I host my own instance of Tux?

Yes! Tux is open source. Check our installation guide for Docker, VPS, and cloud deployment options.

### What are the system requirements?

- Python 3.13+
- PostgreSQL database
- 1GB+ RAM (2GB+ recommended)
- 10GB+ storage

### How do I get a Discord bot token?

1. Go to <https://discord.com/developers/applications>
2. Create a new application
3. Go to "Bot" section and create a bot
4. Copy the token (keep it secure!)

### Can I modify the bot for my needs?

Yes! Fork the repository and make your changes. The bot is licensed under GPL v3.0.

### How do I update my self-hosted instance?

1. Pull latest changes from GitHub
2. Update dependencies: `uv sync`
3. Run database migrations: `uv run db migrate-push`
4. Restart the bot

### Where can I get help with self-hosting?

Join our Discord server and ask in the `#self-hosting` channel.

## Privacy and Data

### What data does Tux store?

Tux stores:

- Server configuration settings
- Moderation case history
- User permission levels
- Snippets and reminders
- Level/XP data (if enabled)

### Does Tux store message content?

No, Tux does not store message content or chat history.

### How long is data retained?

- Configuration: Until manually deleted
- Cases: Indefinitely (for moderation history)
- Reminders: Deleted after execution
- Levels: Until manually reset

### Can I delete my data?

Server administrators can delete server data by removing the bot. For self-hosted instances, you
control all data.

### Is my data secure?

We follow security best practices:

- Encrypted database connections
- No unnecessary data collection
- Regular security updates
- Open source for transparency

## Development and Contributing

### How can I contribute to Tux?

- Report bugs on GitHub
- Suggest features
- Contribute code (see contributing guide)
- Help with documentation
- Support other users

### How do I report bugs?

Create a bug report on GitHub with:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Bot version and environment info

### How do I suggest new features?

Create a feature request on GitHub or discuss it in our Discord server first.

### Is there a development roadmap?

Check GitHub issues and milestones for planned features and improvements.

### How can I stay updated on changes?

- Watch the GitHub repository
- Join our Discord server
- Check release notes for updates

## Technical Questions

### What programming language is Tux written in?

Python 3.13+ using the discord.py library.

### What database does Tux use?

PostgreSQL with SQLModel (Pydantic + SQLAlchemy) for type-safe database operations.

### Does Tux support sharding?

Currently, Tux is designed for single-instance deployment. Sharding support may be added in the
future.

### Can Tux work with other databases?

Tux is designed for PostgreSQL. While SQLAlchemy supports other databases, they haven't been tested.

### How does error tracking work?

Tux uses Sentry for error tracking and monitoring (optional for self-hosted instances).

## Getting More Help

### Where can I get real-time help?

Join our Discord server: [discord.gg/gpmSjcjQxg](https://discord.gg/gpmSjcjQxg)

### How do I report security issues?

Email security issues privately rather than posting them publicly. Contact information is in the
repository.

### Can I hire someone to set up Tux for me?

While we don't provide paid setup services, community members may be willing to help. Ask in our
Discord server.

### Is there commercial support available?

Tux is a community project without commercial support. However, the community is very helpful!

---

**Still have questions?** Join our Discord server or create an issue on GitHub. We're here to help!
