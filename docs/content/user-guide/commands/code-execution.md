# Code Execution

Run code snippets directly in Discord using Godbolt and Wandbox compilers.

## Commands

### Run

Execute code in various programming languages.

**Usage:**

**Aliases:** `compile`, `exec`

**Permission:** Rank 0 (Everyone)

**Note:** Prefix-only command

**Supported Languages:**

Via **Godbolt** (compiler output):

- C, C++, C#, F#
- Haskell
- Julia
- Python
- Go
- Kotlin
- Swift
- Zig
- Java
- Rust

Via **Wandbox** (execution output):

- Bash/Shell
- D
- Elixir
- Erlang
- Groovy
- JavaScript/Node.js
- TypeScript
- Lisp
- Lua
- Nim
- OCaml
- Pascal
- Perl
- PHP
- Pony
- R
- Ruby
- SQL (SQLite)

**Example:**

---

### Languages

List all supported programming languages.

**Usage:**

```text
$languages
```

**Aliases:** `langs`, `lang`

**Permission:** Rank 0 (Everyone)

**Shows:**

- All supported languages
- Compiler/runtime versions
- Backend service (Godbolt/Wandbox)

---

## Compiler Backends

### Godbolt

Godbolt is used for compiled languages:

- Returns compiler output and assembly
- Useful for seeing optimizations
- Links to Godbolt explorer

**Languages:** C, C++, Rust, Go, Haskell, Python, Java, Kotlin, Swift, Zig

### Wandbox

Wandbox is used for interpreted/script languages:

- Returns execution output
- Supports STDIN
- Good for scripting languages

**Languages:** Bash, JavaScript, TypeScript, Ruby, Python, PHP, Perl, Lua, Elixir, etc.

### Language Detection

Tux automatically detects:

- Language from code block
- Appropriate backend (Godbolt/Wandbox)
- Compiler version

## Limitations

### Execution Limits

- **Timeout:** 10 seconds maximum
- **Output:** Limited to Discord message size
- **Resources:** Limited CPU/memory on backend
- **Network:** No network access in code

### Restricted Operations

- Cannot access files
- Cannot make network requests
- Cannot run indefinitely
- No persistent state

### Safety

- Code runs in sandboxed environments
- Cannot affect Discord or the bot
- Output is sanitized
- ANSI codes removed for readability

## Tips

!!! tip "Language Aliases"
    Many languages have aliases: `py`/`python`, `js`/`javascript`, `rs`/`rust`, `cpp`/`c++`

!!! tip "Check Support"
    Use `$languages` to see all supported languages and their versions.

!!! tip "Formatting"
    Use proper code blocks (triple backticks) for multi-line code.

!!! tip "Quick Tests"
    Perfect for testing small code snippets or algorithms!

!!! warning "Not an IDE"
    This is for quick tests and demonstrations, not full development. Use a proper IDE for larger projects!

## Troubleshooting

### "Unsupported Language"

**Cause:** Language not supported or typo

**Solution:**

- Run `$languages` to see supported languages
- Check spelling
- Use language alias (e.g., `py` instead of `python3`)

### Compilation Error

**Cause:** Syntax error in code

**Solution:**

- Check your code syntax
- Verify language is correct
- Test locally first

### Timeout Error

**Cause:** Code takes too long to execute

**Solution:**

- Simplify your code
- Remove infinite loops
- Optimize algorithm

### Output Too Long

**Cause:** Code produces too much output

**Solution:**

- Limit output lines
- Summarize results
- Use shorter test cases

## Supported Language Reference

### Compiled Languages (Godbolt)

| Language | Versions | Aliases |
|----------|----------|---------|
| C | GCC 15.1 | `c` |
| C++ | GCC 15.1 | `cpp`, `c++` |
| Rust | 1.87.0 | `rs`, `rust` |
| Go | GCC Go 15.1 | `go` |
| Haskell | GHC 9.8.4 | `hs`, `haskell` |
| Python | 3.13 | `py`, `python` |
| Java | Java 24 | `java` |
| Kotlin | 2.1.21 | `kt`, `kotlin`, `kot` |
| Swift | 6.1 | `swift` |
| Zig | 0.14.1 | `zig` |
| C# | .NET 8.0 | `cs`, `csharp` |
| F# | .NET 8.0 | `fs`, `fsharp` |
| Julia | Nightly | `julia` |

### Interpreted Languages (Wandbox)

| Language | Versions | Aliases |
|----------|----------|---------|
| JavaScript | Node.js 20.17.0 | `js`, `javascript` |
| TypeScript | 5.6.2 | `ts`, `typescript` |
| Python | (via Wandbox) | `py`, `python` |
| Ruby | 3.4.1 | `ruby` |
| PHP | 8.3.12 | `php` |
| Bash | Latest | `bash`, `sh` |
| Lua | 5.4.7 | `lua` |
| Perl | 5.40.0 | `perl` |
| R | 4.4.1 | `r` |
| SQL | SQLite 3.46.1 | `sql` |
| Elixir | 1.17.3 | `elixir` |
| Erlang | 27.1 | `erlang` |
| Nim | 2.2.4 | `nim` |
| OCaml | 5.2.0 | `ocaml` |
| Groovy | 4.0.23 | `groovy` |
| D | DMD 2.109.1 | `d` |
| Pascal | FPC 3.2.2 | `pascal` |
| Pony | 0.58.5 | `pony` |
| Lisp | CLISP 2.49 | `lisp` |

## Related Commands

- **[Tools](tools.md)** - Reference lookups
- **[Utility](utility.md)** - General utilities

## External Services

- **[Godbolt Compiler Explorer](https://godbolt.org/)** - Compiler output and assembly
- **[Wandbox](https://wandbox.org/)** - Online code execution

---

**Next:** Learn about [Config Commands](config.md) for server configuration.
