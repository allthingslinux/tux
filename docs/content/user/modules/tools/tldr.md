---
title: TLDR
description: Access quick command-line reference pages
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - tools
  - help
---

# TLDR

The `tldr` command provides a collaborative cheat sheet for console commands. It's designed to give you exactly what you need: common usage examples for popular CLI tools (like `git`, `tar`, `docker`) without having to read through lengthy `man` pages.

It pulls data from the global [tldr-pages](https://tldr.sh) project, offering interactive navigation and support for multiple operating systems and languages.

## Syntax

The `tldr` command can be used in two ways:

**Slash Command:**

```text
/tldr command:STRING [platform:STRING] [language:STRING] [show_short:BOOLEAN] [show_long:BOOLEAN] [show_both:BOOLEAN]
```

**Prefix Command:**

```text
$tldr <command> [-platform PLATFORM] [-language LANG] [-short] [-long] [-both]
```

**Aliases:**

- `man`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `command` | STRING | Yes | The CLI command to look up (e.g., `tar`, `grep`). |
| `platform`| STRING | No | OS platform (e.g., `linux`, `osx`, `windows`, `common`). |
| `language`| STRING | No | Language code (e.g., `en`, `es`, `fr`). |

## Flags (Prefix Command)

This command supports flags for choosing display modes:

- `-platform`: Specify a preferred OS platform.
- `-language`: Choose a specific language.
- `-short`: Display short-form options.
- `-long`: Display long-form options (Default).
- `-both`: Show both short and long options.

## Usage Examples

### Quick Reference

Get the most common usage examples for `tar`.

```text
/tldr command:"tar"
```

### Platform Specific

Look up `git` specifically for the Linux platform.

```text
/tldr command:"git" platform:"linux"
```

### Multilingual Support

View the page in Spanish.

```text
/tldr command:"ls" language:"es"
```

## Response

The bot returns an embed with the command's description and a list of common usage examples.

- **Paging:** If the content is long, you can use the interactive buttons at the bottom of the embed to navigate through multiple pages.
- **Copy-Paste Ready:** All examples are formatted in code blocks for easy copying to your terminal.

## Related Commands

- [`/wiki arch`](../utility/wiki.md) - For deep technical documentation on Linux tools.
