---
title: Remindme
description: Set personal reminders for a future time
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - utility
  - reminders
---

# Remindme

The `remindme` command is a personal productivity tool that allows you to set timed notifications. It's perfect for keeping track of tasks, meetings, or any event you don't want to forget. The bot will send you a Direct Message (DM) when the specified time has elapsed.

## Syntax

The `remindme` command can be used in two ways:

**Slash Command:**

```text
/remindme time:STRING reminder:STRING
```

**Prefix Command:**

```text
$remindme <time> <reminder>
```

**Aliases:**

- `remind`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `time` | STRING | Yes | The duration until the reminder (e.g., "10m", "1h", "1d"). |
| `reminder` | STRING | Yes | The message you want to be reminded of. |

### Supported Time Formats

You can use shorthand for time units:

- `s` - Seconds
- `m` - Minutes
- `h` - Hours
- `d` - Days
- `w` - Weeks

Examples: `30m`, `2h`, `1d12h`, `500s`.

## Usage Examples

### Short Term Reminder

Set a reminder for a quick task.

```text
/remindme time:10m reminder:"Take the laundry out"
```

### Long Term Planning

Set a reminder for next week.

```text
/remindme time:1w reminder:"Submit the project report"
```

## Response Format

When you set a reminder, the bot confirms with a message like:
`✅ OK! I will remind you about "Take the laundry out" in 10 minutes.`

When the time expires, Tux sends you a **Direct Message** containing your reminder text. The DM includes the original reminder message and indicates when it was set.

## Error Handling

### Invalid Time Format

**When it occurs:** If the time format is not recognized, is set to zero, or contains invalid characters.

**What happens:** The bot sends an error message indicating the time format is invalid.

**Solutions:**

- Ensure you use the correct format with valid time units (e.g., `10m`, `1h`, `2d`)
- Use shorthand for time units: `s` (seconds), `m` (minutes), `h` (hours), `d` (days), `w` (weeks)
- Combine units if needed (e.g., `1d12h` for 1 day and 12 hours)
- Make sure the duration is greater than zero

## Behavior Notes

- **DMs required:** Ensure you have Direct Messages enabled from server members, otherwise the bot will be unable to deliver your reminder
- **Persistence:** Reminders are stored in the database and will be delivered even if the bot restarts
- **Time accuracy:** Reminders are delivered based on the time you set, accounting for the bot's system clock

## Related Commands

- [`/afk`](afk.md) - For status management while away
