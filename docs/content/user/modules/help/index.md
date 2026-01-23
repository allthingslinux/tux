---
title: Help
description: Get help with Tux commands and features using the interactive help system
icon: lucide/help-circle
tags:
  - user-guide
  - commands
  - utility
  - help
---

# Help

The `help` command provides an interactive interface to explore all available Tux commands, organized by category. It's the best way to discover what Tux can do and learn how to use specific commands.

## Syntax

The help command is available as a prefix command:

```text
$help [command]
$h [command]
$commands [command]
```

**Aliases:**

You can also use these aliases instead of `help`:

- `h`
- `commands`

!!! note "Prefix Command Only"
    The help command is only available as a prefix command (using `$`), not as a slash command. This is because it uses Discord.py's built-in help command system.

## Usage Examples

### View All Commands

Get an overview of all available command categories:

```text
$help
```

This opens an interactive menu with:

- **Category dropdown** - Browse commands by category (Moderation, Utility, Fun, etc.)
- **Command dropdown** - Select specific commands to view details
- **Navigation buttons** - Navigate between pages and categories
- **Help banner** - Visual banner image (if configured)

### Get Help for a Specific Command

View detailed information about a specific command:

```text
$help ban
$help ping
$h cases
```

This shows:

- Command description and usage
- Available aliases
- Required parameters and flags
- Permission requirements
- Usage examples

### Get Help for a Subcommand

View help for command subcommands:

```text
$help cases view
$help config ranks
```

## Features

### Interactive Navigation

The help command uses an interactive dropdown menu system:

1. **Category Selection** - Choose from categories like Moderation, Utility, Fun, etc.
2. **Command Selection** - Browse commands within each category
3. **Subcommand Navigation** - Navigate through command groups and subcommands
4. **Back Navigation** - Return to previous views easily

### Permission Filtering

The help command automatically filters commands based on your permission rank:

- **Visible Commands** - Only shows commands you have permission to use
- **Hidden Commands** - Commands you can't access are hidden from the menu
- **Dynamic Updates** - Command visibility updates based on your current permissions

### Performance Optimizations

The help system uses several performance optimizations:

- **Caching** - Command categories and permissions are cached for faster loading
- **Batch Processing** - Permission checks are batched to reduce database queries
- **Optimized Rendering** - Commands are organized efficiently for quick navigation

## Response Format

When you run `$help`, you'll see:

- **Main Embed** - Overview of all command categories with descriptions
- **Category Dropdown** - Select a category to browse commands
- **Command Dropdown** - Select a command to view details
- **Navigation Buttons** - Navigate between pages
- **Help Banner** - Visual banner image (if available)

### Main Help View

The main help view shows:

- **Command Categories** - All available command categories
- **Category Descriptions** - Brief descriptions of what each category contains
- **Usage Instructions** - How to use the help system
- **Support Links** - Links to support server and GitHub repository
- **Bot Information** - Bot name, version, and owner information

### Command Details View

When viewing a specific command, you'll see:

- **Command Name** - The command and its aliases
- **Description** - What the command does
- **Usage** - How to use the command with examples
- **Parameters** - Required and optional parameters
- **Flags** - Available command flags and options
- **Permissions** - Required permission rank (if any)
- **Examples** - Practical usage examples

## Permissions

### Bot Permissions

Tux requires the following permissions to display help:

- **Send Messages** - To display help information
- **Embed Links** - For rich formatting
- **Add Reactions** - For interactive navigation (if using reactions)

### User Permissions

The help command is available to all users. However, the command list is filtered based on your permission rank:

- **All Users** - See commands available to rank 0 (Member)
- **Moderators** - See additional moderation commands
- **Administrators** - See all commands including configuration

!!! tip "Permission-Based Filtering"
    The help command automatically shows only commands you can use. If you don't see a command, you may not have the required permission rank. Contact a server administrator to check your permissions.

## Tips and Tricks

### Quick Command Lookup

Use the help command to quickly find commands:

```text
# Find specific command
$help ban

# Find command group
$help cases

# Find subcommand
$help cases view
```

!!! note "Category Navigation"
    To browse commands by category (like Moderation, Utility, etc.), use `$help` to open the interactive menu, then select a category from the dropdown. Categories cannot be accessed directly via command arguments.

### Discovering New Commands

Browse categories to discover new features:

1. Run `$help` to see all categories
2. Select a category from the dropdown
3. Browse available commands
4. Select a command to view details

### Understanding Command Syntax

The help command shows:

- **Required parameters** - Parameters you must provide
- **Optional parameters** - Parameters in `[]` brackets
- **Flags** - Command flags with aliases
- **Examples** - Real-world usage examples

## Troubleshooting

### Help Command Not Responding

If the help command doesn't respond:

1. Check that the bot is online and responsive
2. Verify the bot has permission to send messages
3. Try using the prefix command instead: `$help`
4. Check bot logs for errors

### Commands Not Showing

If you don't see commands you expect:

1. Check your permission rank using `/config roles`
2. Verify the command is configured in `/config commands`
3. Ensure you have the required Discord roles
4. Note: Commands work in DMs without permission checks

### Navigation Not Working

If dropdowns or buttons don't work:

1. Ensure you're the one who ran the command (interactions are user-specific)
2. Try running `$help` again to get a fresh menu
3. Check that the bot has permission to use message components

## Related Commands

- [`/ping`](ping.md) - Check bot status and latency
- [`/config`](../../config/index.md) - Configure server settings
- [Moderation Commands](../../moderation/index.md) - Moderation command reference

## See Also

- [Permission Configuration](../../../../admin/config/commands.md) - Configure command permissions
- [Admin Configuration Guide](../../../../admin/config/index.md) - Complete configuration reference
- [Command Modules](../index.md) - Browse all command modules
