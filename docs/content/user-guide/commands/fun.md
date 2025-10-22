# Fun Commands

Entertainment and random commands for your server.

## Commands

### Random

Generate random numbers, choices, or flip coins.

**Usage:**

```
/random choice "Option 1" "Option 2" "Option 3"
/random number 1 100
/random coin
```

**Permission:** Rank 0 (Everyone)

**Features:**

- Random choice from options
- Random number in range
- Coin flip (heads/tails)
- Dice roll
- And more random generators

**Examples:**

```
/random choice "Pizza" "Burgers" "Sushi"    # Pick one
/random number 1 6                           # Dice roll
/random coin                                 # Heads or tails
```

---

### XKCD

View XKCD comics.

**Usage:**

```
/xkcd                               # Random comic
/xkcd 353                           # Specific comic number
/xkcd latest                        # Latest comic
```

**Parameters:**

- `number` (optional) - Specific comic number, or "latest"/"random"

**Permission:** Rank 0 (Everyone)

**Features:**

- Browse XKCD comics
- Show comic image, title, and alt text
- Random comic selection
- Direct comic lookup

**Example:**

```
/xkcd 353                           # The famous "Python" comic
```

---

## Permission Requirements

| Command | Minimum Rank | Typical Role  |
|---------|-------------|----------------|
| random  | 0           | Everyone       |
| xkcd    | 0           | Everyone       |

## Usage Examples

### Making Decisions

```
/random choice "Yes" "No" "Maybe"
```

### Games

```
/random number 1 20                 # D20 roll for RPG
/random coin                        # Coin toss
```

### Entertainment

```
/xkcd                               # Random XKCD comic
```

## Tips

!!! tip "Comma-Separated Choices"
    For `/random choice`, separate options with spaces in quotes: `"Option 1" "Option 2"`

!!! tip "XKCD Explainer"
    Don't get the joke? Check [explainxkcd.com](https://www.explainxkcd.com/)!

## Related Commands

- **[Utility Commands](utility.md)** - Utility tools
- **[Tools](tools.md)** - Wiki, TLDR, and more

---

**Next:** Learn about [Tools](tools.md) for lookups and references.
