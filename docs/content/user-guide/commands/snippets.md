# Snippet Commands

Snippets are reusable text templates for your server. Perfect for rules, FAQs, common responses, and more.

## What Are Snippets?

Snippets allow you to:

- Store frequently used text
- Share server rules quickly
- Provide consistent information
- Save time with common responses

## Basic Commands

### Create Snippet

Create a new snippet.

**Usage:**

```
$createsnippet name content here
```

**Parameters:**

- `name` (required) - Snippet name (single word)
- `content` (required) - Snippet content (rest of message)

**Aliases:** `cs`

**Permission:** Rank 3 (Moderator)

**Note:** Prefix-only command

**Example:**

```
$createsnippet rules Please read our rules in #rules before posting.
```

---

### Get Snippet

Use a snippet (shows its content).

**Usage:**

```
$snippet name
```

**Parameters:**

- `name` (required) - Snippet name

**Aliases:** `s`

**Permission:** Rank 0 (Everyone, unless snippet-banned)

**Example:**

```
$snippet rules
```

Output: The snippet content

---

### List Snippets

View all available snippets.

**Usage:**

```
$snippets
```

**Aliases:** `ls`

**Permission:** Rank 0 (Everyone)

**Shows:**

- Snippet names
- Creation date
- Creator
- Lock status

---

### Snippet Info

View detailed information about a snippet.

**Usage:**

```
$snippetinfo name
```

**Parameters:**

- `name` (required) - Snippet name

**Aliases:** `si`

**Permission:** Rank 0 (Everyone)

**Shows:**

- Snippet content
- Creator
- Creation date
- Last modified
- Usage count
- Lock status

---

## Management Commands

### Edit Snippet

Edit an existing snippet's content.

**Usage:**

```
$editsnippet name new content here
```

**Parameters:**

- `name` (required) - Snippet name
- `content` (required) - New content

**Aliases:** `es`

**Permission:** Rank 3 (Moderator)

**Note:** Can only edit unlocked snippets or your own snippets

**Example:**

```
$editsnippet rules Updated rules - see #rules for details
```

---

### Delete Snippet

Delete a snippet.

**Usage:**

```
$deletesnippet name
```

**Parameters:**

- `name` (required) - Snippet name to delete

**Aliases:** `ds`

**Permission:** Rank 3 (Moderator)

**Note:** Can only delete unlocked snippets or your own snippets

**Example:**

```
$deletesnippet outdated
```

---

### Toggle Snippet Lock

Lock or unlock a snippet to prevent editing.

**Usage:**

```
$togglesnippetlock name
```

**Parameters:**

- `name` (required) - Snippet name

**Aliases:** `tsl`

**Permission:** Rank 5 (Administrator)

**Notes:**

- Locked snippets can only be edited/deleted by admins
- Useful for protecting important snippets (rules, info)
- Toggle command - run again to unlock

**Example:**

```
$togglesnippetlock rules            # Lock the rules snippet
$togglesnippetlock rules            # Unlock it
```

---

## Permission Requirements

| Command          | Minimum Rank | Typical Role  |
|-----------------|-------------|----------------|
| snippet         | 0           | Everyone       |
| snippets        | 0           | Everyone       |
| snippetinfo     | 0           | Everyone       |
| createsnippet   | 3           | Moderator      |
| editsnippet     | 3           | Moderator      |
| deletesnippet   | 3           | Moderator      |
| togglesnippetlock| 5          | Administrator  |

## Common Use Cases

### Server Rules

```
$createsnippet rules Our server rules are in #rules. Please read and follow them!

# Usage:
$snippet rules
```

### FAQ Responses

```
$createsnippet linux-help For Linux help, try:
1. Man pages: man command
2. TLDR: /tldr command
3. Wiki: /wiki topic

# Usage:
$snippet linux-help
```

### Support Responses

```
$createsnippet support Please provide:
- Your OS and version
- Error messages
- Steps to reproduce
- Screenshots if applicable

# Usage:
$snippet support
```

### Welcome Messages

```
$createsnippet welcome Welcome to the server! Please:
1. Read #rules
2. Assign roles in #roles
3. Introduce yourself in #introductions

# Usage:
$snippet welcome
```

## Best Practices

### Naming

✅ **Good names:**

- `rules` - Clear and simple
- `linux-help` - Descriptive with hyphen
- `faq-audio` - Category prefix

❌ **Bad names:**

- `r` - Too short, unclear
- `the rules for the server` - Too long, has spaces
- `RULES!!!` - Special characters

### Content

✅ **Good content:**

- Clear and concise
- Well-formatted
- Links to relevant channels
- Action items or steps

❌ **Bad content:**

- Walls of text
- Unclear references
- Outdated information
- Overly long

### Organization

- Use prefixes for categories (`faq-`, `rule-`, `help-`)
- Lock important snippets
- Regularly review and update
- Delete unused snippets

## Snippet Restrictions

### Snippet Ban

Users can be banned from using snippets:

```
/snippetban @user reason:"Snippet abuse"
```

Banned users cannot:

- Use `$snippet`
- Create snippets
- Edit/delete snippets
- View snippet list

See [Moderation Commands](moderation.md#snippetban) for details.

## Tips

!!! tip "Prefix Only"
    All snippet commands use the prefix (`$`) not slash commands. This is by design for quick access.

!!! tip "Lock Important Ones"
    Lock snippets that shouldn't be changed (rules, important info) with `/togglesnippetlock`.

!!! tip "Use Snippets in Embeds"
    Snippet content can include Discord markdown for formatting!

!!! tip "Quick Access"
    Snippets are designed for fast access - just `$s name` for the short alias!

## Troubleshooting

### "Snippet not found"

**Cause:** Snippet doesn't exist or name typo

**Solution:**

- Check spelling: `$snippets` to list all
- Use exact name (case-sensitive)

### Can't Create Snippet

**Cause:** Insufficient permissions

**Solution:**

- Must be Rank 3+
- Check your roles: `/config role` (ask admin)

### Can't Edit/Delete Snippet

**Cause:** Snippet is locked or not yours

**Solution:**

- Check if locked: `$snippetinfo name`
- Ask admin to unlock: `/togglesnippetlock name`
- Admins can edit/delete any snippet

### Snippet Command Not Working

**Cause:** You're snippet-banned

**Solution:**

- Ask moderator to check: `/cases` for snippet ban
- Appeal to have ban removed: `/snippetunban`

## Related Features

- **[Bookmarks](../features/bookmarks.md)** - Personal message saving
- **[Moderation](moderation.md)** - Snippet ban/unban

---

**Next:** Learn about [Levels](levels.md) for XP and ranking.
