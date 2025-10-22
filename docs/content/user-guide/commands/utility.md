# Utility Commands

Tux provides various utility commands for server management, productivity, and convenience.

## Server Status

### Ping

Check the bot's latency and system stats.

**Usage:**

```bash
/ping
$ping
```bash

**Aliases:** `status`

**Permission:** Rank 0 (Everyone)

**Shows:**

- API Latency (ms)
- Bot Uptime
- CPU Usage (%)
- RAM Usage (MB/GB)

**Example Output:**

```bash
Pong!
API Latency: 45ms
Uptime: 2d 14h 32m 15s
CPU Usage: 12.5%
RAM Usage: 256MB
```bash

---

## Productivity Tools

### RemindMe

Set a reminder for yourself.

**Usage:**

```bash
/remindme duration:1h content:"Check the logs"
$remindme 1h Check the logs
```bash

**Parameters:**

- `duration` (required) - When to remind you
- `content` (required) - What to remind you about

**Permission:** Rank 0 (Everyone)

**Duration Format:**

- `30s` - 30 seconds
- `5m` - 5 minutes
- `2h` - 2 hours
- `3d` - 3 days
- `1w` - 1 week

**Notes:**

- Reminder sent via DM
- If DM fails, sends in original channel
- Stored in database (persists across restarts)

**Examples:**

```bash
/remindme duration:30m content:"Meeting starts"
/remindme duration:1d content:"Follow up on issue"
```bash

---

### Poll

Create a poll with multiple options.

**Usage:**

```bash
/poll title:"What's your favorite distro?" options:"Arch, Debian, Fedora, Ubuntu"
```bash

**Parameters:**

- `title` (required) - Poll question
- `options` (required) - Comma-separated options (max 9)

**Permission:** Rank 0 (Everyone)

**Note:** This is a **slash-only** command.

**How It Works:**

1. Creates an embed with numbered options
2. Adds number reactions (1️⃣, 2️⃣, 3️⃣, etc.)
3. Users vote by reacting
4. Results visible by reaction counts

**Example:**

```bash
/poll title:"Pizza night?" options:"Yes, No, Maybe"
```bash

---

### AFK

Set yourself as away from keyboard.

**Usage:**

```bash
/afk reason:"Lunch break"
$afk Going to lunch
```bash

**Parameters:**

- `reason` (optional) - Why you're AFK

**Permission:** Rank 0 (Everyone)

**Features:**

- Auto-notification when someone mentions you
- Auto-clear when you send a message
- Adds [AFK] to your nickname
- Stores in database

**Example:**

```bash
/afk reason:"In a meeting, back in 1h"
```bash

---

### PermAFK

Set yourself permanently AFK until manually cleared.
**This is a toggle command** - run it again to clear your AFK status.

**Usage:**

```bash
/permafk reason:"On vacation"         # Set AFK
/permafk reason:"Back from vacation"  # Clear AFK (toggle)
$permafk On vacation for 2 weeks       # Set AFK
$permafk Back now                      # Clear AFK (toggle)
```bash

**Parameters:**

- `reason` - Why you're AFK (default: "No reason.")

**Permission:** Rank 0 (Everyone)

**Key Features:**

- **Toggle behavior:** Run the command again to clear your AFK status
- Doesn't auto-clear when you send messages (unlike regular AFK)
- Must manually toggle off by running `/permafk` again
- Useful for extended absences

---

### Self Timeout

Timeout yourself (self-moderation).

**Usage:**

```bash
/self_timeout duration:30m reason:"Need a break"
$self_timeout 30m -r "Need a break"
```bash

**Parameters:**

- `duration` (required) - How long to timeout (max 28 days)
- `reason` - Reason for self-timeout (optional)

**Aliases:** `sto`, `stimeout`, `selftimeout`

**Permission:** Rank 0 (Everyone)

**Notes:**

- Useful for self-discipline
- Cannot be removed by yourself (must wait or ask moderator)
- Creates a case like moderator timeouts

**Example:**

```bash
/self_timeout duration:2h reason:"Taking a break from Discord"
```bash

---

## Encoding Tools

### Encode

Encode text to various formats.

**Usage:**

