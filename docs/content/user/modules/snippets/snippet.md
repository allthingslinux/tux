---
title: Snippet
description: Retrieve and use stored code snippets
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - snippets
---

# Snippet

The `snippet` command is the primary way to access and share stored pieces of text or code within the server. By providing a snippet's name, the bot will instantly reply with the saved content. This is ideal for sharing frequently used links, code blocks, or canned responses.

## Syntax

The `snippet` command is available as a prefix command:

**Prefix Command:**

```text
$snippet <name>
```

**Aliases:**

- `s`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | STRING | Yes | The name of the snippet you want to retrieve. |

## Usage Examples

### Retrieve a Snippet

Get the content of a snippet named `guide`.

```text
$snippet guide
```

### Using Aliases

Quickly access a snippet using the shorthand alias.

```text
$s guide
```

## Response Format

When executed, Tux replies to your message with the snippet's content. If the snippet is an alias, Tux automatically resolves it and shows the content of the target snippet, while indicating the alias relationship.

If the content exceeds Discord's message limit, the bot provides the content in a paginated interface or splits it across multiple messages.

## Behavior Notes

- **Usage tracking:** Each time a snippet is used, its usage counter increments (visible in `$snippets` and `$snippetinfo`)
- **Replies:** The bot preserves context by replying to your message
- **Allowed mentions:** Snippets are sent with restricted mentions to prevent accidental @everyone or role pings
- **Alias resolution:** If you use an alias, it resolves to the target snippet and increments the target's usage count
- **Broken aliases:** If an alias points to a deleted snippet, the bot automatically cleans it up when you try to use it

## Related Commands

- [`$snippets`](snippets.md) - List all available snippets in the server
- [`$createsnippet`](createsnippet.md) - Create a new snippet or alias
- [`$snippetinfo`](snippetinfo.md) - View detailed information about a snippet
