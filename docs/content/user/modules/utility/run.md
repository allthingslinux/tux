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
<!-- markdownlint-disable MD013 MD040 -->
# Run

The `run` command allows users to execute code snippets directly within Discord. By integrating with high-performance online compilers like Godbolt and Wandbox, Tux can compile and run code in over 25 programming languages, returning the standard output or compiler errors in a clean format.

## Syntax

The `run` command is available as a prefix command:

**Prefix Command:**

```text
$run <code_block>
```

**Aliases:**

- `compile`
- `exec`

## Usage Examples

### Running Code Directly

Paste your code within triple backticks, specifying the language for syntax highlighting and compiler selection.

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

## Response

The bot returns an embed containing:

- **Source Code:** The code that was executed (for reference).
- **Output:** The standard output (stdout) or standard error (stderr) from the compiler/runner.
- **Service Info:** A link to the service used (Godbolt or Wandbox).

The response includes a **"Close"** button allowing the user to delete the output once they are finished.

## Error Handling

### Error: Missing Code

**When it occurs:** If the command is used without a code block or a valid message reference.

**Solution:** Ensure your code is wrapped in ` ```lang ` backticks.

### Error: Unsupported Language

**When it occurs:** If the language identifier used in the backticks is not recognized.

**Solution:** Check `$langs` for the correct identifier (e.g., use `py` or `python`).

## Behavior Notes

- **Isolation:** Code is executed in a sandboxed environment provided by external APIs.
- **Time Limits:** There is a strict execution time limit (typically few seconds) to prevent infinite loops.
- **Output Truncation:** Long outputs are truncated to fit within Discord's embed limits.

## Related Commands

<!-- markdownlint-disable MD042 -->
- [`$languages`](#) - List all supported programming languages.
- [`/tldr`](../tools/tldr.md) - For quick CLI command reference.
