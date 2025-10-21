# Levels Commands

XP and leveling commands for viewing and managing user progression.

## User Commands

### Level

View your or someone else's level and XP.

**Usage:**

```
/level                              # Your own level
/level @user                        # Someone else's level
$level @user
```

**Parameters:**

- `user` (optional) - User to check (default: yourself)

**Aliases:** `lvl`, `rank`, `xp`

**Permission:** Rank 0 (Everyone)

**Shows:**

- Current level
- Total XP
- XP to next level
- Server rank position
- Progress bar

**Example:**

```
/level @friend
```

Output: "Friend is Level 25 with 12,450 XP. Rank #5 in server. 550 XP to Level 26."

---

## Admin Commands

These commands are for managing the XP system.

### Levels

Group command for XP management.

**Usage:**

```
/levels                             # Show help
```

**Aliases:** `lvls`

**Permission:** Varies by subcommand

**Subcommands:**

- `set` - Set user's level
- `add` - Add XP to user
- `remove` - Remove XP from user
- `reset` - Reset user's XP
- `blacklist` - Toggle XP blacklist

---

### Levels Set

Set a user's level directly.

**Usage:**

```
/levels set @user level:25
```

**Parameters:**

- `user` (required) - User to modify
- `level` (required) - Level to set (0-100)

**Aliases:** `s`

**Permission:** Rank 5 (Administrator)

**Notes:**

- Updates XP to match level
- Grants/removes XP roles automatically
- Creates audit log entry

---

### Levels Add

Add XP to a user.

**Usage:**

```
/levels add @user xp:1000
```

**Parameters:**

- `user` (required) - User to give XP to
- `xp` (required) - Amount of XP to add

**Permission:** Rank 5 (Administrator)

**Notes:**

- Can trigger level-ups
- Grants roles automatically

---

### Levels Remove

Remove XP from a user.

**Usage:**

```
/levels remove @user xp:500
```

**Parameters:**

- `user` (required) - User to remove XP from
- `xp` (required) - Amount of XP to remove

**Permission:** Rank 5 (Administrator)

**Notes:**

- Can trigger level-downs
- Removes roles automatically

---

### Levels Reset

Reset a user's XP to 0.

**Usage:**

```
/levels reset @user
```

**Parameters:**

- `user` (required) - User to reset

**Permission:** Rank 5 (Administrator)

**Warning:** This is permanent and cannot be undone!

---

### Levels Blacklist

Toggle XP gain for a user.

**Usage:**

```
/levels blacklist @user
```

**Parameters:**

- `user` (required) - User to blacklist/unblacklist

**Permission:** Rank 5 (Administrator)

**Notes:**

- Blacklisted users don't gain XP
- Existing XP/level is preserved
- Toggle command - run again to unblacklist
- Useful for bots or inactive accounts

---

## Permission Requirements

| Command          | Minimum Rank | Typical Role  |
|-----------------|-------------|----------------|
| level           | 0           | Everyone       |
| levels set      | 5           | Administrator  |
| levels add      | 5           | Administrator  |
| levels remove   | 5           | Administrator  |
| levels reset    | 5           | Administrator  |
| levels blacklist| 5           | Administrator  |

## Configuration

Levels/XP system requires configuration in `config.toml`:

```toml
[xp_config]
xp_roles = [
    { level = 5, role_id = 123456789 },
    { level = 10, role_id = 987654321 },
    { level = 25, role_id = 111222333 },
]
```

If XP_ROLES is empty, the levels cog won't load.

**See:** [XP System Feature Documentation](../features/xp-system.md)

## Common Use Cases

### Checking Progress

```
/level                              # See your own progress
/level @friend                      # See friend's progress
```

### Rewarding Users

```
/levels add @helper xp:500          # Bonus for helping
```

### Fixing Mistakes

```
/levels remove @user xp:100         # Remove incorrectly gained XP
```

### Managing Bots

```
/levels blacklist @MusicBot         # Prevent bot from gaining XP
```

## Tips

!!! tip "Automatic Roles"
    Configure XP roles to automatically grant roles at certain levels!

!!! tip "Leaderboard"
    Level rankings show server position - competitive users love this!

!!! warning "Blacklist vs Ban"
    Blacklist prevents XP gain but keeps existing XP. Use for bots or inactive users, not punishment.

## Related Features

- **[XP System](../features/xp-system.md)** - How XP/leveling works
- **[Configuration](config.md)** - Set up XP roles

---

**Next:** Learn about [Fun Commands](fun.md) for entertainment.
