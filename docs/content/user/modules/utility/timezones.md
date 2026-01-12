---
title: Timezones
description: View current times across the globe
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - utility
  - time
---

# Timezones

The `timezones` command is an interactive tool for checking current times in different regions of the world. It’s designed to help community members coordinate across various continents by providing an easy-to-navigate menu of major cities and their current local times.

## Syntax

The `timezones` command is available as a hybrid command:

**Slash Command:**

```text
/timezones
```

**Prefix Command:**

```text
$timezones
$tz
```

**Aliases:**

You can also use these aliases instead of `timezones`:

- `tz`

## Usage Examples

### Open Timezone Menu

Launch the interactive timezone browser.

```text
/timezones
```

## Dashboard/Interface

When you run the command, Tux opens an interactive dashboard with the following features:

- **Continent selection** - A dropdown menu allows you to switch between North America, South America, Europe, Africa, Asia, and Australia/Oceania
- **Real-time display** - Shows the current hour and minute in both 24-hour (`14:30`) and 12-hour (`02:30 PM`) formats
- **UTC offsets** - Clearly displays the offset from Coordinated Universal Time (e.g., `UTC-05:00`)
- **Visual cues** - Uses flag emojis to identify countries and regions quickly
- **City listings** - Displays major cities within each continent with their current local times

## Navigation

- **Select continent:** Use the dropdown menu to jump to a specific global region
- **Paging:** If a continent has many entries, use the **Next** and **Back** buttons to browse through them
- **End session:** Click the red **End Session** button to close the menu and clear the interactive components
- **Session timeout:** The dashboard automatically closes after a period of inactivity

## Related Commands

- [`/ping`](ping.md) - To see the bot's current uptime and system time status
