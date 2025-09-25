# Getting Support

Need help with Tux? This guide covers all the ways to get support and find answers to your
questions.

## Quick Help

### Common Commands

**Get Help:**

```text
/help                    # Show all commands
/help <command>          # Get help for specific command
!help                    # Prefix version
```text

**Check Bot Status:**

```text
/ping                    # Check bot latency
```text

**Configuration:**

```text
/config prefix set ?         # Change command prefix
/config logs set Public      # Set log channel
```text

### First Steps Checklist

If Tux isn't working properly:

- [ ] Check if bot is online (green status in member list)
- [ ] Verify bot has necessary permissions
- [ ] Try both slash commands (`/help`) and prefix commands (`!help`)
- [ ] Check if you're using the correct command prefix
- [ ] Ensure you have permission to use the command

## Support Channels

### Discord Server

**Join our official Discord server for:**

- Real-time help and support
- Community discussions
- Feature announcements
- Direct help from developers

**Server Invite:** [discord.gg/gpmSjcjQxg](https://discord.gg/gpmSjcjQxg)

**Support Channels:**

- `#general-support` - General questions and help
- `#technical-support` - Technical issues and bugs
- `#feature-requests` - Suggest new features
- `#self-hosting` - Self-hosting help

### GitHub Issues

**Use GitHub for:**

- Bug reports
- Feature requests
- Technical discussions
- Documentation issues

**Repository:** [github.com/allthingslinux/tux](https://github.com/allthingslinux/tux)

**Issue Templates:**

- Bug Report - For reporting bugs
- Feature Request - For suggesting features
- Documentation - For documentation issues

### GitHub Discussions

**Use Discussions for:**

- General questions
- Ideas and proposals
- Show and tell
- Long-form discussions

**Access:** Go to the GitHub repository and click "Discussions"

## Troubleshooting

### Bot Not Responding

**Check Bot Status:**

1. Look for Tux in the member list
2. Check if status is online (green dot)
3. If offline, the bot may be down temporarily

**Check Permissions:**

1. Ensure bot has "Send Messages" permission
2. Check channel-specific permissions
3. Verify bot role is above target roles (for moderation)

**Try Different Commands:**

```text
/ping                    # Test basic functionality
!ping                    # Test prefix commands
/help                    # Check if slash commands work
```text

### Commands Not Working

**Common Fixes:**

- Use correct command prefix (check with `/config prefix`)
- Ensure proper command syntax
- Check if command is available in current channel
- Verify you have required permission level

**Command Syntax:**

```text
# Correct
/ban @user spam

# Incorrect
/ban user spam          # Missing @ mention
/ban @user              # Missing reason (if required)
```text

### Moderation Issues

**Bot Can't Moderate:**

1. Check bot permissions:
   - Kick Members (for kick command)
   - Ban Members (for ban command)
   - Moderate Members (for timeout command)
   - Manage Roles (for jail system)

2. Check role hierarchy:
   - Bot role must be above target user's highest role
   - Bot cannot moderate server owner
   - Bot cannot moderate users with higher roles

**Case System Issues:**

```text
/case 123               # Check if case exists
/cases @user            # Check user's case history
```text

### Database/Configuration Issues

**Configuration Problems:**

```text
/config                 # View current configuration
/config log_channel #logs # Set log channel
/config prefix !        # Reset prefix
```text

**Permission System:**

```text
# Check with server administrators about permissions
```text

## Frequently Asked Questions

### General Questions

**Q: How do I invite Tux to my server?**
A: Use the official invite link from our website or GitHub repository. Make sure you have
Administrator permissions in your server.

**Q: What permissions does Tux need?**
A: For basic functionality: Send Messages, Embed Links, Read Message History. For moderation: Kick
Members, Ban Members, Manage Messages, Moderate Members.

**Q: How do I change the command prefix?**
A: Use `/config prefix <new_prefix>` or `!config prefix <new_prefix>`.

**Q: Can I use both slash commands and prefix commands?**
A: Yes! Most commands support both formats. Use whichever you prefer.

### Moderation Questions

**Q: How do I set up moderation logging?**
A: Use `/config log_channel #your-log-channel` to set where moderation actions are logged.

**Q: How do I give someone moderator permissions?**
A: Use `!permission assign <level> <role>` to set permission levels for roles.

**Q: What's the difference between timeout and jail?**
A: Timeout uses Discord's built-in timeout feature. Jail uses a custom role system that you need to
set up.

**Q: How do I view someone's moderation history?**
A: Use `/cases @user` to see all cases for that user.

### Technical Questions

**Q: Can I self-host Tux?**
A: Yes! Check our installation guide for Docker, VPS, and cloud platform deployment options.

**Q: How do I report a bug?**
A: Create a bug report on our GitHub repository with detailed information about the issue.

**Q: How do I request a new feature?**
A: Create a feature request on GitHub or discuss it in our Discord server first.

**Q: Is my data safe?**
A: We only store necessary data for bot functionality (case history, configuration). We don't store
message content or personal information.

### Self-Hosting Questions

**Q: What are the system requirements?**
A: Python 3.13+, PostgreSQL database, 1GB+ RAM recommended. See the installation guide for details.

**Q: Can I modify the bot for my server?**
A: Yes! Tux is open source. You can fork the repository and make modifications.

**Q: How do I update my self-hosted instance?**
A: Pull the latest changes from GitHub, update dependencies, and restart the bot. Check for database
migrations.

**Q: Where can I get help with self-hosting?**
A: Join our Discord server and ask in the `#self-hosting` channel.

## Error Messages

### Common Error Messages

### Missing Permissions

- Bot lacks required Discord permissions
- Check bot role permissions in server settings
- Ensure bot role is above target user roles

### Command not found

- Check command spelling
- Verify command prefix
- Use `/help` to see available commands

### You don't have permission to use this command

- Check with server admin about your permission level
- Ask server admin to adjust your permissions
- Some commands require specific roles

### User not found

- Check user mention format (`@user` not `user`)
- Ensure user is in the server
- Try using user ID instead of mention

### Database error occurred

- Temporary database issue
- Try command again in a few minutes
- Report persistent issues on GitHub

### Getting Debug Information

**For Bug Reports:**

```text
/ping                   # Bot latency
/config                 # Current configuration
```text

**Include in Bug Reports:**

- Exact command used
- Error message received
- Bot version (check with server admin)
- Steps to reproduce
- Expected vs actual behavior

## Response Times

### Support Response Times

**Discord Server:**

- General questions: Usually within a few hours
- Technical issues: Within 24 hours
- Complex problems: 1-3 days

**GitHub Issues:**

- Bug reports: Within 48 hours
- Feature requests: Within 1 week
- Pull requests: Within 72 hours

**Emergency Issues:**

- Bot completely down: Within 2 hours
- Security issues: Immediate priority
- Data loss issues: Within 4 hours

### Self-Service Options

**Before Asking for Help:**

1. Check this documentation
2. Search existing GitHub issues
3. Try basic troubleshooting steps
4. Check bot status and permissions

**When Asking for Help:**

1. Provide clear description of issue
2. Include relevant error messages
3. Mention what you've already tried
4. Include bot version and configuration

## Community Guidelines

### Getting Help Effectively

**Do:**

- Be specific about your issue
- Provide relevant details
- Be patient with responses
- Thank helpers
- Share solutions if you find them

**Don't:**

- Ask the same question in multiple channels
- Demand immediate responses
- Be rude or impatient
- Share sensitive information (tokens, passwords)

### Helping Others

**If you can help:**

- Answer questions you know
- Point people to relevant documentation
- Share your experience
- Be patient with beginners

**Community Benefits:**

- Faster support for everyone
- Shared knowledge base
- Stronger community
- Better documentation

## Additional Resources

### Documentation

- **User Guide** - Complete feature overview
- **Admin Guide** - Deployment and administration
- **Developer Guide** - Contributing and development
- **API Reference** - Technical documentation

### External Resources

- **Discord.py Documentation** - For understanding Discord bot concepts
- **PostgreSQL Documentation** - For database-related questions
- **Python Documentation** - For general Python questions

### Status Pages

- **Bot Status** - Check if there are known issues
- **GitHub Status** - Check GitHub service status
- **Discord Status** - Check Discord API status

Remember: The community is here to help! Don't hesitate to ask questions, and consider helping
others when you can.
