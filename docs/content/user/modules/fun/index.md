---
title: Fun
description: Entertainment and fun commands for your Discord server
tags:
  - user-guide
  - modules
  - fun
icon: lucide/dices
---

# Fun

The Fun module provides entertainment commands to add some fun and engagement to your Discord server. These commands are designed for casual use and community interaction.

These lighthearted commands help break the ice, generate conversation, or simply provide entertainment for your server members. They are safe for general use and require minimal permissions, making them perfect for building community spirit.

## Command Groups

This module includes the following command groups:

### Random

The `/random` command group provides various randomization methods for making decisions or generating random content.

**Commands:**

- `/random coinflip` - Flip a virtual coin (heads or tails)
- `/random dice` - Roll dice with customizable sides
- `/random 8ball` - Get a magic 8-ball prediction
- `/random number` - Generate a random number within a range

### XKCD

The `/xkcd` command group allows you to view and share XKCD webcomics with interactive features.

**Commands:**

- `/xkcd latest` - View the most recent XKCD comic
- `/xkcd random` - Get a random XKCD comic
- `/xkcd specific` - View a specific comic by ID

## Commands

| Command | Aliases | Description | Documentation |
|---------|---------|-------------|---------------|
| `/random` | `rand` | Get random numbers, choices, or other random content | [Details](random.md) |
| `/xkcd` | `xk` | View XKCD comics | [Details](xkcd.md) |

## Common Use Cases

### Making Random Decisions

Use random commands to make decisions or add an element of chance to your server interactions.

**Steps:**

1. Use `/random coinflip` to quickly decide between two options.
2. Use `/random dice` with custom sides for games or activities.
3. Use `/random 8ball` to get a fun response to a question.

**Example:**

```text
/random coinflip
/random dice sides:20
/random 8ball question:"Should we order pizza?"
```

### Viewing and Sharing Comics

Share XKCD comics with your community, with easy access to explanations and original links.

**Steps:**

1. Use `/xkcd latest` to view the most recent comic.
2. Use `/xkcd random` to discover a random comic from the archive.
3. Use `/xkcd specific comic_id:1234` to view a specific comic by its number.
4. Use the provided buttons to view the comic's explanation or visit the original xkcd page.

**Example:**

```text
/xkcd latest
/xkcd random
/xkcd specific comic_id:1024
```

## Permissions

### Bot Permissions

Tux requires the following permissions for this module:

- **Send Messages** - Required for command responses
- **Embed Links** - Required for displaying XKCD comics and random outputs

### User Permissions

Fun commands are available to all users by default.

!!! tip "Permission System"
    Tux uses a dynamic permission system. Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Related Documentation

- [Permission Configuration](../../../admin/config/commands.md)
- [Admin Configuration Guide](../../../admin/config/index.md)
