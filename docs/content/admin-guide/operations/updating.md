# Updating Tux

Keep your Tux instance up to date.

## Docker Compose

```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose up -d --build

# Apply new migrations
docker compose exec tux uv run db push

# Verify
docker compose logs --tail=50 tux
```

## VPS/Systemd

```bash
# As tux user
sudo -u tux -i
cd ~/tux

# Pull updates
git pull

# Update dependencies
uv sync

# Exit tux user
exit

# Run migrations
sudo -u tux bash -c "cd ~/tux && uv run db push"

# Restart service
sudo systemctl restart tux

# Check status
sudo systemctl status tux
sudo journalctl -u tux -f
```

## Update Checklist

Before updating:

- [x] Backup database
- [x] Review changelog/release notes
- [x] Check for breaking changes
- [x] Plan maintenance window (if needed)

After updating:

- [x] Apply migrations
- [x] Restart bot
- [x] Check logs for errors
- [x] Test critical commands
- [x] Monitor for issues

## Version Pinning

For stability, pin to specific version:

```bash
git checkout v1.0.0
docker compose build
```

## Rollback

If update causes issues:

```bash
# Rollback code
git checkout previous_version

# Rollback database (if needed)
uv run db downgrade -1

# Rebuild and restart
docker compose up -d --build
```

## Related

- **[Troubleshooting](troubleshooting.md)**
- **[Backups](../database/backups.md)**

---

*Always backup before updating!*
