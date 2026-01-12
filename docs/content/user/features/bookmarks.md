---
title: Bookmarks
description: Save important Discord messages for later reference by reacting with the bookmark emoji.
tags:
  - user-guide
  - features
  - bookmarks
icon: lucide/bookmark
---

# Bookmarks

Save important Discord messages by reacting with 🔖. Tux automatically sends a formatted copy to your
DMs with all attachments, images, and context, allowing you to build a personal library of valuable
information without cluttering server channels.

This feature works entirely in the background, monitoring message reactions and instantly providing you with a private, permanent record of the content you find most important.

## How It Works

### Mechanics

Tux monitors reaction events across all servers where it is present. When it detects a 🔖 reaction from a user, it triggers the bookmarking process.

- **Content Extraction:** Tux parses the original message to extract text, embeds, and metadata.
- **Attachment Handling:** The bot collects up to 10 images and other attachments to include in the DM.
- **Context Preservation:** Every bookmark includes a jump link to the original message, author information, and the original timestamp.

### Automation

This feature works automatically in the background:

- **Message Monitoring:** Tux listens for specific emoji reactions on all visible messages.
- **DM Delivery:** Once a bookmark is triggered, Tux instantly formats and sends the message to your DMs.
- **Cleanup Management:** Tux monitors reactions on the bookmark messages themselves to allow for easy removal.

### Triggers

The feature activates when:

- You react to any message in a server with the 🔖 emoji.
- You react with 🗑️ on a bookmark message in your DMs to delete it.

## User Experience

### What Users See

When you bookmark a message, you receive a formatted DM from Tux containing:

- **Author Info:** The name and avatar of the person who sent the original message.
- **Message Content:** The full text of the original message.
- **Attachments:** Images and files from the original message (up to Discord's limit).
- **Metadata:** The server and channel name where the message was found.
- **Navigation:** A "Jump to Message" link to view the original context.

### Interaction

Users interact with this feature by:

1. Reacting to a message with 🔖 to save it.
2. Checking their DMs for the formatted bookmark from Tux.
3. Reacting to the bookmark in their DMs with 🗑️ to remove it from their history.

## Configuration

No configuration is required for individual users. The feature works automatically for anyone in a server where Tux is present.

### User Requirements

1. **DMs Enabled:** You must allow direct messages from server members for Tux to send your bookmarks.
2. **Access:** You must have permission to see the message you are trying to bookmark.

!!! info "Configuration Guide"
    For detailed configuration instructions, see the [Admin Guide](../../admin/config/index.md).

## Permissions

### Bot Permissions

Tux requires the following permissions for this feature:

- **Read Message History** - Needed to access the content of the message being bookmarked.
- **Read Messages** - Needed to monitor for the bookmark reaction.
- **Send Messages** - Needed to send the bookmark to your DMs.
- **Embed Links** - Needed to create the formatted bookmark card.
- **Attach Files** - Needed to forward original attachments to your DMs.

### User Permissions

None required. Users can bookmark messages in any channel they can view.

!!! info "Permission System"
    Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Troubleshooting

### Issue: Not receiving bookmarks

**Symptoms:**

- Reacting with 🔖 does nothing.
- No DM is received from Tux.

**Causes:**

- Discord privacy settings are blocking DMs from server members.
- Tux does not have "Read Message History" permission in the channel.

**Solutions:**

1. Check your Discord privacy settings and enable DMs for the server.
2. Verify Tux is online and has access to the channel.

### Issue: Missing attachments

**Symptoms:**

- The bookmark arrives but is missing some or all images/files.

**Causes:**

- The original attachment was deleted from Discord.
- The message had more than 10 attachments (Discord's limit).

**Solutions:**

1. Verify the original message still has its attachments.
2. Check for links in the embed content which may contain non-image attachments.

## Limitations

- **DMs Required:** You must have DMs enabled to receive bookmarks.
- **Attachment Limit:** Discord limits messages to 10 attachments.
- **Truncation:** Very long messages may be truncated due to Discord embed character limits.
- **Interactive Elements:** Buttons, select menus, and other interactive components from the original message are not preserved.

## Related Documentation

- [Admin Configuration Guide](../../admin/config/index.md)
- [Permission Configuration](../../../admin/config/commands.md)
