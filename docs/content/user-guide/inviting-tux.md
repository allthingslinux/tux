# Inviting Tux to Your Server

This guide covers how to add Tux to your Discord server.

## Official Tux Bot

!!! note "Coming Soon"
    An officially hosted Tux bot will be available in the future. For now, you'll need to self-host your own instance or wait for the official release.

    Join the **[Discord server](https://discord.gg/gpmSjcjQxg)** for announcements about the official bot.

## Self-Hosting Tux

If you want to run your own Tux instance:

1. Follow the **[Self-Hoster Guide](../getting-started/for-self-hosters.md)**
2. Deploy Tux using Docker, VPS, or a cloud platform
3. Create your own Discord bot application
4. Invite your bot using the steps below

## Invite Process

Once you have a Tux bot (yours or official):

### Step 1: Get the Invite Link

For your self-hosted bot:

1. Go to the **[Discord Developer Portal](https://discord.com/developers/applications)**
2. Select your bot application
3. Go to **OAuth2** → **URL Generator**
4. Select scopes and permissions (see below)
5. Copy the generated URL

### Step 2: Select Scopes

Required scopes:

- ☑️ **`bot`** - Basic bot functionality
- ☑️ **`applications.commands`** - Slash commands

### Step 3: Select Permissions

#### Minimum Required Permissions

For basic functionality:

- ☑️ **Read Messages/View Channels** - See channels and messages
- ☑️ **Send Messages** - Send responses
- ☑️ **Send Messages in Threads** - Reply in threads
- ☑️ **Embed Links** - Send rich embeds
- ☑️ **Attach Files** - Send images/files
- ☑️ **Read Message History** - Access message history
- ☑️ **Add Reactions** - React to messages
- ☑️ **Use External Emojis** - Use custom emojis

#### Moderation Permissions

For full moderation features:

- ☑️ **Manage Messages** - Delete/edit messages (for purge)
- ☑️ **Kick Members** - Kick users
- ☑️ **Ban Members** - Ban/unban users
- ☑️ **Moderate Members** - Timeout users
- ☑️ **Manage Roles** - Assign roles (for jail system)

#### Recommended Full Permissions

For all features:

- All of the above, plus:
- ☑️ **Manage Channels** - For temp VC creation
- ☑️ **View Audit Log** - Enhanced moderation tracking

### Step 4: Generate and Use Invite URL

1. **Copy the generated URL**
2. **Paste in your browser** or send to a server admin
3. **Select your server** from the dropdown
4. **Authorize** the bot
5. **Complete any CAPTCHA** if prompted

### Step 5: Verify Bot Joined

Check that Tux appeared in your server:

- Look for Tux in the member list
- You should see a "joined the server" message
- Try a command: `/ping` or `/help`

## Initial Setup

After inviting Tux:

### 1. Run the Setup Wizard

The easiest way to configure Tux:

```
/config wizard
```

This interactive wizard will guide you through:

- Setting up moderation channels
- Configuring the jail system
- Setting up starboard
- Configuring XP roles
- Basic bot settings

### 2. Set Up Permissions

Configure who can use which commands:

```
# Initialize permission ranks
/config rank init

# Assign roles to ranks
/config rank assign @Moderators 3
/config rank assign @Admins 5
```

**[Learn more about permissions →](permissions.md)**

### 3. Configure Channels

Set up important channels:

```
# Moderation log channel
/config set log_channel #mod-logs

# Starboard channel
/config set starboard_channel #starboard
```

### 4. Test Commands

Verify everything works:

```
# Basic test
/ping

# Info command
/info @yourself

# If you're a moderator
/warn @TestUser Test warning
/cases view
```

## Permission Requirements

### Discord Server Permissions

To invite Tux, you need:

- **Administrator** permission in the server, OR
- **Manage Server** permission

### Bot Permissions

Ensure Tux's role has the requested permissions:

1. Go to **Server Settings** → **Roles**
2. Find Tux's role (usually named "Tux")
3. Verify it has the required permissions
4. Move Tux's role **above** roles it needs to moderate

!!! warning "Role Hierarchy"
    Tux cannot moderate users with roles higher than its own role. Place Tux's role appropriately in the role list.

## Channel-Specific Permissions

### Allowing Tux in Channels

Tux needs access to channels to work there:

1. **Channel Settings** → **Permissions**
2. Add **Tux** or its role
3. Grant:
   - ✅ View Channel
   - ✅ Send Messages
   - ✅ Embed Links
   - ✅ Read Message History

### Restricting Tux

To prevent Tux from certain channels:

1. **Channel Settings** → **Permissions**
2. Add **Tux** or its role
3. Deny:
   - ❌ View Channel

## Troubleshooting

### Bot Doesn't Appear in Server

**Possible causes:**

- ❌ You don't have permission to add bots
- ❌ The invite link is incorrect or expired
- ❌ Server reached bot limit (100 bots max per server)

**Solutions:**

- Ask a server administrator to invite the bot
- Regenerate the invite link
- Remove unused bots to make space

### Bot Shows as Offline

**Possible causes:**

- ❌ Bot is not running (self-hosted)
- ❌ Bot token is invalid
- ❌ Network issues

**Solutions:**

- Check if bot process is running
- Verify bot token is correct
- Check bot's internet connection
- Check Discord API status

### Commands Don't Work

**Possible causes:**

- ❌ Bot lacks required Discord permissions
- ❌ User lacks required Tux permissions (rank)
- ❌ Commands not synced

**Solutions:**

1. Check bot's Discord permissions
2. Check user's roles and assigned ranks: `/config role`
3. Sync commands: `/dev sync_tree` (requires appropriate rank)
4. Check channel-specific permissions

### "Missing Access" Error

**Possible causes:**

- ❌ Bot can't see the channel
- ❌ Bot lacks "View Channel" permission

**Solutions:**

- Grant Tux "View Channel" permission in channel settings
- Check role permissions

### "Missing Permissions" for Moderation

**Possible causes:**

- ❌ Bot lacks Discord moderation permissions
- ❌ Target user has higher role than bot
- ❌ Target user is server owner

**Solutions:**

- Grant bot appropriate Discord permissions (Kick/Ban/Moderate Members)
- Move bot's role higher in role list (but below admin roles)
- Server owner cannot be moderated by bots

## Permissions Checklist

Before inviting, ensure you have:

- [ ] Administrator or Manage Server permission
- [ ] Decided which permissions Tux needs
- [ ] Generated invite URL with correct scopes
- [ ] Planned role hierarchy (where Tux's role will go)

After inviting, ensure:

- [ ] Bot appears in server
- [ ] Bot shows as online (green status)
- [ ] `/ping` command works
- [ ] Bot's role is properly positioned
- [ ] Required permissions are granted
- [ ] Channel access is configured
- [ ] Setup wizard completed: `/config wizard`
- [ ] Permission ranks configured

## Next Steps

Once Tux is in your server:

1. **[Run Setup Wizard](commands/config.md)** - Configure basic settings
2. **[Set Up Permissions](permissions.md)** - Configure rank system
3. **[Learn Commands](commands/moderation.md)** - Explore what Tux can do
4. **[Configure Features](commands/config.md)** - Enable desired features

## Getting Help

### Bot Won't Join

- Check you have permission to add bots
- Verify the invite link is correct
- Try a different browser
- Check Discord's status page

### Bot Joined But Doesn't Respond

- Wait a few minutes (Discord needs to sync)
- Try `/help` or `/ping`
- Check bot is online (green dot)
- Verify bot has channel permissions

### Need More Help?

- **[FAQ](../community/faq.md)** - Common questions
- **[Discord Support](https://discord.gg/gpmSjcjQxg)** - Ask the community
- **[GitHub Issues](https://github.com/allthingslinux/tux/issues)** - Report bugs

---

**Ready to configure Tux?** Head to the **[Configuration Guide](commands/config.md)** or run `/config wizard` in your server!
