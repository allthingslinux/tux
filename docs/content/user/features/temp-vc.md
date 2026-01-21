---
title: Temp VC
description: Automatically create and manage temporary voice channels for users when they join a designated template channel.
tags:
  - user-guide
  - features
  - voice-channels
icon: lucide/mic
---

# Temp VC

Temp VC (Temporary Voice Channels) is a utility that allows users to create their own private or
group voice spaces on demand. Instead of having dozens of empty voice channels cluttering your
server, you provide a single "template" channel. When a user joins this template, Tux instantly
creates a new voice channel for them and moves them into it.

The system is completely self-managing. Channels are created only when needed and are automatically deleted as soon as the last person leaves. This keeps your voice channel list clean while giving users the flexibility to have their own space whenever they want.

## How It Works

### Mechanics

Tux monitors voice state changes to detect when a user enters the designated template channel.

- **Dynamic Creation:** Upon joining the template, Tux creates a new voice channel in the configured category.
- **Naming Convention:** New channels are automatically named `/tmp/[username]` to clearly identify them as temporary.
- **Permission Cloning:** The new channel inherits all permissions and settings from the template channel, allowing for easy configuration.
- **Smart Re-entry:** If a user already has a temporary channel and tries to create another, Tux simply moves them back to their existing channel.

### Automation

The system handles the entire lifecycle of a temporary channel:

- **Instant Movement:** Users are moved to their new channel immediately after joining the template.
- **Automatic Cleanup:** A background task constantly monitors temporary channels and deletes them the moment they become empty.
- **Category Management:** All temporary channels are kept within a specific category to keep the server organized.

### Triggers

The feature activates when:

- A user joins the designated template voice channel.
- The last user leaves a temporary voice channel.

## User Experience

### What Users See

From a user's perspective, the process is seamless:

- **Join to Create:** Users simply click on a voice channel named something like "Join to Create".
- **Instant Result:** They are immediately moved into a new channel named `/tmp/TheirName`.
- **Privacy/Control:** Since they are the "owner" (by name), they can invite others or use it for private conversations as configured by the template permissions.
- **Zero Cleanup:** When they are done, they just leave; the channel disappears on its own.

### Interaction

Users interact with this feature by:

1. Joining the server's designated template voice channel.
2. Using their temporary channel as they would any other voice channel.
3. Leaving the channel when finished.

## Configuration

Temp VC is configured through the server's `config.json` file.

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `TEMPVC_CHANNEL_ID` | `integer` \| `null` | The ID of the voice channel that acts as the "Join to Create" trigger. Strings are accepted and coerced to integer. |
| `TEMPVC_CATEGORY_ID` | `integer` \| `null` | The ID of the category where temporary channels will be created. Strings are accepted and coerced to integer. |

### Example Configuration

Unquoted integers (recommended) or quoted strings both work:

```json
{
  "TEMPVC": {
    "TEMPVC_CHANNEL_ID": 123456789012345678,
    "TEMPVC_CATEGORY_ID": 987654321098765432
  }
}
```

### Setup Steps

1. **Category Setup:** Create a new category (e.g., "Temporary Channels").
2. **Template Channel:** Create a voice channel inside that category (e.g., "➕ Create Channel").
3. **Permissions:** Configure the permissions on the template channel exactly how you want the temporary channels to look (e.g., bitrates, user limits).
4. **IDs:** Enable Discord Developer Mode and copy the IDs for both the channel and the category.
5. **Config:** Add these IDs to your `config.json` under the `TEMPVC` object.

!!! info "Configuration Guide"
    For detailed configuration instructions, see the [Admin Guide](../../admin/config/index.md).

## Permissions

### Bot Permissions

Tux requires the following permissions for this feature:

- **Manage Channels** - Needed to create and delete the temporary voice channels.
- **Move Members** - Needed to move users from the template to their new channel.
- **Connect** - Needed for the bot to see and manage the voice channels.
- **View Channel** - Needed to monitor the template and temporary channels.

### User Permissions

None required to use the feature. Users only need permission to join the template channel.

!!! info "Permission System"
    Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Troubleshooting

### Issue: Channels are not being created

**Symptoms:**

- A user joins the template channel but nothing happens.

**Causes:**

- The `TEMPVC_CHANNEL_ID` or `TEMPVC_CATEGORY_ID` is incorrect.
- Tux is missing "Manage Channels" or "Move Members" permission.
- The category has reached Discord's channel limit (50 channels per category).

**Solutions:**

1. Verify the IDs in your `config.json`.
2. Ensure Tux has the necessary permissions in both the category and the template channel.
3. Check if there are too many channels in the category.

### Issue: Users are not being moved

**Symptoms:**

- A new channel is created, but the user stays in the template channel.

**Causes:**

- Tux is missing the "Move Members" permission.
- The user's role is higher than Tux's role, and your server settings restrict moving them.

**Solutions:**

1. Grant Tux the "Move Members" permission.
2. Move Tux's role higher in the server's role hierarchy.

## Limitations

- **Discord Limits:** Each server is limited to a total of 500 channels, and each category is limited to 50.
- **Naming Pattern:** Temporary channels always follow the `/tmp/[username]` naming convention for identification and cleanup.
- **Single Channel:** A user can only have one temporary channel at a time; joining the template again will move them to their existing one.

## Related Documentation

- [Admin Configuration Guide](../../admin/config/index.md)
- [Permission Configuration](../../../admin/config/commands.md)
