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

## Response Format

When executed, Tux returns a paginated embed showing:

- **Snippet name** - The unique identifier for the snippet
- **Usage count** - How many times the snippet has been invoked
- **Status indicators:**
  - 🔒 - Indicates the snippet is locked (only moderators can edit)
  - → - Indicates the snippet is an alias pointing to another snippet

## Behavior Notes

- **Sorting:** Snippets are sorted by usage count in descending order, showing the most popular snippets first
- **Pagination:** Use the interactive navigation buttons to browse through multiple pages (30 snippets per page)
- **Search:** When you provide a search query, results are filtered by snippet name or content (case-insensitive)
- **Empty results:** If no snippets match your search or none exist, you'll see an appropriate message

## Related Commands

- [`$snippet`](snippet.md) - Retrieve a specific snippet from the list.
- [`$snippetinfo`](snippetinfo.md) - Get more details about a specific snippet.
