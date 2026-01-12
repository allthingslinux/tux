---
title: Wiki
description: Search specialized Linux and community wikis
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - utility
  - wiki
---

# Wiki

The `wiki` command group allows users to quickly search and retrieve links from specialized documentation sources, specifically for Linux and the local community. It streamlines the process of finding relevant articles by providing direct links and descriptions within Discord.

## Syntax

The `wiki` command can be used in two ways:

**Slash Command:**

```text
/wiki arch query:STRING
/wiki atl query:STRING
```

**Prefix Command:**

```text
$wiki arch <query>
$wiki atl <query>
$wk arch <query>
$wk atl <query>
```

**Aliases:**

You can also use these aliases instead of `wiki`:

- `wk`

## Subcommands

### arch

Searches the [Arch Linux Wiki](https://wiki.archlinux.org), the gold standard for Linux documentation.

- **Parameters:**
  - `query` (Type: `STRING`, Required): The term or article you are looking for.

### atl

Searches the [All Things Linux Wiki](https://atl.wiki), featuring community-specific guides and resources.

- **Parameters:**
  - `query` (Type: `STRING`, Required): The term or article you are looking for.

## Usage Examples

### Technical Support

Quickly find an Arch Linux Wiki article about a specific tool or configuration.

```text
/wiki arch query:"Systemd"
```

### Community Resources

Look up a community guide or policy on the ATL wiki.

```text
/wiki atl query:"Rules"
```

## Response Format

When a match is found, the bot returns a rich embed containing:

- **Article title** - The title of the matching wiki article
- **Description** - A brief snippet or description from the article
- **Direct link** - A clickable link to view the full article on the wiki website

The embed is formatted to make it easy to quickly identify relevant articles and access the full documentation.

## Error Handling

### No Results Found

**When it occurs:** When the search query does not match any existing articles.

**What happens:** The bot sends an error message indicating no results were found.

**Solutions:**

- Try different search terms or keywords
- Check spelling and try variations of your query
- Use more general terms if specific searches don't work
- Consider using `/tldr` for command-line documentation instead

## Related Commands

- [`/tldr`](../tools/tldr.md) - For quick command-line summaries
