---
title: Caching Best Practices
description: Caching best practices for Tux development, including TTLCache, cache managers, optional Valkey backend, and multi-guild safety.
tags:
  - developer-guide
  - best-practices
  - caching
icon: lucide/database
---

# Caching Best Practices

Tux uses a TTL-based caching system to improve performance and reduce database load. All cache code lives in `src/tux/cache/`. The system supports an optional Valkey (Redis-compatible) backend for shared state across restarts; when Valkey is not configured or unavailable, in-memory backends are used.

## Architecture

### Package layout

| Module | Purpose |
|--------|---------|
| `tux.cache.ttl` | `TTLCache` — in-memory TTL cache used by backends and managers |
| `tux.cache.backend` | `InMemoryBackend`, `ValkeyBackend`, `get_cache_backend(bot)` |
| `tux.cache.managers` | `GuildConfigCacheManager`, `JailStatusCache` |
| `tux.cache.service` | `CacheService` — Valkey connection lifecycle (connect, ping, close) |

### Backends

- **InMemoryBackend**: Single process, one `TTLCache` with configurable TTL and `max_size`. Used when Valkey is not configured or when `get_cache_backend(bot)` has no connected `cache_service`.
- **ValkeyBackend**: When `VALKEY_URL` is set and the bot connects at startup, guild config, jail status, prefix, and permission caches use Valkey. Keys are prefixed with `tux:` and values are JSON-serialized.

Setup (e.g. `cache_setup.py`) connects to Valkey on startup and sets the backend on `GuildConfigCacheManager` and `JailStatusCache`; permission controllers receive the backend via the coordinator. No code changes are required in consumers — they use the same managers; the backend is injected by setup.

### Multi-guild safety

All cache keys that represent guild-specific data include `guild_id` (and `user_id` or `command_name` where needed). One backend instance is shared across all guilds; keys do not collide. Examples:

- `guild_config:{guild_id}`
- `jail_status:{guild_id}:{user_id}`
- `prefix:{guild_id}`
- `perm:command_permission:{guild_id}:{command_name}`

## Overview

The caching system provides:

- **TTLCache** — In-memory TTL cache with automatic expiration (used internally and for direct use)
- **GuildConfigCacheManager** — Singleton cache manager for guild configuration (audit log, mod log, jail role/channel IDs)
- **JailStatusCache** — Singleton cache manager for jail status per (guild_id, user_id)
- **Optional Valkey backend** — Shared cache across process restarts when `VALKEY_URL` is set
- **Automatic expiration** — Entries expire after their TTL
- **Cache invalidation** — Manual invalidation when data changes

## TTLCache

`TTLCache` is the in-memory TTL cache used by `InMemoryBackend` and by the managers when no backend is set. It supports synchronous `get` / `set` / `invalidate` / `clear`.

### Basic usage

```python
from tux.cache import TTLCache

# Create a cache with 5-minute TTL and max 1000 entries
cache = TTLCache(ttl=300.0, max_size=1000)

# Set a value
cache.set("key", "value")

# Get a value (returns None if not found or expired)
value = cache.get("key")

# Invalidate a specific key
cache.invalidate("key")

# Clear all entries
cache.clear()
```

### Get or fetch pattern

The `get_or_fetch` method is useful for caching expensive operations:

```python
def fetch_user_data(user_id: int) -> dict:
    # Expensive database query
    return {"name": "User", "id": user_id}

# Get from cache or fetch if missing
user_data = cache.get_or_fetch(
    f"user_{user_id}",
    lambda: fetch_user_data(user_id),
)
```

### Cache configuration

Choose appropriate TTL values based on how often data changes:

- **Frequently changing data** (e.g. jail status): 60–300 seconds
- **Moderately changing data** (e.g. guild config): 300–600 seconds (5–10 minutes)
- **Rarely changing data** (e.g. permission ranks): 600 seconds (10 minutes)

## GuildConfigCacheManager

`GuildConfigCacheManager` is a singleton that caches guild configuration (audit log ID, mod log ID, jail role ID, jail channel ID). When a backend is set (e.g. Valkey), get/set/invalidate use the backend; otherwise they use an in-memory TTL cache. All methods that read or write cache are **async**.

### Usage

```python
from tux.cache import GuildConfigCacheManager

cache_manager = GuildConfigCacheManager()

# Get cached config (async)
config = await cache_manager.get(guild_id)
if config:
    audit_log_id = config.get("audit_log_id")
    mod_log_id = config.get("mod_log_id")

# Update cache — only updates provided fields (async)
await cache_manager.set(
    guild_id=guild_id,
    audit_log_id=123456789,
    mod_log_id=987654321,
)

# Invalidate cache when config changes (async)
await cache_manager.invalidate(guild_id)
```

