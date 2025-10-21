# Info Commands

Information commands provide detailed information about Discord objects like users, channels, servers, and more.

## Commands

### Info

Display detailed information about Discord objects.

**Usage:**

```bash
/info @user                         # User info
/info #channel                      # Channel info
/info @role                         # Role info
/info :emoji:                       # Emoji info
$info @user                         # Prefix version
$info #channel                      # Prefix version
```bash

**Parameters:**

- `entity` (required) - Discord object to get info about
  - **Users:** `@user` or `user#1234`
  - **Channels:** `#channel` or channel ID
  - **Roles:** `@role` or role ID
  - **Emojis:** `:emoji:` or emoji ID
  - **Guilds:** Server ID (prefix only)

**Supported Types:**

- **Users** - User/Member information
- **Channels** - Channel details
- **Guilds** - Server information
- **Roles** - Role details
- **Emojis** - Custom emoji info
- **Stickers** - Sticker information
- **Invites** - Invite details
- **Threads** - Thread information
- **Events** - Scheduled event details

**Permission:** Rank 0 (Everyone)

**Example:**

```bash
/info @user
```bash

Shows: Account created, joined server, roles, permissions, avatar, etc.

---

### Avatar

View a user's avatar in full resolution.

**Usage:**

```bash
/avatar @user
/avatar                             # Your own avatar
$avatar @user
```bash

**Parameters:**

- `user` (optional) - User to view avatar of (default: yourself)

**Aliases:** `av`, `pfp`

**Permission:** Rank 0 (Everyone)

**Features:**

- Shows both server avatar and global avatar
- Provides download links
- Full resolution images

**Example:**

```bash
/avatar @friend
```bash

---

### Member Count

Show server member statistics.

**Usage:**

```bash
/membercount
$membercount
```bash

**Aliases:** `mc`, `members`

**Permission:** Rank 0 (Everyone)

**Shows:**

- Total members
- Online members
- Bot count
- Human count
- Various statistics

**Example:**

```bash
/membercount
```bash

Output: "Server has 1,234 members (1,000 humans, 234 bots). 456 online."

---

## Permission Requirements

| Command      | Minimum Rank | Typical Role  |
|-------------|-------------|----------------|
| info        | 0           | Everyone       |
| avatar      | 0           | Everyone       |
| membercount | 0           | Everyone       |

## Usage Examples

### Getting User Information

```bash
/info @user
```bash

Useful for:

- Checking join date
- Viewing roles
- Checking account age
- Viewing permissions

### Checking Channel Details

```bash
/info #channel
```bash

Shows:

- Channel type
- Creation date
- Topic
- Permissions
- Member count (for voice)

### Server Information

```bash
/info
```bash

Without any target, shows information about the current server.

## Tips

!!! tip "Context Menu"
    Some info commands may be available via right-click context menus in Discord.

!!! tip "Avatar Quality"
    Use `/avatar` to get the full-resolution avatar instead of right-clicking.

!!! tip "Quick Stats"
    Use `/membercount` to quickly check server growth and online status.

## Related Commands

- **[Utility Commands](utility.md)** - General utility tools
- **[Tools](tools.md)** - Wiki and TLDR lookups

---

**Next:** Learn about [Snippets](snippets.md) for text management.
