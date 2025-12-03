---
title: Bot Token Configuration
tags:
  - selfhost
  - configuration
  - bot-token
---

# Bot Token Configuration

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

Quick guide to get your Discord bot token configured for Tux.

## Getting Your Bot Token

1. **Visit Discord Developer Portal**:
   - Go to [discord.com/developers/applications](https://discord.com/developers/applications)
   - Log in with your Discord account

2. **Create New Application**:
   - Click "New Application"
   - Name it (e.g., "Tux Bot")
   - Click "Create"

3. **Add Bot User**:
   - Go to "Bot" section
   - Click "Add Bot" → "Yes, do it!"

4. **Copy Token**:
   - Click "Reset Token" to generate new token
   - Copy the token (keep it secret!)

## Required Bot Permissions

!!! warning "Admin Permissions Required"
    **Currently, Tux requires Administrator permissions** until we complete permission auditing and cleanup. We're working on reducing this to only necessary permissions.

**Give Tux the Administrator permission** when inviting the bot to your server.

!!! info "Permission Cleanup"
    We're actively working on identifying the exact permissions Tux needs. This will be updated in a future release.

## Environment Setup

Add to your `.env` file:

```env
# Required: Your Discord bot token
BOT_TOKEN=your_bot_token_here

# Optional: Bot owner Discord user ID (for admin commands)
USER_IDS__BOT_OWNER_ID=your_discord_user_id_here
```

!!! important "Keep Tokens Secret"
    - Never share your token
    - Don't commit it to version control
    - Use environment variables only

## Enable Privileged Intents

Tux uses all Discord intents for full functionality:

1. **Go to Bot Settings** → **Privileged Gateway Intents**
2. **Enable all three**:
   - Message Content Intent
   - Server Members Intent
   - Presence Intent

!!! warning "Verification Required"
    Bots in 100+ servers need Discord verification to use privileged intents.

## Invite Bot to Server

1. **Go to OAuth2** → **URL Generator**
2. **Select scopes**: `bot`, `applications.commands`
3. **Select permissions**: **Administrator** (required for now)
4. **Copy URL** and open it in browser
5. **Select your server** and authorize

## Test Your Setup

```bash
# Start the bot
tux run

# Test basic commands
/ping
```

## Common Issues

**Bot offline?**

- Check `BOT_TOKEN` is correct in `.env`
- Verify bot is invited to your server
- Check bot status: `tux status`

**Commands not working?**

- Ensure bot has **Administrator permission** (required for now)
- Check role hierarchy (bot role should be high enough)
- Try reinviting with correct scopes and permissions

**Token errors?**

- Token should be ~59 characters
- Regenerate if compromised
- No spaces or special characters

## Next Steps

Once your bot token is configured, you can set up your database.

[Database Setup](database.md){ .md-button }
