---
title: Ping
description: Check bot latency and system status
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - utility
  - status
---

# Ping

The `ping` command is used to check the bot's current connection status and retrieve essential system performance metrics. It provides real-time data on API latency, uptime, and resource usage, making it an ideal tool for verifying if the bot is healthy and responsive.

## Syntax

The `ping` command can be used in two ways:

**Slash Command:**

```text
/ping
```

**Prefix Command:**

```text
$ping
$status
```

**Aliases:**

You can also use these aliases instead of `ping`:

- `status`

## Usage Examples

### Check Bot Health

Quickly verify if the bot is responding and how fast its connection to Discord is.

```text
/ping
```

## Response Format

When executed, the bot returns an informational embed containing:

- **API latency** - The round-trip time in milliseconds for a heartbeat to reach Discord's gateway
- **Uptime** - How long the bot has been running since its last restart (formatted as human-readable duration)
- **CPU usage** - The percentage of CPU being utilized by the bot process
- **RAM usage** - The amount of memory currently consumed by the bot (formatted in MB or GB as appropriate)

## Permissions

### Bot Permissions

Tux requires the following permissions to execute this command:

- **Embed Links** - To display the performance metrics in a structured format.

### User Permissions

This command is available to all users.

## Related Commands

- [`/info`](../info/info.md) - For general server and member information
