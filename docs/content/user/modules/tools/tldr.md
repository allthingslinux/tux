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
$tldr <command> [-p PLATFORM] [-lang LANG] [-l LANG] [-short] [-long] [-both]
$man <command> [-platform PLATFORM] [-language LANG] [-short] [-long] [-both]
$man <command> [-p PLATFORM] [-lang LANG] [-l LANG] [-short] [-long] [-both]
```

**Aliases:**

You can also use these aliases instead of `tldr`:

- `man`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `command` | STRING | Yes | The CLI command to look up (e.g., `tar`, `grep`, `git-commit`). Use hyphens for multi-word commands. |
| `platform`| STRING | No | OS platform (e.g., `linux`, `osx`, `windows`, `common`, `android`, `freebsd`). |
| `language`| STRING | No | Language code (e.g., `en`, `es`, `fr`, `de`, `pt`, `zh`, `ja`). |
| `show_short`| BOOLEAN | No | Display short-form options only. |
| `show_long`| BOOLEAN | No | Display long-form options only (default). |
| `show_both`| BOOLEAN | No | Display both short and long options. |

## Flags (Prefix Command)

This command supports the following flags:

| Flag | Aliases | Type | Default | Description |
|------|---------|------|---------|-------------|
| `-platform` | `-p` | String | None | Specify a preferred OS platform (e.g., `linux`, `osx`, `windows`, `common`). |
| `-language` | `-lang`, `-l` | String | None | Choose a specific language code (e.g., `en`, `es`, `fr`). |
| `-show_short` | `-short` | Boolean | False | Display short-form options only. |
| `-show_long` | `-long` | Boolean | True | Display long-form options only (default). |
| `-show_both` | `-both` | Boolean | False | Show both short and long options. |

## Usage Examples

### Quick Reference

Get the most common usage examples for a command.

```text
/tldr command:tar
/tldr command:grep
```

### Multi-Word Commands

Look up commands with multiple words using hyphens.

```text
/tldr command:git-commit
/tldr command:git-status
/tldr command:docker-compose
```

### Platform Specific

Look up platform-specific examples for a command.

```text
/tldr command:git platform:linux
/tldr command:tar platform:osx
/tldr command:dir platform:windows
```

### Multilingual Support

View documentation in different languages.

```text
/tldr command:ls language:es
/tldr command:grep language:fr
/tldr command:tar language:de
```

### Display Options

Control how options are displayed (short-form, long-form, or both).

```text
/tldr command:tar show_short:true
/tldr command:git show_both:true
```

## Response Format

The bot returns an embed with the command's description and a list of common usage examples.

- **Command description** - Brief explanation of what the command does
- **Usage examples** - Common use cases with explanations, formatted in code blocks for easy copying
- **Interactive pagination** - If the content spans multiple pages, use the navigation buttons at the bottom to browse through all examples
- **Platform indicator** - Shows which platform the examples are for (if specified)
- **Language indicator** - Shows which language the page is in (if not English)

All examples are formatted in code blocks, making them ready to copy and paste directly into your terminal.

## Behavior Notes

- **Command normalization:** Multi-word commands are automatically normalized (e.g., `git commit` becomes `git-commit`)
- **Autocomplete:** The slash command provides autocomplete suggestions for commands, platforms, and languages
- **Caching:** TLDR pages are cached locally for faster access
- **Platform fallback:** If a platform-specific page isn't found, the bot falls back to the `common` platform
- **Language fallback:** If a language-specific page isn't available, the bot falls back to English

## Related Commands

- [`/wiki arch`](../utility/wiki.md) - For deep technical documentation on Linux tools
- [`/wiki`](../utility/wiki.md) - For general knowledge search
