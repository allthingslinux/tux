---
title: Xkcd
description: Fetch and view comics from xkcd.com
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - fun
  - xkcd
---

# Xkcd

The `xkcd` command group allows users to browse and share comics from the popular [xkcd](https://xkcd.com) webcomic. It provides easy access to the latest comics, random selections, or specific items from the xkcd library, complete with the comic's title text (hover text) and navigation buttons.

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
```

**Aliases:**

- `xk`

## Subcommands

### latest

Fetches the most recently published xkcd comic.

- **Aliases:** `l`, `new`, `n`

### random

Fetches a random xkcd comic from the entire archive.

- **Aliases:** `rand`, `r`

### specific

Fetches an xkcd comic by its specific number/ID.

- **Parameters:**
  - `comic_id` (Type: `INTEGER`, Required): The ID of the comic you want to view.
- **Aliases:** `s`, `id`, `num`

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

## Response

When executed successfully, the bot sends an embed containing:

- The comic title and ID.
- The comic image.
- The "Alt Text" (description) of the comic.
- Buttons to view the comic on xkcd.com or visit the "Explain xkcd" page for context.

## Error Handling

### Error: Not Found

**When it occurs:** When a `comic_id` is provided that doesn't exist (e.g., too high or negative).

**Error message:**

```text
I couldn't find the xkcd comic. Please try again later.
```

## Related Commands

- [`/random`](random.md) - For other fun random tools.
