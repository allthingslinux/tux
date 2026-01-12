---
title: AFK
description: Set an "Away From Keyboard" status
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - utility
  - afk
---

# AFK

The `afk` command allows you to notify other server members that you are currently unavailable. When you set an AFK status, the bot will automatically inform anyone who mentions you that you are away, along with an optional reason.

Your AFK status is automatically cleared the next time you send a message in the server, unless you use the `permafk` version.

## Syntax

The `afk` command can be used in two ways:

**Slash Command:**

```text
/afk [reason:STRING]
/permafk [reason:STRING]
```

**Prefix Command:**

```text
$afk [reason]
$permafk [reason]
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `reason` | STRING | No | The reason you are away (e.g., "Lunch", "Sleeping"). Defaults to "No reason." |

## Usage Examples

### Standard AFK

Set your status before stepping away. It will clear when you return and type a message.

```text
/afk reason:"At the gym"
```

### Permanent AFK

Set a status that persists even if you send messages. Useful for long-term unavailability.

```text
/permafk reason:"Away for the weekend"
```

## Response Format

When you set your AFK status, the bot confirms with a message like:
`😴 || You are now afk! Reason: At the gym`

When another user mentions you while you are AFK, the bot automatically replies to their message:
`[User] is AFK: At the gym (X minutes ago)`

The AFK notification shows your username, the reason you set, and how long ago you went AFK.

## Behavior Notes

- **Auto-clear:** Your AFK status is automatically removed as soon as you send a message in any channel where the bot can see it
- **Permanent AFK:** Using `/permafk` sets a status that persists even when you send messages - useful for long-term unavailability
- **Mentions:** The bot only triggers the AFK notification when you are explicitly mentioned (pinged) by another user
- **Nicknames:** Depending on server settings, the bot may prepend `[AFK]` to your server nickname while you are away
- **Server-specific:** AFK status is per-server, so you can have different AFK statuses in different servers

## Related Commands

- [`/clearafk`](../moderation/clearafk.md) - Administrative tool to clear another user's AFK status
- [`/remindme`](remindme.md) - Set personal reminders for future tasks
