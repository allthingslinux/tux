---
title: Bookmarks
description: Save important Discord messages for later reference by reacting with the bookmark emoji.
tags:
  - user-guide
  - features
  - bookmarks
---

# Bookmarks

Save important Discord messages by reacting with 🔖. Tux automatically sends a formatted copy to your DMs with all attachments, images, and context. Remove bookmarks by reacting with 🗑️ on the bookmark message in your DMs.

## How It Works

- Monitors reactions on all messages across servers
- When you react with 🔖, creates bookmark and sends to DMs
- Extracts content, attachments, and metadata
- Includes jump links, author info, and timestamps
- React with 🗑️ on bookmark messages in DMs to delete them

## User Experience

- React to any message with 🔖 to bookmark it
- Receive DM from Tux with formatted bookmark
- Up to 10 images included as attachments
- Jump link to view original message in context
- Remove bookmarks with 🗑️ reaction in DMs

## Configuration

No configuration required - works automatically once Tux is added to your server. Ensure you have DMs enabled with Tux to receive bookmarks.

## Commands

No commands - works entirely through Discord reactions.

## Permissions

**Bot Permissions:**

- Read Message History
- Read Messages
- Send Messages
- Embed Links
- Attach Files

**User Permissions:** None required (can bookmark messages in any accessible channel)

## Troubleshooting

**Not receiving bookmarks:**

- Check Discord privacy settings and enable DMs from server members
- Verify Tux is online and functioning
- Ensure you're using the correct emoji (🔖)

**Can't remove bookmarks:**

- React in your DMs, not in server channels
- React to the bookmark message sent by Tux
- Use the 🗑️ emoji

**Missing attachments:**

- Check if original attachment still exists
- Non-image attachments included as links in embed
- Only first 10 images included (Discord limit)

## Limitations

- Requires DMs enabled with Tux
- Discord limits messages to 10 attachments
- Very long messages may be truncated
- Complex embeds may not be fully recreated
- Interactive elements (buttons, menus) not included
