# Getting a Discord Bot Token

This guide walks you through creating a Discord bot application and obtaining your bot token.

## Prerequisites

- **Discord Account** with verified email
- **Web Browser** to access Discord Developer Portal

## Step-by-Step Guide

### 1. Access Developer Portal

Visit the **[Discord Developer Portal](https://discord.com/developers/applications)**

Log in with your Discord account if prompted.

### 2. Create New Application

1. Click **"New Application"** (top right)
2. Enter a name for your bot (e.g., "Tux" or "My Server Bot")
3. Accept the Developer Terms of Service
4. Click **"Create"**

### 3. Configure General Information

On the **General Information** tab:

- **Name:** Your bot's name
- **Description:** Brief description of what your bot does
- **Icon:** Upload a bot avatar (optional)
- **Tags:** Add relevant tags (optional)

Click **"Save Changes"** at the bottom.

### 4. Create Bot User

1. Navigate to the **"Bot"** tab in the left sidebar
2. Click **"Add Bot"**
3. Confirm by clicking **"Yes, do it!"**

### 5. Get Your Bot Token

1. In the Bot tab, find the **Token** section
2. Click **"Reset Token"** (or "Copy" if first time)
3. Confirm the action if prompted
4. **Copy the token immediately** and save it securely

!!! danger "Token Security"
    **Never share your bot token publicly!**

    - Don't commit it to Git
    - Don't post it in Discord
    - Don't share it with untrusted people
    - If leaked, reset it immediately

### 6. Configure Bot Settings

Still in the Bot tab:

#### Public Bot

- **Uncheck** "Public Bot" if you only want to use it in your servers
- **Check** if you want others to be able to invite it

#### Requires OAuth2 Code Grant

- Leave **unchecked** (not needed for most bots)

#### Presence Intent

- **Check** if you need to track user presence (for status roles feature)

#### Server Members Intent

- **Check** - Required for Tux to see guild members

#### Message Content Intent

- **Check** - Required for prefix commands and message processing

!!! warning "Privileged Intents"
    Server Members Intent and Message Content Intent are "Privileged Intents".

    For bots in 100+ servers, you'll need to verify your bot and request these intents.

### 7. Configure OAuth2

Navigate to **"OAuth2"** → **"URL Generator"**:

#### Select Scopes

- ☑️ **`bot`** - Basic bot functionality
- ☑️ **`applications.commands`** - Slash commands

#### Select Bot Permissions

**Essential Permissions:**

- ☑️ **Read Messages/View Channels**
- ☑️ **Send Messages**
- ☑️ **Send Messages in Threads**
- ☑️ **Embed Links**
- ☑️ **Attach Files**
- ☑️ **Read Message History**
- ☑️ **Add Reactions**
- ☑️ **Use External Emojis**

**Moderation Permissions:**

- ☑️ **Manage Messages** (for purge)
- ☑️ **Kick Members**
- ☑️ **Ban Members**
- ☑️ **Moderate Members** (for timeouts)
- ☑️ **Manage Roles** (for jail system)

**Advanced (Optional):**

- ☑️ **Manage Channels** (for temp VC)
- ☑️ **View Audit Log** (for enhanced tracking)

Copy the generated URL - you'll use this to invite your bot later.

## What You'll Need

From the Developer Portal, you need:

### Bot Token

Found in: **Bot** tab → **Token** section

```
Your token looks like:
MTIzNDU2Nzg5MDEyMzQ1Njc4OQ.GHIJK.aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890
```

Save this in your `.env` file:

```bash
BOT_TOKEN=your_token_here
```

### Client ID

Found in: **General Information** tab → **Application ID**

Used for:

- Generating invite URLs
- OAuth2 flows

### Client Secret

Found in: **OAuth2** tab → **Client Secret**

Usually not needed for basic bot deployment.

## Security Best Practices

### Token Storage

✅ **Do:**

- Store in `.env` file (git-ignored)
- Use environment variables
- Secure file permissions (600)
- Use secrets management in production

❌ **Don't:**

- Commit to Git
- Share publicly
- Hardcode in source
- Share in Discord/support channels

### Token Compromise

If your token is leaked:

1. **Immediately** reset token in Developer Portal
2. Update your `.env` file with new token
3. Restart your bot
4. Review recent bot activity for suspicious actions
5. Consider security review

### Regenerating Token

To reset your token:

1. Go to **Bot** tab
2. Click **"Reset Token"**
3. Confirm the action
4. Copy new token
5. Update your configuration
6. Restart bot

!!! warning "Old Token Stops Working"
    After resetting, the old token is immediately invalidated. Update your deployment before the bot goes offline!

## Permission Calculator

Use Discord's permission calculator to generate permission integers:

1. Visit **[Discord Permissions Calculator](https://discordapi.com/permissions.html)**
2. Select required permissions
3. Copy the permission integer
4. Use in invite URL: `&permissions=YOUR_NUMBER`

For Tux, recommended permissions integer: `1099511627775`

## Invite URL Template

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=1099511627775&scope=bot%20applications.commands
```

Replace `YOUR_CLIENT_ID` with your Application ID.

## Troubleshooting

### Can't Create Application

**Cause:** Account not verified or restrictions

**Solution:**

- Verify your email address
- Check account standing
- Try different browser

### Token Reset Doesn't Work

**Cause:** Browser cache or Discord issue

**Solution:**

- Hard refresh (Ctrl+Shift+R)
- Clear browser cache
- Try different browser
- Wait a few minutes and try again

### Bot Shows Offline After Token Reset

**Cause:** Didn't update `.env` with new token

**Solution:**

1. Copy new token from Developer Portal
2. Update `BOT_TOKEN` in `.env`
3. Restart bot: `docker compose restart tux`

### "Invalid Token" Error

**Cause:** Token is wrong, expired, or malformed

**Solution:**

- Verify token is copied correctly (no spaces)
- Check for extra characters
- Reset token and try again
- Verify it's the BOT token, not client secret

## Next Steps

Once you have your bot token:

1. **[Set Up Database](database.md)** - Configure PostgreSQL
2. **[Configure Environment Variables](environment-variables.md)** - Create `.env` file
3. **[Deploy Tux](../deployment/)** - Choose deployment method
4. Invite bot to your server using the OAuth2 URL

## Related Documentation

- **[Environment Variables](environment-variables.md)** - Using the bot token
- **[Security Best Practices](../security/token-security.md)** - Protecting your token
- **[Deployment Guide](../deployment/)** - Deploying Tux

---

**Next:** [Set up your database →](database.md)
