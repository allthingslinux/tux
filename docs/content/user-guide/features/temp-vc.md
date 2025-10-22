# Temporary Voice Channels

Automatically create and manage temporary voice channels for your community.

## What Are Temp VCs?

Temporary Voice Channels (Temp VCs) allow users to have their own private voice channels that are:

- **Auto-created** when joining a designated "creator" channel
- **Auto-deleted** when empty
- **User-controlled** (creator can manage their VC)
- **Temporary** (don't clutter your server)

## How It Works

### 1. Join Creator Channel

Server has a special voice channel (usually named "/tmp/" or similar) that acts as the creator.

### 2. Bot Creates Your VC

When you join the creator channel:

- Bot creates a new voice channel
- Named something like "/tmp/YourName"
- You're automatically moved to it
- You become the channel owner

### 3. Use Your VC

Your temporary channel:

- You can invite friends
- You control permissions
- Works like any voice channel
- Persists while in use

### 4. Auto-Cleanup

When everyone leaves:

- Channel sits empty briefly
- Bot automatically deletes it
- Keeps server organized
- No manual cleanup needed

## Setup

### For Administrators

Configure temp VC system:

1. **Create Creator Channel**
   - Create a voice channel (e.g., "/tmp/")
   - This is where users join to create temp VCs

2. **Configure in Tux**

   ```text
   # Configuration happens via config file or environment
   # See admin documentation for setup
   ```

3. **Set Permissions**
   - Ensure bot can create/delete channels
   - Set appropriate permissions for temp VCs

### Required Bot Permissions

- **Manage Channels** - Create/delete voice channels
- **Move Members** - Move users to created channels
- **View Channels** - See voice state changes

## For Users

### Creating Your VC

1. Join the designated creator channel (e.g., "/tmp/")
2. Bot creates your personal VC
3. You're auto-moved to it
4. Start talking!

### Managing Your VC

While in your temp VC, you can:

- Invite friends (they can join)
- Set channel name (right-click channel)
- Adjust permissions
- Set user limit

### Ending Your VC

Simply leave the channel:

- If others are still there, they can continue
- When everyone leaves, bot deletes it

## Configuration

### Base VC Name

The creator channel name pattern (default: "/tmp/"):

```python
base_vc_name = "/tmp/"
```

### Category

Temp VCs are created in the same category as the creator channel.

### Naming

New temp VCs are named: `{base_name}{username}`

Example: "/tmp/Alice"

## Use Cases

### Private Conversations

- Small group discussions
- Team meetings
- Study sessions
- Gaming parties

### Dynamic Events

- Breakout rooms for events
- Workshop groups
- Temporary teams
- Ad-hoc meetings

### Organization

- Keeps permanent channels clean
- No VC clutter
- Self-organizing system
- Scales automatically

## Best Practices

### For Server Admins

- **Clear Naming** - Use obvious creator channel name
- **Pin Instructions** - Pin message explaining how it works
- **Set Limits** - Prevent abuse with appropriate permissions
- **Monitor Usage** - Check for issues or abuse

### User Guidelines

- **Clean Up** - Leave when done so channel deletes
- **Don't Hoard** - Create when needed, not "just in case"
- **Respect Permissions** - Don't abuse channel control
- **Name Appropriately** - Keep channel names appropriate

## Tips

!!! tip "Automatic Cleanup"
    You don't need to worry about cleanup - bot handles it automatically!

!!! tip "Quick Access"
    Perfect for spontaneous voice chats without asking admin to create channels.

!!! tip "Permissions Persist"
    While your temp VC exists, you have control over it!

!!! info "Category Matters"
    Temp VCs inherit permissions from their category, so creator channel category matters!

## Troubleshooting

### VC Not Created

**Causes:**

- Bot missing "Manage Channels" permission
- Category full (max 50 channels)
- Bot offline

**Solutions:**

- Grant bot permission
- Clean up unused channels
- Contact admin

### Can't Move to VC

**Causes:**

- Bot missing "Move Members" permission
- VC permissions restrictive

**Solutions:**

- Grant bot permission
- Manually join the created VC

### VC Not Deleting

**Causes:**

- Bot offline when it became empty
- Permission issues

**Solutions:**

- Bot will clean up when back online
- Admin can manually delete if needed

## Admin Configuration

### For Self-Hosters

Configure in your config file:

```toml
[temp_vc]
enabled = true
base_vc_name = "/tmp/"
# Creator channel is determined by special naming
```

**See:** [Admin Configuration - Temp VC](../../admin-guide/configuration/features.md#temp-vc)

## Related Features

- **[Status Roles](status-roles.md)** - Auto-roles based on status
- **[GIF Limiter](gif-limiter.md)** - Channel management

---

**Next:** Learn about [Status Roles](status-roles.md) for automatic role assignment.
