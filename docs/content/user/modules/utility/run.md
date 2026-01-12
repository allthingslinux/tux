---
title: Run
description: Execute code snippets in various programming languages
icon: lucide/square-slash
tags:

- user-guide
- commands
- utility
- code
---

# Run

The `run` command allows users to execute code snippets directly within Discord. By integrating with high-performance online compilers like Godbolt and Wandbox, Tux can compile and run code in over 25 programming languages, returning the standard output or compiler errors in a clean format.

## Syntax

The `run` command is available as a prefix command:

**Prefix Command:**

```text
$run <code_block>
$compile <code_block>
$exec <code_block>
```

**Aliases:**

You can also use these aliases instead of `run`:

- `compile`
- `exec`

## Usage Examples

### Running Code Directly

Paste your code within triple backticks, specifying the language for syntax highlighting and compiler selection.

<!-- markdownlint-disable MD040 -->
```text
$run ```python
print("Hello from Tux!")
```

```

### Replying to Messages

You can execute code from another user's message by replying to it with the `$run` command. The bot will automatically extract the code within the first set of triple backticks.

```text
(User message contains a code block)
$run
```

## Supported Languages

Tux supports a wide variety of languages, including but not limited to:

- **C / C++ / C#**
- **Python / Javascript / Typescript**
- **Rust / Go / Swift**
- **Java / Kotlin / Scala**
- **Haskell / OCaml / Lisp**
- **Bash / SQL / PHP / Ruby**

Use the `$languages` command to see the full list of supported identifiers.

## Response Format

The bot returns an embed containing:

- **Source code** - The code that was executed (displayed for reference)
- **Output** - The standard output (stdout) or standard error (stderr) from the compiler/runner
- **Service info** - A link to the service used (Godbolt or Wandbox) for transparency
- **Language indicator** - Shows which language was detected and executed

The response includes a **Close** button allowing you to delete the output message once you're finished viewing it.

## Error Handling

### Missing Code

**When it occurs:** If the command is used without a code block or a valid message reference.

**What happens:** The bot sends an error message indicating no code was provided.

**Solutions:**

- Ensure your code is wrapped in triple backticks with a language specifier: ` ```python `
- If replying to a message, make sure the referenced message contains a code block
- Use the `$languages` command to see examples of proper code block formatting

### Unsupported Language

**When it occurs:** If the language identifier used in the backticks is not recognized.

**What happens:** The bot sends an error message listing supported languages.

**Solutions:**

- Use `$languages` or `$langs` to see the full list of supported language identifiers
- Use the correct identifier (e.g., `py` or `python` for Python, `js` or `javascript` for JavaScript)
- Check for typos in the language identifier

## Behavior Notes

- **Sandboxed execution:** Code is executed in a sandboxed environment provided by external APIs (Godbolt or Wandbox)
- **Time limits:** There is a strict execution time limit (typically a few seconds) to prevent infinite loops or resource exhaustion
- **Output truncation:** Long outputs are truncated to fit within Discord's embed limits - check the service link for full output if needed
- **Code extraction:** When replying to a message, the bot automatically extracts code from the first code block found in that message
- **Language detection:** The language is determined by the identifier in the code block's opening backticks

## Related Commands

- `$languages` (aliases: `$langs`, `$lang`) - List all supported programming languages
- [`/tldr`](../tools/tldr.md) - For quick CLI command reference
