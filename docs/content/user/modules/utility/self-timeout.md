---
title: Self-timeout
description: Voluntarily time yourself out for a specified duration
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - utility
  - distraction
---

# Self-timeout

The `self_timeout` command is a focus and productivity tool that allows you to voluntarily restrict your own access to the server. Once confirmed, Tux will apply a standard Discord timeout to your account, preventing you from sending messages or reacting for the duration you specify.

**Warning:** Once applied, the timeout **cannot** be removed early, even by server administrators. Use this tool carefully!

## Syntax

The `self_timeout` command is available as a hybrid command:

**Slash Command:**

```text
/self_timeout duration:STRING [reason:STRING]
```

**Prefix Command:**

```text
$self_timeout <duration> [reason]
```

**Aliases:**

- `sto`
- `stimeout`
- `selftimeout`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `duration`| STRING | Yes | How long to be timed out (e.g., `1h`, `1d`). Min: 5m, Max: 7d. |
| `reason`  | STRING | No | The reason for your self-timeout. Defaults to "No Reason." |

## Usage Examples

### Focus Hour

Time yourself out for one hour to focus on work or study.

```text
/self_timeout duration:1h reason:"Study session"
```

### Digital Detox

Take a longer break from the community.

```text
/self_timeout duration:2d reason:"Vacation"
```

## Confirmation Process

To prevent accidental timeouts, the bot follows a strict confirmation flow:

1. You run the command with your desired duration and optional reason.
2. Tux replies with a **confirmation message** explaining the consequences and showing your selected duration.
3. You must click the **Confirm** button within the response to proceed.
4. Once confirmed, the timeout is immediately applied and cannot be reversed early.

The confirmation message clearly states that the timeout cannot be removed early, even by administrators.

## Behavior Notes

- **AFK Integration:** Upon timing out, Tux will also set your status to AFK with the same reason.
- **DM Delivery:** The bot will attempt to send you a Direct Message confirming the start of your timeout.
- **Irreversibility:** The timeout is handled by Discord's native system and enforced by the bot's configuration; staff are instructed not to remove voluntary timeouts.

## Error Handling

### Invalid Duration

**When it occurs:** If the duration is less than 5 minutes or longer than 7 days.

**What happens:** The bot sends an error message indicating the duration is outside the allowed range.

**Solutions:**

- Choose a duration within the supported range (minimum: 5 minutes, maximum: 7 days)
- Use valid time units: `m` (minutes), `h` (hours), `d` (days), `w` (weeks)
- Examples of valid durations: `5m`, `1h`, `2d`, `1w`
- Combine units if needed (e.g., `1d12h` for 1 day and 12 hours)

## Related Commands

- [`/afk`](afk.md) - For a non-restrictive away status
- [`/timeout`](../moderation/timeout.md) - Administrative timeout command
