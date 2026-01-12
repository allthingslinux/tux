---
title: Level
description: View your current level and XP progress
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - levels
  - xp
---

# Level

The `level` command allows users to check their progress within the server's leveling system. It displays your current level, the total amount of XP you have earned, and a visual progress bar showing how close you are to reaching the next level milestone.

Users can also use this command to check the rank and progress of other community members.

## Syntax

The `level` command can be used in two ways:

**Slash Command:**

```text
/level [member:USER]
```

**Prefix Command:**

```text
$level [member]
```

**Aliases:**

- `lvl`
- `rank`
- `xp`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member` | USER | No | The member whose level and XP you want to view. Defaults to yourself. |

## Usage Examples

### Check Your Own Rank

View your current standing and progress.

```text
/level
```

### Check Someone Else's Progress

See the level and XP of another member.

```text
/level member:@User
```

## Response Format

The bot returns a rank card (as an embed) containing:

- **Member name and avatar** - Displayed in the embed author
- **Current level** - Your current level milestone shown in the title
- **Progress bar** - A visual indicator (e.g., `▰▰▰▱▱`) showing progress to the next level (if progress display is enabled)
- **Total XP** - Your lifetime experience points in this server, shown in the footer

If you have reached the maximum configured level, the XP display will indicate that the limit has been reached. The embed format may vary slightly depending on server configuration (progress bars can be enabled or disabled).

## How XP Works

- **XP generation:** XP is earned by sending messages in non-blacklisted channels
- **Cooldowns:** There is a configurable cooldown between messages that grant XP to prevent spamming
- **Role multipliers:** Some roles may provide XP multipliers, increasing the amount of XP you earn per message
- **Role rewards:** Reaching certain levels automatically grants you specific roles configured by server administrators
- **XP cap:** If configured, there may be a maximum level cap that limits how high you can progress

## Related Commands

- [`/levels`](levels.md) - Administrative XP and level management
- [XP & Leveling Feature](../../features/leveling.md) - Complete guide to the leveling system
