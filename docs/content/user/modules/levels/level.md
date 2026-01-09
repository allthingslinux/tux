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

## Response

The bot returns a rank card (as an embed) containing:

- **Total XP:** Your lifetime experience points in this server.
- **Current Level:** Your current level milestone.
- **Progress Bar:** A visual indicator (`▰▰▰▱▱`) showing progress to the next level.
- **XP Required:** The specific amount of XP needed for the next level up.

If you have reached the maximum configured level, the progress bar will indicate that the limit has been reached.

## Behavior Notes

- **XP Generation:** XP is earned by sending messages in non-blacklisted channels.
- **Cooldowns:** There is a short cooldown between messages that grant XP to prevent spamming.
- **Role Rewards:** Reaching certain levels may automatically grant you specific roles configured by the server administrators.

## Related Commands

- [`/levels`](levels.md) - Administrative XP and level management.
