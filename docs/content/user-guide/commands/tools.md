# Tools

Reference and lookup commands for finding information quickly.

## Commands

### TLDR

Show simplified man pages (Too Long; Didn't Read).

**Usage:**

```bash
$tldr ls
$tldr tar
$tldr command_name
```bash

**Parameters:**

- `command` (required) - Command to look up

**Aliases:** `man`

**Permission:** Rank 0 (Everyone)

**Features:**

- Simplified command documentation
- Common use cases
- Example commands
- Faster than full man pages

**Example:**

```bash
$tldr tar
```bash

Shows common tar usage examples instead of the full manual.

---

### Wolfram

Query Wolfram|Alpha for computations and information.

**Usage:**

```bash
/wolfram query:"integrate x^2"
/wolfram query:"population of France"
$wolfram integrate x^2
```bash

**Parameters:**

- `query` (required) - Question or computation

**Permission:** Rank 0 (Everyone)

**Use Cases:**

- Mathematical calculations
- Unit conversions
- Scientific queries
- General knowledge questions
- Symbolic math

**Examples:**

```bash
/wolfram query:"derivative of sin(x)"
/wolfram query:"100 USD to EUR"
/wolfram query:"weather in London"
```bash

**Note:** Returns image result from Wolfram|Alpha API.

---

### Wiki

Search Arch Linux Wiki or All Things Linux Wiki for articles.

**Usage:**

```bash
/wiki arch query:"systemd"
/wiki atl query:"discord"
$wiki arch systemd
$wiki atl discord
```bash

**Parameters:**

- `arch` or `atl` (required) - Wiki source to search
- `query` (required) - Search term

**Permission:** Rank 0 (Everyone)

**Features:**

- Arch Linux Wiki search for technical documentation
- All Things Linux Wiki search for community content
- Article summaries and links
- Disambiguation handling

**Examples:**

```bash
/wiki arch query:"systemd"
/wiki atl query:"discord"
```bash

Shows relevant wiki articles from the specified source.

---

## Permission Requirements

| Command | Minimum Rank | Typical Role  |
|---------|-------------|----------------|
| tldr    | 0           | Everyone       |
| wolfram | 0           | Everyone       |
| wiki    | 0           | Everyone       |

## Common Use Cases

### Learning Commands

```bash
$tldr git                           # Quick git reference
$tldr docker                        # Docker cheat sheet
$tldr systemctl                     # Systemd service management
```bash

### Quick Calculations

```bash
/wolfram query:"50 kilograms to pounds"
/wolfram query:"solve x^2 + 5x + 6 = 0"
/wolfram query:"integral of e^x"
```bash

### Quick Lookups

```bash
/wiki query:"GNU"
/wiki query:"Package manager"
/wiki query:"Shell scripting"
```bash

## Tips

!!! tip "TLDR is Fast"
    TLDR gives you what you need without scrolling through full man pages!

!!! tip "Wolfram for Math"
    Wolfram|Alpha is excellent for math, physics, and scientific queries.

!!! tip "Wiki for Context"
    Use wiki when you need background on a topic quickly.

!!! tip "Combine with Snippets"
    Save common TLDR results as snippets for instant access!

## Troubleshooting

### TLDR "Not Found"

**Cause:** Command not in TLDR database

**Solution:**

- Try `man command` in your terminal instead
- Check spelling
- Command might be too niche for TLDR

### Wolfram API Error

**Cause:** API limit reached or query malformed

**Solution:**

- Wait a moment and try again
- Simplify your query
- Check query syntax

### Wiki No Results

**Cause:** Ambiguous query or typo

**Solution:**

- Be more specific
- Check spelling
- Try different search terms

## External Resources

- **[TLDR Pages](https://tldr.sh/)** - TLDR project website
- **[Wolfram|Alpha](https://www.wolframalpha.com/)** - Wolfram|Alpha website
- **[Wikipedia](https://www.wikipedia.org/)** - Wikipedia

## Related Commands

- **[Info Commands](info.md)** - Discord object information
- **[Utility Commands](utility.md)** - General utilities

---

**Next:** Learn about [Code Execution](code-execution.md) for running code snippets.
