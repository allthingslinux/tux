# Admin Troubleshooting

Common issues server administrators encounter and their solutions.

## Configuration Issues

### Bot Not Starting
- **Check bot token** - Verify the bot token is correct and valid
- **Check permissions** - Ensure the bot has necessary Discord permissions
- **Verify configuration** - Check that configuration files are valid JSON/YAML/TOML

### Commands Not Working
- **Check bot permissions** - Ensure Tux has the required permissions in your server
- **Verify command prefix** - Check if the command prefix is set correctly
- **Check role hierarchy** - Ensure Tux's role is above users' roles

## Permission Issues

### Permission Denied Errors
- **Check role hierarchy** - Ensure Tux's role is above the target user's role
- **Verify bot permissions** - Check that Tux has the necessary Discord permissions
- **Check command permissions** - Verify the command's permission requirements

### Users Can't Use Commands
- **Check user roles** - Ensure users have the required roles/permissions
- **Verify command settings** - Check if commands are enabled for the user's role
- **Check channel permissions** - Ensure users can send messages in the channel

## Feature Configuration

### Features Not Working
- **Check feature settings** - Verify features are enabled in configuration
- **Check dependencies** - Ensure required services (database, APIs) are available
- **Verify permissions** - Check that Tux has necessary permissions for the feature

### Database Issues
- **Check database connection** - Verify database is accessible and running
- **Check database permissions** - Ensure Tux has necessary database permissions
- **Verify migrations** - Check that database migrations have been applied

## Getting Help

If you can't resolve your issue:
1. Check the **[FAQ](../community/faq.md)** for common solutions
2. Join our **[Discord server](https://discord.gg/gpmSjcjQxg)** for community support
3. File an issue on **[GitHub](https://github.com/allthingslinux/tux/issues)** for bugs
