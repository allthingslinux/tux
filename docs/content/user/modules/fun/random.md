---
title: Random
description: Generate random numbers, flip coins, roll dice, and ask the magic 8-ball
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - fun
  - random
---

# Random

The `random` command group provides various entertainment tools for generating random outcomes. Whether you need to settle a debate with a coin flip, decide on a number, or get a cryptic message from the magic 8-ball, these commands add an element of chance to your server interaction.

## Syntax

The `random` command can be used in two ways:

**Slash Command:**

```text
/random coinflip
/random dice [sides:INTEGER]
/random 8ball question:STRING [cow:true/false]
/random number [minimum:INTEGER] [maximum:INTEGER]
```

**Prefix Command:**

```text
$random coinflip
$random dice [sides]
$random 8ball <question> [-cow]
$random number [minimum] [maximum]
```

**Aliases:**

- `rand`

## Subcommands

### coinflip

Flip a virtual coin to get either "Heads" or "Tails".

- **Aliases:** `cf`

### dice

Roll a dice with a specified number of sides.

- **Parameters:**
  - `sides` (Type: `INTEGER`, Default: `6`): The number of sides on the dice. (Min: 2)
- **Aliases:** `d`

### 8ball

Ask the magic 8-ball a question and receive a random response.

- **Parameters:**
  - `question` (Type: `STRING`, Required): The question you want to ask.
  - `cow` (Type: `BOOLEAN`, Default: `false`): Whether to display the response in a cowsay format.
- **Aliases:** `eightball`, `8b`

### number

Generate a random integer between a minimum and maximum value.

- **Parameters:**
  - `minimum` (Type: `INTEGER`, Default: `0`): The lower bound.
  - `maximum` (Type: `INTEGER`, Default: `100`): The upper bound.
- **Aliases:** `n`

## Usage Examples

### Decision Making

Quickly settle a choice with a coin flip.

```text
/random coinflip
```

### Complex Dice Rolls

Roll a 20-sided dice for a game or activity.

```text
/random dice sides:20
```

### Cryptic Advice

Ask the magic 8-ball for its opinion on a matter.

```text
/random 8ball question:"Should I eat pizza?"
/random 8ball question:"Is it going to rain?" cow:true
```

### Random IDs or Numbers

Generate a number between 1 and 1000.

```text
/random number minimum:1 maximum:1000
```

## Response

When executed, the command returns the result in an embed or a code block (for 8ball cowsay).

- **Coinflip:** Returns "You got heads!" or "You got tails!".
- **Dice:** Returns an embed showing the roll result.
- **8ball:** Returns the response wrapped in ASCII art (Penguin or Cow).
- **Number:** Returns "Your random number is: X".

## Related Commands

- [`/xkcd`](xkcd.md) - View random comics.
