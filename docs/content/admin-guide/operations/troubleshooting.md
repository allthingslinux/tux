# Troubleshooting

Common issues and solutions.

## Bot Issues

### Bot Won't Start

1. Check logs: `docker compose logs tux`
2. Verify BOT_TOKEN in `.env`
3. Check database connection
4. Verify all required env vars set

### Bot Shows Offline

1. Check token validity
2. Verify internet connection
3. Check Discord API status
4. Review connection logs

### Commands Not Working

1. Wait for Discord sync (1-2 min)
2. Verify bot permissions
3. Check user permission ranks
4. Try `/dev sync_tree`

## Database Issues

### Can't Connect

1. Check PostgreSQL running: `docker compose ps tux-postgres`
2. Verify connection details in `.env`
3. Test connection: `uv run db health`

### Migration Failures

1. Check migration status: `uv run db status`
2. Review migration logs
3. Try: `uv run db reset`

## Performance Issues

### High CPU Usage

1. Check for infinite loops in logs
2. Monitor database queries: `uv run db queries`
3. Review error rate

### High Memory Usage

1. Check connection pool size
2. Monitor with: `docker stats tux`
3. Restart if needed

## Discord Issues

### Permission Errors

1. Verify bot has required Discord permissions
2. Check bot role hierarchy
3. Re-invite bot with correct scopes

### Rate Limiting

1. Check Discord API status
2. Reduce command usage
3. Wait for rate limit to reset

## Need Help?

- **[Discord Support](https://discord.gg/gpmSjcjQxg)**
- **[GitHub Issues](https://github.com/allthingslinux/tux/issues)**
- **[Logging Guide](logging.md)**

---

*Comprehensive troubleshooting guide in progress.*
