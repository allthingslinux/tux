---
title: Snippets
description: List and search for snippets in the server
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - snippets
---

# Snippets

The `snippets` command provides a directory of all snippets and aliases currently stored in the server. It allows users to browse the library through a paginated interface, helping them discover available resources and check usage statistics.

## Syntax

The `snippets` command is available as a prefix command:

**Prefix Command:**

```text
$snippets [search_query:STRING]
```

**Aliases:**

- `ls`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search_query` | STRING | No | Filter the list by name or content. |

## Usage Examples

### List All Snippets

Browse the entire library.

```text
$snippets
```

### Search for Specific Snippets

Find snippets related to "python".

```text
$snippets python
```

## Response

When executed, Tux returns a paginated embed showing:

- **Snippet Name:** The unique identifier for the snippet.
- **Usage Count:** How many times the snippet has been invoked.
- **Status Indicators:**
  - 🔒 - Indicates the snippet is locked.
  - → - Indicates the snippet is an alias.

## Behavior Notes

- **Sorting:** Snippets are sorted by their usage count in descending order, showing the most popular snippets first.
- **Pagination:** Use the interactive buttons to navigate through 30 snippets per page.

## Related Commands

- [`$snippet`](snippet.md) - Retrieve a specific snippet from the list.
- [`$snippetinfo`](snippetinfo.md) - Get more details about a specific snippet.
