---
title: Temp VC
description: Automatically create and manage temporary voice channels for users when they join a designated template channel.
tags:
  - user-guide
  - features
  - voice-channels
---

# Temp VC

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

The Temporary Voice Channels feature automatically creates private voice channels for users when they join a designated template channel. These channels are automatically deleted when they become empty, providing an on-demand voice channel system.

## How It Works

When a user joins the configured template voice channel:

1. **Tux creates a new channel** named `/tmp/[username]` for that user
2. **The user is automatically moved** to their new temporary channel
3. **If a channel already exists** for that user, they're moved to it instead
4. **When channels become empty**, they're automatically deleted
5. **All empty temp channels** are cleaned up when someone leaves

## Key Features

### Automatic Channel Creation

- **On-demand creation** - Channels created only when needed
- **Per-user channels** - Each user gets their own channel
- **Reuses existing** - If a user's channel already exists, they're moved to it
- **Clones template** - New channels inherit settings from the template channel

### Automatic Cleanup

- **Deletes when empty** - Channels removed as soon as they're empty
- **Bulk cleanup** - All empty temp channels cleaned up when someone leaves
- **Prevents clutter** - Keeps your server organized automatically

### Channel Naming

- **Consistent naming** - All temp channels use `/tmp/[username]` format
- **Easy identification** - Channel name shows who owns it
- **Unique per user** - Each user gets one channel at a time

## Setting Up Temporary Voice Channels

### Prerequisites

Before setting up temporary voice channels:

1. **Create a category** for temporary voice channels
2. **Create a template voice channel** in that category
3. **Configure permissions** on the template channel
4. **Get channel and category IDs** for configuration

### Configuration

Temporary Voice Channels are configured through your server's configuration file.

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `tempvc_channel_id` | `string` | The template voice channel ID users join |
| `tempvc_category_id` | `string` | The category ID where temp channels are created |

### Example Configuration

```toml
[temp_vc]
# Template channel users join to create their temp channel
tempvc_channel_id = "123456789012345678"

# Category where temporary channels are created
tempvc_category_id = "987654321098765432"
```

## How It Works in Detail

### Joining the Template Channel

When a user joins the template channel:

1. **Tux checks** if a channel named `/tmp/[username]` already exists
2. **If it exists**, the user is moved to that existing channel
3. **If it doesn't exist**, a new channel is created by cloning the template
4. **User is moved** to their new or existing channel automatically

### Channel Creation

New channels are created by:

- **Cloning the template** - Inherits all settings from template channel
- **Naming convention** - Uses `/tmp/[username]` format
- **Same category** - Created in the configured category
- **Same permissions** - Inherits permissions from template

### Channel Deletion

Channels are deleted when:

- **User leaves** and the channel becomes empty
- **All users disconnect** from a temporary channel
- **Cleanup runs** when someone leaves any temp channel

### Cleanup Process

When a user leaves a temporary channel:

1. **Their channel is checked** - If empty, it's deleted
2. **All temp channels are scanned** - Empty channels are identified
3. **Empty channels are deleted** - Keeps the category clean
4. **Template channel is preserved** - Never deleted

## Use Cases

### Private Voice Channels

Provide users with private voice channels:

- **Personal spaces** - Each user gets their own channel
- **Privacy** - Users can invite specific people
- **Flexibility** - Channels created only when needed
- **No clutter** - Empty channels automatically removed

### Gaming Sessions

Perfect for gaming communities:

- **Quick setup** - Join template, get your channel instantly
- **Team organization** - Each team gets their own channel
- **Automatic cleanup** - No manual channel management needed

### Study Groups

Great for educational servers:

- **Study rooms** - Students get private study channels
- **Group work** - Multiple groups can work simultaneously
- **Clean organization** - Channels disappear when done

### Community Events

Useful for event organization:

- **Breakout rooms** - Create temporary discussion spaces
- **Event channels** - Temporary channels for specific events
- **Easy management** - No need to manually create/delete

## Behavior Details

### Naming Convention

All temporary channels follow this naming pattern:

- **Format**: `/tmp/[username]`
- **Example**: `/tmp/Alice` for user "Alice"
- **Case-sensitive** - Uses exact Discord username
- **Unique** - One channel per user at a time

### Template Channel

The template channel serves as:

- **Entry point** - Users join this to create their channel
- **Settings source** - New channels clone its settings
- **Preserved** - Never deleted or modified
- **Reference** - Used to create all temporary channels