```bash
/encode encoding:base64 text:"Hello World"
$encode base64 Hello World
```bash

**Parameters:**

- `encoding` (required) - Encoding format
- `text` (required) - Text to encode

**Permission:** Rank 0 (Everyone)

**Supported Formats:**

- `base64` - Base64 encoding
- `base32` - Base32 encoding
- `hex` - Hexadecimal encoding
- `binary` - Binary encoding
- `ascii85` - ASCII85 encoding
- `rot13` - ROT13 cipher
- `url` - URL encoding

**Aliases:** `ec`

**Example:**

```bash
/encode encoding:base64 text:"secret message"
```bash

Output: `c2VjcmV0IG1lc3NhZ2U=`

---

### Decode

Decode text from various formats.

**Usage:**

```bash
/decode encoding:base64 text:"SGVsbG8gV29ybGQ="
$decode base64 SGVsbG8gV29ybGQ=
```bash

**Parameters:**

- `encoding` (required) - Encoding format
- `text` (required) - Text to decode

**Permission:** Rank 0 (Everyone)

**Supported Formats:** Same as encode

**Aliases:** `dc`

**Example:**

```bash
/decode encoding:base64 text:"SGVsbG8gV29ybGQ="
```bash

Output: `Hello World`

---

## Time & Location

### Timezones

Display current time in various timezones.

**Usage:**

```bash
/timezones
$timezones
```bash

**Aliases:** `tz`

**Permission:** Rank 0 (Everyone)

**Shows:**

- Multiple major timezones
- Current time in each
- Useful for coordinating with global teams

---

## Permission Requirements

| Command      | Minimum Rank | Typical Role  |
|-------------|-------------|----------------|
| ping        | 0           | Everyone       |
| poll        | 0           | Everyone       |
| remindme    | 0           | Everyone       |
| afk         | 0           | Everyone       |
| permafk     | 0           | Everyone       |
| self_timeout| 0           | Everyone       |
| encode      | 0           | Everyone       |
| decode      | 0           | Everyone       |
| timezones   | 0           | Everyone       |

## Common Use Cases

### Coordinating Across Timezones

```bash
/timezones                          # Check current time zones
/remindme duration:8h content:"EU meeting starts"
```bash

### Taking a Break

```bash
/afk reason:"Grabbing dinner, back in 30m"
/self_timeout duration:30m reason:"Studying"
```bash

### Community Engagement

```bash
/poll title:"Next event?" options:"Game night, Movie night, Coding session"
```bash

### Encoding Messages

```bash
/encode encoding:base64 text:"secret message"
# Share the encoded text
# Others use /decode to read it
```bash

## Tips

!!! tip "Reminder Persistence"
    Reminders are stored in the database and will still fire even if the bot restarts.

!!! tip "AFK Automation"
    AFK status automatically clears when you send a message (except with `/permafk`).

!!! tip "Self-Moderation"
    Use `/self_timeout` if you need to force yourself to take a break from Discord!

!!! tip "Poll Reactions"
    The bot automatically adds number reactions to polls. Users just click to vote!

## Troubleshooting

### Reminder Didn't Fire

**Possible causes:**

- Bot was offline when reminder was due
- DMs are disabled and channel was deleted
- Database error

**Solution:**

- Check bot uptime: `/ping`
- Enable DMs from server members
- Check bot logs

### AFK Not Clearing

**Possible causes:**

- Using `/permafk` instead of `/afk`
- Bot permissions issue

**Solution:**

- If using permafk, run `/permafk` again to clear
- Ask moderator to use `/clearafk @you`

### Poll Reactions Not Working

**Possible causes:**

- Bot missing "Add Reactions" permission
- Custom emoji restrictions

**Solution:**

- Grant bot "Add Reactions" permission
- Use slash command version: `/poll`

## Related Commands

- **[Info Commands](info.md)** - User and server information
- **[AFK Commands](#afk)** - Clear someone's AFK status

## Need Help?

- **[Discord Support](https://discord.gg/gpmSjcjQxg)** - Ask in #support
- **[GitHub Issues](https://github.com/allthingslinux/tux/issues)** - Report bugs

---

**Next:** Learn about [Info Commands](info.md) for viewing Discord information.
