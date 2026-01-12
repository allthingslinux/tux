---
title: XKCD
description: Fetch and view comics from xkcd.com
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - fun
  - xkcd
---

# XKCD

The `xkcd` command group allows you to browse and share comics from the popular [xkcd](https://xkcd.com) webcomic. It provides easy access to the latest comics, random selections, or specific items from the xkcd library, complete with the comic's title text (hover text) and navigation buttons.

## Syntax

The `xkcd` command can be used in two ways:

**Slash Command:**

```text
/xkcd [comic_id:INTEGER]
/xkcd latest
/xkcd random
/xkcd specific comic_id:INTEGER
```

**Prefix Command:**

```text
$xkcd [comic_id]
$xkcd latest
$xkcd random
$xkcd specific <comic_id>
$xk [comic_id]
$xk latest
$xk random
$xk specific <comic_id>
```

**Aliases:**

You can also use these aliases instead of `xkcd`:

- `xk`

When you use `/xkcd` with a comic ID directly (e.g., `/xkcd 1234`), it automatically fetches that specific comic, equivalent to using `/xkcd specific comic_id:1234`. Without any parameters, the command shows help information.

## Subcommands

### latest

Fetches the most recently published xkcd comic.

**Syntax:**

```text
/xkcd latest
$xkcd latest
$xkcd l
$xkcd new
$xkcd n
```

**Aliases:**

- `l`, `new`, `n`

### random

Fetches a random xkcd comic from the entire archive.

**Syntax:**

```text
/xkcd random
$xkcd random
$xkcd rand
$xkcd r
```

**Aliases:**

- `rand`, `r`

### specific

Fetches an xkcd comic by its specific number/ID.

**Syntax:**

```text
/xkcd specific comic_id:INTEGER
$xkcd specific <comic_id>
$xkcd s <comic_id>
$xkcd id <comic_id>
$xkcd num <comic_id>
```

**Parameters:**

- `comic_id` (Type: `INTEGER`, Required): The ID of the comic you want to view.

**Aliases:**

- `s`, `id`, `num`

## Usage Examples

### Viewing the Latest Comic

Catch up on the newest comic release.

```text
/xkcd latest
```

### Discovering Random Comics

Find a random comic to enjoy or share.

```text
/xkcd random
```

### Looking Up a Specific Comic

If you know the comic number (e.g., comic 1024), you can view it directly.

```text
/xkcd specific comic_id:1024
```

## Response Format

When executed successfully, the bot sends an embed containing:

- **Comic title and ID** - The comic number and title
- **Comic image** - The full comic image displayed in the embed
- **Alt text** - The comic's description (hover text) shown as a quote
- **Navigation buttons** - Interactive buttons to view the comic on xkcd.com or visit the "Explain xkcd" page for additional context

## Error Handling

### Comic Not Found

**When it occurs:** When a `comic_id` is provided that doesn't exist (e.g., a number that's too high, negative, or zero).

**What happens:** The bot sends an error embed with the message: "I couldn't find the xkcd comic. Please try again later."

**Solutions:**

- Verify the comic ID exists (xkcd comics start at 1)
- Try using `/xkcd latest` to see the current highest comic number
- Use `/xkcd random` to get a valid comic instead

## Related Commands

- [`/random`](random.md) - Generate random numbers, flip coins, roll dice, and ask the magic 8-ball