### Permissions

Temporary channels inherit:

- **Category permissions** - From the category they're in
- **Template permissions** - From the template channel
- **User permissions** - Can be modified after creation
- **Role permissions** - Inherited from template

### Multiple Users

If multiple users want to use the same channel:

- **First user creates** - Channel created when first user joins template
- **Other users join** - Can join the existing channel manually
- **Channel persists** - Remains until all users leave
- **Owner-based** - Channel name reflects creator, but others can join

## Tips

!!! tip "Set Up Template Channel First"
    Configure your template channel with the exact settings you want temporary channels to have. All temp channels will inherit these settings.

!!! tip "Use a Dedicated Category"
    Create a category specifically for temporary voice channels. This keeps them organized and separate from your regular channels.

!!! tip "Configure Permissions Carefully"
    Set permissions on the template channel that you want all temp channels to have. Consider who should be able to join, speak, and manage channels.

!!! tip "Test the Setup"
    Join the template channel yourself to test that channels are created correctly. Make sure permissions and settings are as expected.

!!! tip "Monitor Channel Creation"
    Watch the category when users join to see channels being created. This helps verify everything is working correctly.

!!! warning "Channel Limits"
    Discord servers have limits on the number of voice channels. Make sure you don't exceed these limits if many users create channels simultaneously.

!!! warning "Permission Requirements"
    Tux needs "Manage Channels" and "Move Members" permissions to create and manage temporary voice channels. Without these permissions, the feature won't work.

## Troubleshooting

### Channels Not Being Created

If channels aren't being created:

1. **Check configuration** - Verify `tempvc_channel_id` and `tempvc_category_id` are set
2. **Verify permissions** - Tux needs "Manage Channels" and "Move Members"
3. **Check channel IDs** - Ensure IDs are correct (enable Developer Mode to copy)
4. **Verify category** - Make sure the category exists and is accessible
5. **Check logs** - Look for error messages in Tux's logs

### Channels Not Being Deleted

If empty channels aren't being deleted:

1. **Check channel name** - Must start with `/tmp/` to be recognized
2. **Verify category** - Channel must be in the configured category
3. **Check permissions** - Tux needs "Manage Channels" permission
4. **Verify empty** - Channel must have zero members to be deleted

### Users Not Being Moved

If users aren't being moved to their channels:

1. **Check permissions** - Tux needs "Move Members" permission
2. **Verify template channel** - User must join the correct template channel
3. **Check role hierarchy** - Tux's role must be above users' roles
4. **Verify bot status** - Ensure Tux is online and functioning

### Wrong Channel Settings

If temp channels have wrong settings:

1. **Check template channel** - Settings are cloned from template
2. **Modify template** - Change template channel settings
3. **Recreate channels** - Users need to recreate channels to get new settings
4. **Category settings** - Check category-level permissions

## For Administrators

### Setup Best Practices

1. **Create dedicated category** - Use a category specifically for temp channels
2. **Configure template channel** - Set up template with desired permissions
3. **Test thoroughly** - Test with different users and scenarios
4. **Monitor usage** - Watch how the feature is being used

### Template Channel Configuration

Recommended template channel settings:

- **Name**: Something like "Create Voice Channel" or "Join to Create"
- **Permissions**: Allow users to join and speak
- **User limit**: Set if you want to limit channel capacity
- **Bitrate**: Configure appropriate audio quality

### Category Setup

Recommended category settings:

- **Name**: "Temporary Channels" or "Private Voice"
- **Permissions**: Inherit from server or set specific rules
- **Position**: Place where it's easily accessible
- **Organization**: Keep separate from regular voice channels

### Permission Configuration

Key permissions to consider:

- **Join Voice**: Who can join temp channels
- **Speak**: Who can speak in temp channels
- **Manage Channels**: Who can modify temp channels
- **Move Members**: Required for Tux to move users

### Monitoring and Maintenance

Regular tasks:

- **Monitor channel creation** - Watch for unusual patterns
- **Check permissions** - Ensure permissions remain correct
- **Review usage** - See how many users are creating channels
- **Clean up manually** - If needed, manually delete stuck channels

### Channel Limits

Be aware of Discord limits:

- **Server limit**: 50 voice channels per server (Nitro: 200)
- **Category limit**: No specific limit per category
- **Concurrent channels**: Monitor active temp channels
- **Rate limits**: Discord may rate limit rapid channel creation
