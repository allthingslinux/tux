---
title: Caching Best Practices
description: Caching best practices for Tux development, including TTLCache, cache invalidation, cache expiration, and cache eviction.
tags:
  - developer-guide
  - best-practices
  - caching
---

# Caching Best Practices

Tux uses a thread-safe TTL (Time-To-Live) caching system to improve performance and reduce database load. The caching system is built on `TTLCache` and provides specialized cache managers for common use cases.

## Overview

The caching system provides:

- **TTLCache** - Thread-safe TTL cache with automatic expiration
- **GuildConfigCacheManager** - Singleton cache manager for guild configuration data
- **JailStatusCache** - Cache manager for jail status checks
- **Automatic expiration** - Entries expire after their TTL
- **Cache invalidation** - Manual invalidation when data changes
- **Size limits** - Optional maximum size with FIFO eviction

## TTLCache

`TTLCache` is the foundation of Tux's caching system. It provides thread-safe caching with automatic expiration.

### Basic Usage

```python
from tux.shared.cache import TTLCache

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

### Get or Fetch Pattern

The `get_or_fetch` method is useful for caching expensive operations:

```python
def fetch_user_data(user_id: int) -> dict:
    # Expensive database query
    return {"name": "User", "id": user_id}

# Get from cache or fetch if missing
user_data = cache.get_or_fetch(
    f"user_{user_id}",
    lambda: fetch_user_data(user_id)
)
```

### Cache Configuration

Choose appropriate TTL values based on how often data changes:

- **Frequently changing data** (e.g., jail status): 60 seconds
- **Moderately changing data** (e.g., guild config): 300 seconds (5 minutes)
- **Rarely changing data** (e.g., permission ranks): 600 seconds (10 minutes)

## GuildConfigCacheManager

`GuildConfigCacheManager` is a singleton that caches guild configuration data (audit log ID, mod log ID, jail role ID, jail channel ID).

### Usage

```python
from tux.shared.cache import GuildConfigCacheManager

cache_manager = GuildConfigCacheManager()

# Get cached config
config = cache_manager.get(guild_id)
if config:
    audit_log_id = config.get("audit_log_id")
    mod_log_id = config.get("mod_log_id")

# Update cache (only updates provided fields)
cache_manager.set(
    guild_id=guild_id,
    audit_log_id=123456789,
    mod_log_id=987654321
)

# Invalidate cache when config changes
cache_manager.invalidate(guild_id)
```

### Partial Updates

The cache manager supports partial updates using sentinel values. Only explicitly provided fields are updated:

```python
# Only update audit_log_id, leave other fields unchanged
cache_manager.set(guild_id=guild_id, audit_log_id=new_id)

# Update multiple fields
cache_manager.set(
    guild_id=guild_id,
    audit_log_id=new_audit_id,
    mod_log_id=new_mod_id
)
```

## JailStatusCache

`JailStatusCache` caches jail status per (guild_id, user_id) tuple to reduce database queries.

### Usage

```python
from tux.shared.cache import JailStatusCache

jail_cache = JailStatusCache()

# Get cached jail status
is_jailed = jail_cache.get(guild_id, user_id)
if is_jailed is None:
    # Not cached, fetch from database
    is_jailed = await check_jail_status(guild_id, user_id)
    jail_cache.set(guild_id, user_id, is_jailed)

# Invalidate when jail status changes
jail_cache.invalidate(guild_id, user_id)

# Invalidate all entries for a guild
jail_cache.invalidate_guild(guild_id)
```

## Cache Invalidation

Proper cache invalidation is critical for data consistency. Always invalidate caches when data changes:

### In Controller Methods

```python
async def update_config(self, guild_id: int, **kwargs):
    # Update database
    result = await self.update(...)
    
    # Invalidate cache
    cache_manager = GuildConfigCacheManager()
    cache_manager.invalidate(guild_id)
    
    return result
```

### In Permission System

The permission system automatically invalidates caches when permissions change:

```python
# Permission assignment cache is invalidated automatically
await permission_controller.assign_permission_rank(...)

# Command permission cache is invalidated automatically
await command_controller.set_command_permission(...)
```

## Best Practices

### 1. Choose Appropriate TTL Values

- Use shorter TTLs (60-120 seconds) for frequently changing data
- Use longer TTLs (300-600 seconds) for stable configuration data
- Consider data update frequency when setting TTL

### 2. Always Invalidate on Updates

```python
# ❌ Bad: Update database but forget to invalidate cache
await controller.update(...)

# ✅ Good: Invalidate cache after update
await controller.update(...)
cache_manager.invalidate(guild_id)
```

### 3. Use Singleton Cache Managers

For shared data like guild config, use the singleton cache managers:

```python
# ✅ Good: Use singleton
cache_manager = GuildConfigCacheManager()

# ❌ Bad: Create new instance (loses shared state)
cache_manager = GuildConfigCacheManager()
```

### 4. Handle Cache Misses Gracefully

```python
# ✅ Good: Handle None return
cached = cache.get(key)
if cached is None:
    cached = await fetch_data()
    cache.set(key, cached)

# ❌ Bad: Assume cache always has value
cached = cache.get(key)  # Could be None!
process(cached)  # Error if None
```

### 5. Use Batch Operations When Possible

For permission checks, use batch retrieval to reduce cache lookups:

```python
# ✅ Good: Batch retrieval
ranks = await permission_system.get_user_ranks_batch(guild_id, user_ids)

# ❌ Bad: Individual lookups
for user_id in user_ids:
    rank = await permission_system.get_user_rank(guild_id, user_id)
```

### 6. Monitor Cache Performance

Use logging to monitor cache hit rates:

```python
from loguru import logger

cached = cache.get(key)
if cached is None:
    logger.trace(f"Cache miss for {key}")
    cached = await fetch_data()
    cache.set(key, cached)
else:
    logger.trace(f"Cache hit for {key}")
```

## Cache Pre-warming

The permission system supports cache pre-warming on bot startup to reduce cold-start delays:

```python
# Pre-warm caches for a specific guild
await permission_system.pre_warm_guild_cache(guild_id)

# Pre-warm caches for all guilds
await permission_system.pre_warm_all_caches()
```

This is automatically called during bot initialization to improve initial command response times.

## Thread Safety

All cache implementations are thread-safe and can be used concurrently from multiple async tasks. The underlying dictionary operations are protected, and expiration checks are atomic.

## Performance Considerations

- **Memory usage**: Set `max_size` to limit memory consumption
- **TTL tuning**: Balance between freshness and cache hit rate
- **Invalidation frequency**: Too frequent invalidation defeats the purpose of caching
- **Batch operations**: Prefer batch retrieval over individual lookups when possible

## Troubleshooting

### Cache Not Updating

If cached data seems stale:

1. Check if cache invalidation is called after updates
2. Verify TTL is appropriate for update frequency
3. Check if multiple cache instances are being created (use singletons)

### High Memory Usage

If cache memory usage is high:

1. Reduce `max_size` to limit entries
2. Reduce TTL to expire entries faster
3. Ensure proper cache invalidation to remove unused entries

### Cache Misses

If cache hit rate is low:

1. Increase TTL for stable data
2. Pre-warm caches on startup
3. Check if invalidation is too frequent

## Resources

- **Source Code**: `src/tux/shared/cache.py`
- **Permission System Caching**: `src/tux/core/permission_system.py`
- **Guild Config Caching**: `src/tux/database/controllers/guild_config.py`
