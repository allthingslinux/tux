---
title: Snippets
description: Create and manage code snippets and aliases with optional role-based access control.
tags:
  - user-guide
  - features
  - snippets
icon: lucide/square-pen
---

# Snippets

Snippets let users store and reuse text or code in your Discord server. Members create snippets by name, add aliases, and call them on demand. With role-based access enabled, only users with designated roles can create, edit, or delete snippets; everyone can still view and use existing ones.

## How It Works

### Mechanics

- **Create:** Users run `$createsnippet` (or `$cs`) with a name and content to add a snippet or an alias.
- **Use:** `$snippet` (or `$s`) outputs the snippet content; `$snippets` lists all snippets; `$snippetinfo` shows metadata.
- **Manage:** `$editsnippet` and `$deletesnippet` change or remove snippets. Owners can always manage their own unless the snippet is locked; moderators can lock snippets and override ownership.

### Role-Based Access

When `LIMIT_TO_ROLE_IDS` is `true`:

- Only users with at least one role in `ACCESS_ROLE_IDS` can **create**, **edit**, or **delete** snippets.
- **Viewing** and **using** snippets (`$snippet`, `$snippets`, `$snippetinfo`) stays available to everyone (subject to command and channel permissions).
- Moderators (rank 2+) can manage any snippet regardless of `ACCESS_ROLE_IDS`.

When `LIMIT_TO_ROLE_IDS` is `false` (default), any member can create and manage their own snippets, subject to snippet bans and lock status.

### Triggers

- **Create:** `$createsnippet <name> <content>`
- **Edit/delete:** Gated by `snippet_check` (mod override, snippet ban, `LIMIT_TO_ROLE_IDS` + `ACCESS_ROLE_IDS`, lock, ownership).

## User Experience

### When Role Restriction Is Off

- Any member can create, edit, and delete their own snippets.
- Locked snippets can only be changed by moderators.

### When Role Restriction Is On

- Users **without** an `ACCESS_ROLE_IDS` role see: *"You do not have a role that allows you to manage snippets. Accepted roles: @Role1, @Role2"* when trying to create, edit, or delete.
- Users **with** an allowed role, or moderators, can manage snippets as usual.

## Configuration

Snippets are configured in the server's `config.json` file under the `SNIPPETS` object.

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `LIMIT_TO_ROLE_IDS` | `boolean` | `false` | When `true`, only users with a role in `ACCESS_ROLE_IDS` can create, edit, or delete snippets. |
| `ACCESS_ROLE_IDS` | `array` | `[]` | Role IDs allowed to manage snippets when `LIMIT_TO_ROLE_IDS` is `true`. Ignored when `false`. |

### Example Configuration

```json
{
  "SNIPPETS": {
    "LIMIT_TO_ROLE_IDS": true,
    "ACCESS_ROLE_IDS": [
      123456789012345678,
      987654321098765432
    ]
  }
}
```

!!! info "Configuration Guide"
    For detailed configuration instructions, see the [Admin Guide](../../admin/config/index.md).

## Permissions

### Bot Permissions

- **Send Messages** – Command responses and snippet output
- **Embed Links** – Rich snippet displays
- **Manage Messages** – Locking and managing snippet responses

### User Permissions

- When `LIMIT_TO_ROLE_IDS` is `false`: any member can create and manage their own snippets (except when snippet-banned or when the snippet is locked).
- When `LIMIT_TO_ROLE_IDS` is `true`: only users with a role in `ACCESS_ROLE_IDS` (or moderators) can create, edit, or delete snippets.

!!! info "Permission System"
    Configure command visibility and defaults via `/config commands` or the [Permission Configuration](../../admin/config/commands.md) guide.

## Troubleshooting

### Issue: "You do not have a role that allows you to manage snippets"

**Causes:**

- `LIMIT_TO_ROLE_IDS` is `true` and the user has no role in `ACCESS_ROLE_IDS`.
- The user's role ID is not in `ACCESS_ROLE_IDS`.
- `ACCESS_ROLE_IDS` is empty while `LIMIT_TO_ROLE_IDS` is `true`.

**Solutions:**

1. Add the intended role IDs to `ACCESS_ROLE_IDS` in `config.json`.
2. Ensure the user has one of those roles.
3. Set `LIMIT_TO_ROLE_IDS` to `false` to allow all members to manage their own snippets.

### Issue: User cannot create snippets at all

**Causes:**

- User is [snippet-banned](../modules/moderation/snippetban.md) (`/snippetban`).
- `LIMIT_TO_ROLE_IDS` is `true` and the user lacks an `ACCESS_ROLE_IDS` role.
- Tux lacks Send Messages or Embed Links in the channel.

**Solutions:**

1. Check snippet ban status with moderators; use `/snippetunban` if appropriate.
2. Confirm `SNIPPETS` config and the user's roles.
3. Ensure Tux has the required permissions in the channel.

## Limitations

- **Manage vs use:** Role restriction only affects creating, editing, and deleting; viewing and using snippets is not restricted by `ACCESS_ROLE_IDS`.
- **Server-scoped:** Snippets and `SNIPPETS` config are per-guild.
- **Prefix commands:** Snippet commands use the `$` prefix; slash equivalents may vary.

## Related Documentation

- [Snippets Module](../modules/snippets/index.md)
- [Admin Configuration Guide](../../admin/config/index.md)
- [Permission Configuration](../../admin/config/commands.md)
