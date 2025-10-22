# Permissions Configuration

Set up Tux's permission rank system for your server.

## Permission Ranks

Tux uses 8 permission ranks (0-7):

- 0: Member
- 1: Trusted
- 2: Junior Moderator
- 3: Moderator
- 4: Senior Moderator
- 5: Administrator
- 6: Head Administrator
- 7: Server Owner

## Setup Steps

### 1. Initialize Ranks

```text
/config rank init
```

Creates all 8 ranks in database.

### 2. Assign Roles

```text
/config role assign 3 @Moderators
/config role assign 5 @Admins
```

### 3. Verify

```text
/config role
```

## Advanced Configuration

**Command-specific permissions:**

```text
/config command assign ping 2       # Restrict /ping to Rank 2+
```

## Related

- **[Permission System Guide](../../user-guide/permissions.md)** - User documentation
- **[Config Commands](../../user-guide/commands/config.md)** - Command reference

---

*See user guide for comprehensive permission documentation.*
