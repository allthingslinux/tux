---
title: Encode-decode
description: Encode and decode text using various algorithms
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - utility
  - security
---

# Encode-decode

The `encode` and `decode` commands provide quick access to common text transformation algorithms. This is useful for developers who need to quickly verify encoded strings or for community activities that involve base-encoded data.

## Syntax

The commands are available in both slash and prefix formats:

**Slash Command:**

```text
/encode encoding:STRING text:STRING
/decode encoding:STRING text:STRING
```

**Prefix Command:**

```text
$encode <encoding> <text>
$decode <encoding> <text>
```

**Aliases:**

- `ec` (encode)
- `dc` (decode)

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `encoding`| STRING | Yes | The format to use: `base16`, `base32`, `base64`, or `base85`. |
| `text`    | STRING | Yes | The data you want to transform. |

## Supported Formats

- **Base16:** Standard hexadecimal encoding.
- **Base32:** Uses a 32-character set (often used in early systems or for readability).
- **Base64:** The most common format for encoding binary data into ASCII text.
- **Base85:** A more efficient encoding than Base64 (also known as Ascii85).

## Usage Examples

### Encoding a Message

Transform a string into Base64.

```text
/encode encoding:base64 text:"Hello World!"
```

### Decoding Data

Translate a Base16 (Hex) string back to readable text.

```text
/decode encoding:base16 text:"48656c6c6f"
```

## Response

The bot replies with the resulting string. If the output exceeds Discord's 2000-character limit, the bot will suggest using an external tool to prevent message truncation.

## Behavior Notes

- **Ephemeral:** Slash command responses are only visible to the user who ran the command.
- **Mentions:** The bot disables all mentions in its output to prevent accidental pings from decoded data.

## Related Commands

- [`/run`](run.md) - For advanced code execution.
