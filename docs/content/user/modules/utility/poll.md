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

### Multiple-Choice Poll

Get feedback on several items.

```text
/poll title:"Favorite Linux Distro?" options:"Arch, Fedora, Debian, Ubuntu"
```

## Response Format

When executed, the bot creates a rich embed containing:

- **Poll title** - Your question or subject displayed prominently
- **Options list** - Each option numbered with emoji indicators (1️⃣, 2️⃣, 3️⃣, etc.)
- **Interactive reactions** - The bot automatically adds number emoji reactions to the message, allowing users to vote by clicking them

Users can vote by clicking the emoji reactions, and the vote count is visible in real-time.

## Error Handling

### Invalid Options Count

**When it occurs:** If you provide fewer than 2 or more than 9 options.

**What happens:** The bot sends an error message indicating the options count is invalid.

**Solutions:**

- Ensure your `options` string contains between 1 and 8 commas to separate 2-9 items
- Check that options are properly comma-separated (e.g., `"Option 1, Option 2, Option 3"`)
- Verify you haven't accidentally included extra commas or empty options

## Behavior Notes

- **Reaction Locking:** To maintain poll integrity, the bot may automatically remove reactions that do not correspond to the valid poll options.
- **Poll Banning:** Server moderators can restrict specific users from creating polls using the `pollban` feature.

## Related Commands

- [`/pollban`](../moderation/pollban.md) - Restrict a user from using the poll system