### Partial updates

The cache manager supports partial updates. Only explicitly provided fields are updated:

```python
# Only update audit_log_id, leave other fields unchanged
await cache_manager.set(guild_id=guild_id, audit_log_id=new_id)

# Update multiple fields
await cache_manager.set(
    guild_id=guild_id,
    audit_log_id=new_audit_id,
    mod_log_id=new_mod_id,
)
```

### clear_all behavior

`clear_all()` clears only the **in-memory** cache. When a Valkey backend is set, backend keys are not removed (no pattern delete in the current API). Use per-guild `invalidate(guild_id)` to clear a specific guild’s entry in both memory and backend.

## JailStatusCache

`JailStatusCache` is a singleton that caches jail status per (guild_id, user_id). When a backend is set, get/set/invalidate use the backend. All methods that read or write cache are **async**.

### Usage

```python
from tux.cache import JailStatusCache

jail_cache = JailStatusCache()

# Get cached jail status (async)
is_jailed = await jail_cache.get(guild_id, user_id)
if is_jailed is None:
    # Not cached, fetch from database
    is_jailed = await check_jail_status(guild_id, user_id)
    await jail_cache.set(guild_id, user_id, is_jailed)

# Invalidate when jail status changes (async)
await jail_cache.invalidate(guild_id, user_id)

# Invalidate all in-memory entries for a guild (async)
# Note: does not clear backend keys when Valkey is used
await jail_cache.invalidate_guild(guild_id)
```

### get_or_fetch with stampede protection

For jail checks with concurrent access, use `get_or_fetch` so only one coroutine fetches and the rest wait:

```python
async def fetch_jail_status() -> bool:
    latest = await get_latest_jail_or_unjail_case(user_id=user_id, guild_id=guild_id)
    return bool(latest and latest.case_type == CaseType.JAIL)

is_jailed = await jail_cache.get_or_fetch(guild_id, user_id, fetch_jail_status)
```

## Cache invalidation

Proper cache invalidation is critical for data consistency. Always invalidate caches when data changes.

### In controller methods

```python
async def update_config(self, guild_id: int, **kwargs):
    # Update database
    result = await self.update(...)

    # Invalidate cache
    cache_manager = GuildConfigCacheManager()
    await cache_manager.invalidate(guild_id)

    return result
```

### In permission system

The permission system and permission controllers automatically invalidate their caches when permissions or ranks change. No extra invalidation is needed when using the standard APIs.

## Best practices

### 1. Choose appropriate TTL values

- Use shorter TTLs (60–300 seconds) for frequently changing data
- Use longer TTLs (300–600 seconds) for stable configuration data
- Consider data update frequency when setting TTL

### 2. Always invalidate on updates

```python
# ❌ Bad: Update database but forget to invalidate cache
await controller.update(...)

# ✅ Good: Invalidate cache after update
await controller.update(...)
cache_manager = GuildConfigCacheManager()
await cache_manager.invalidate(guild_id)
```

### 3. Use singleton cache managers

For shared data like guild config and jail status, use the singleton cache managers. Do not replace or bypass them with ad-hoc caches for the same data:

```python
# ✅ Good: Use singleton
cache_manager = GuildConfigCacheManager()
config = await cache_manager.get(guild_id)

# ❌ Bad: Bypass manager with a separate cache (inconsistent state)
my_own_cache = TTLCache()
```

### 4. Handle cache misses and async APIs

```python
# ✅ Good: Handle None and use await for managers
cached = await cache_manager.get(guild_id)
if cached is None:
    cached = await fetch_config(guild_id)
    await cache_manager.set(guild_id, audit_log_id=cached["audit_log_id"], ...)

# ❌ Bad: Assume cache always has value
cached = await cache_manager.get(guild_id)
process(cached)  # Error if None
```

### 5. Use batch operations when possible

For permission checks, prefer batch retrieval to reduce cache lookups and round-trips.

### 6. In tests, invalidate when relying on fresh DB state

When a test expects the database to be the source of truth (e.g. “latest case is UNJAIL”), invalidate the relevant cache key first so the manager does not return a stale value from a previous test or from the backend:

```python
await JailStatusCache().invalidate(TEST_GUILD_ID, TEST_USER_ID)
# Now create cases and call code that uses is_jailed
```

## Cache pre-warming

The permission system supports cache pre-warming on bot startup to reduce cold-start latency:

