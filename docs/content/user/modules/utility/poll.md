---
title: Poll
description: Create interactive community polls
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - utility
  - poll
---

# Poll

The `poll` command provides an easy way to gather community feedback through interactive reaction voting.

Whether you're deciding on server changes, choosing a game to play, or just gauging interest in a topic, the poll command creates a clean, professional-looking interface for server members to cast their votes.

## Syntax

The `poll` command is **only available as a slash command**:

**Slash Command:**

```text
/poll title:STRING options:STRING
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | STRING | Yes | The question or subject of your poll. |
| `options` | STRING | Yes | A comma-separated list of options (Min: 2, Max: 9). |

## Usage Examples

### Simple Two-Option Poll

Decide between two choices.

```text
/poll title:"Should we add a new channel?" options:"Yes, No"
```

### Multiple Choice Poll

Get feedback on several items.

```text
/poll title:"Favorite Linux Distro?" options:"Arch, Fedora, Debian, Ubuntu"
```

## Response

When executed, the bot creates a rich embed highlighting the poll title and listing the options next to number emojis (1️⃣, 2️⃣, etc.). The bot then automatically adds these number emojis as reactions to the message, allowing users to click them to vote.

## Error Handling

### Error: Invalid Options Count

**When it occurs:** If you provide fewer than 2 or more than 9 options.

**Error message:**

```text
Poll options count needs to be between 2-9, you provided X options.
```

**Solution:** Ensure your `options` string contains between 1 and 8 commas to separate 2-9 items.

## Behavior Notes

- **Reaction Locking:** To maintain poll integrity, the bot may automatically remove reactions that do not correspond to the valid poll options.
- **Poll Banning:** Server moderators can restrict specific users from creating polls using the `pollban` feature.

## Related Commands

- [`/pollban`](../moderation/pollban.md) - Restrict a user from using the poll system.
