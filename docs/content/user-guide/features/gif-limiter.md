# GIF Limiter

Automatically moderate GIF spam in your server.

## What is GIF Limiter?

GIF Limiter automatically:

- Detects GIFs in messages
- Limits GIF posting frequency
- Prevents GIF spam
- Keeps chat readable

## How It Works

### Detection

Bot monitors messages for:

- Tenor GIF links
- GIPHY links
- Direct .gif file uploads
- Discord GIF embeds

### Rate Limiting

When a user posts GIFs:

1. Bot tracks posting frequency
2. If threshold exceeded, deletes the GIF
3. Warns the user (optional)
4. Cooldown period before they can post again

### Automatic Enforcement

- No moderator action needed
- Automatic cleanup
- Fair and consistent
- Configurable per server

## Configuration

### For Self-Hosters

Configure in config file:

```toml
[gif_limiter]
enabled = true
max_gifs_per_minute = 3             # Max GIFs per user per minute
cooldown_period = 60                # Cooldown in seconds
warn_user = true                    # Send warning message
```

**See:** [Admin Configuration - GIF Limiter](../../admin-guide/configuration/features.md#gif-limiter)

## Use Cases

### Preventing Spam

- Users posting GIF walls
- Disrupting conversation flow
- Attention-seeking behavior

### Keeping Chat Readable

- Too many GIFs make chat hard to follow
- Helps maintain conversation quality
- Balances fun with readability

### Fair Enforcement

- Automatic and consistent
- No moderator bias
- Clear limits for everyone

## Best Practices

### Configuration

**Small servers:**

- Higher limit (5-10 GIFs/min)
- Longer cooldown (30-60s)
- Warnings enabled

**Large servers:**

- Stricter limit (2-3 GIFs/min)
- Shorter cooldown (10-30s)
- Warnings optional

### Channel Exceptions

Consider disabling in:

- Meme channels
- Off-topic channels
- Media sharing channels

## Limitations

- Only limits frequency, not content
- Can't detect inappropriate GIFs
- Requires "Manage Messages" permission
- Brief delay in deletion

## Tips

!!! tip "Balance Fun and Order"
    Don't make it too strict - GIFs are fun! Just prevent spam.

!!! info "Automatic Moderation"
    Once configured, no manual enforcement needed!

!!! warning "Not Content Moderation"
    This limits spam, not inappropriate content. Still need moderator review for content.

## Troubleshooting

### GIFs Not Being Limited

**Causes:**

- Feature disabled
- Bot missing permissions
- User has bypass permission

**Solutions:**

- Enable in configuration
- Grant "Manage Messages" permission
- Verify configuration

### Legitimate GIFs Being Deleted

**Causes:**

- Limit too strict
- User posting too quickly

**Solutions:**

- Increase limit in config
- Add cooldown awareness
- Create exempt role for trusted users

## Moderation Integration

GIF limiter works alongside:

- **Manual moderation** - Moderators can still delete
- **Other automod** - Complements other systems
- **Warning system** - Can trigger warnings if configured

## Related Features

- **[Moderation Commands](../commands/moderation.md)** - Manual moderation
- **[Starboard](starboard.md)** - Highlighting good content

## Related Documentation

- **[Configuration](../../admin-guide/configuration/features.md#gif-limiter)** - Admin setup

---

**All features documented!** Explore the [User Guide](../index.md) for more.