```python
# Pre-warm caches for a specific guild
await permission_system.pre_warm_guild_cache(guild_id)

# Pre-warm caches for all guilds
await permission_system.pre_warm_all_caches()
```

This is invoked during bot initialization where applicable.

## Concurrency and safety

- **TTLCache**: Synchronous API; safe for concurrent use from multiple async tasks (no await between check and use for a key).
- **Managers**: Async API; use `await` for get/set/invalidate. Locks are per-guild or per (guild_id, user_id) to avoid cross-guild contention.
- **Backends**: One backend instance per bot; keys include `guild_id` (and user/command where needed) so multiple guilds do not share the same logical entry.

## Valkey implementation notes

These notes summarize behavior and edge cases from the cache/Valkey implementation audit.

### Fallback backend reuse

When Valkey is not configured or disconnected, `get_cache_backend(bot)` returns a single shared `InMemoryBackend` cached on the bot (`bot._fallback_cache_backend`).

All consumers (cache setup, permission setup, prefix manager, permission system) therefore share the same in-memory store when Valkey is unavailable.

### GuildConfigCacheManager: set vs async_set

- **`set()`**: No per-guild lock. Concurrent `set()` calls for the same guild can race (read–merge–write). Last write wins; partial merges are safe but one update could be lost under heavy concurrency. Used by the guild config controller after DB updates (typically one writer per guild).
- **`async_set()`**: Uses a per-guild lock for concurrent safety. Use when multiple coroutines may update the same guild’s config (e.g. communication_service). Prefer `async_set()` for code paths that may run concurrently for the same guild.

### JailStatusCache: set vs async_set

- **`set()`**: Overwrites the cached value. Used after rejail (jail.py) to record the new status.
- **`async_set()`**: Same overwrite behavior as `set()`, with async locking for concurrent safety. Use when multiple coroutines may update the same guild/user; otherwise `set()` is sufficient.

### Valkey disconnect and errors

- **No automatic reconnection**: If Valkey is lost mid-run (network partition, server restart), the client is not reconnected. Cache operations will raise (e.g. connection errors) until the process is restarted. Startup retries and ping-on-connect reduce the chance of running with a bad connection.
- **Backend operations**: `ValkeyBackend` get/set/delete do not catch exceptions; Valkey/network errors propagate to callers. Callers should handle or log as appropriate.

### Backend behavior details

- **InMemoryBackend**: Ignores `ttl_sec` on `set()`; all entries use the backend’s default TTL from construction.
- **ValkeyBackend**: TTL is passed to Valkey as integer seconds (fractional seconds truncated). Non-JSON values returned by Valkey (e.g. legacy or raw strings) are returned as-is from `get()`; JSON values are deserialized.
- **Delete missing key**: Backends treat delete of a missing key as a no-op (Valkey returns 0; in-memory invalidate is safe).

## Performance considerations

- **Memory (InMemoryBackend)**: A single `TTLCache` with `max_size` is shared across all guilds; eviction is global. Size the limit for total entries across guilds.
- **Valkey**: When used, backend keys have a global `tux:` prefix; no per-guild key limit. TTLs are applied per key where supported.
- **TTL tuning**: Balance freshness vs. hit rate; avoid overly short TTLs that defeat caching.
- **Invalidation**: Invalidate only when data actually changes; excessive invalidation reduces benefit.

## Troubleshooting

### Cache not updating

If cached data seems stale:

1. Ensure cache invalidation is called after updates (and that you `await` it for managers).
2. When Valkey is used, remember that `clear_all()` and `invalidate_guild()` only clear in-memory state; use per-key `invalidate(guild_id)` or `invalidate(guild_id, user_id)` to clear backend entries.
3. Verify TTL is appropriate for how often the data changes.
4. Confirm you are using the singleton managers, not separate caches for the same data.

### High memory usage

If in-memory cache usage is high:

1. Reduce `max_size` on the backend/cache where configurable.
2. Reduce TTL so entries expire sooner.
3. Ensure invalidation is called when data is updated or removed.

### Low cache hit rate

If cache hit rate is low:

1. Increase TTL for stable data.
2. Use pre-warming on startup where supported.
3. Check whether invalidation is too frequent or too broad.

## Resources

- **Cache package**: `src/tux/cache/` — `ttl.py`, `backend.py`, `managers.py`, `service.py`
- **Cache setup**: `src/tux/core/setup/cache_setup.py`
- **Permission system caching**: `src/tux/core/permission_system.py`
- **Permission controller caching**: `src/tux/database/controllers/permissions.py`
- **Guild config controller**: `src/tux/database/controllers/guild_config.py`
- **Prefix caching**: `src/tux/core/prefix_manager.py`
