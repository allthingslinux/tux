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

## Response

When you set a reminder, the bot confirms:
`✅ OK! I will remind you about "Take the laundry out" in 10 minutes.`

When the time is up, Tux will send you a **Direct Message** with your reminder content.

## Error Handling

### Error: Invalid Time

**When it occurs:** If the time format is not recognized or is set to zero.

**Solution:** Ensure you use the correct format like `10m` or `1h`.

## Behavior Notes

- **DMs Required:** Ensure you have Direct Messages enabled from server members, otherwise the bot will be unable to deliver your reminder.
- **Bot Restarts:** Reminders are typically persistent and will be delivered even if the bot restarts.

## Related Commands

- [`/afk`](afk.md) - For status management while away.
