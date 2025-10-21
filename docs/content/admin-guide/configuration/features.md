# Features Configuration

Enable and configure Tux features.

## XP/Leveling System

Configure in `config.toml`:

```toml
[xp]
xp_cooldown = 60
levels_exponent = 2.0
show_xp_progress = true
enable_xp_cap = false

xp_roles = [
    { level = 5, role_id = 1234567890 },
    { level = 10, role_id = 2345678901 },
    { level = 25, role_id = 3456789012 },
]

xp_multipliers = [
    { role_id = 9876543210, multiplier = 1.5 },
]

xp_blacklist_channels = [1111222233]
```

**Required:** `xp_roles` must be configured for XP system to load.

**See:** [XP System Feature Guide](../../user-guide/features/xp-system.md)

## Starboard

Set up via commands:

```
/starboard setup #starboard ⭐ 3
```

**See:** [Starboard Feature Guide](../../user-guide/features/starboard.md)

## Status Roles

Configure in `config.toml`:

```toml
[status_roles]
mappings = [
    { status = "online", role_id = 123456 },
    { status = "streaming", role_id = 789012 },
]
```

**See:** [Status Roles Feature Guide](../../user-guide/features/status-roles.md)

## Temp VC

Configure channel and category IDs:

```bash
TEMPVC__TEMPVC_CHANNEL_ID=creator_channel_id
TEMPVC__TEMPVC_CATEGORY_ID=category_id
```

**See:** [Temp VC Feature Guide](../../user-guide/features/temp-vc.md)

## GIF Limiter

Configure limits:

```toml
[gif_limiter]
recent_gif_age = 60
gif_limit_exclude = [channel_id1, channel_id2]
```

**See:** [GIF Limiter Feature Guide](../../user-guide/features/gif-limiter.md)

## Snippets

```toml
[snippets]
limit_to_role_ids = false
access_role_ids = []
```

## Related

- **[Config Files](../setup/config-files.md)**
- **[User Feature Guides](../../user-guide/features/xp-system.md)**

---

*Full feature configuration documentation in progress.*
