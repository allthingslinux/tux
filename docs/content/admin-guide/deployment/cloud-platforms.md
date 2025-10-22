# Cloud Platform Deployment

Deploy Tux on cloud platforms for managed infrastructure.

## Overview

Cloud platforms offer:

- Managed infrastructure
- Automatic scaling
- Built-in monitoring
- Easy deployment
- Free tiers (some platforms)

## Popular Platforms

### Railway

**Best for:** Quick deployment with managed database

**Pros:**

- Free $5/month credit
- Managed PostgreSQL
- GitHub integration
- Automatic deploys
- Simple interface

**Setup:**

1. Fork Tux repository to your GitHub
2. Sign up at [railway.app](https://railway.app)
3. Create new project from GitHub repo
4. Add PostgreSQL database service
5. Set environment variables:

   ```bash
   BOT_TOKEN=your_token
   POSTGRES_HOST=${{Postgres.POSTGRES_HOST}}
   POSTGRES_DB=${{Postgres.POSTGRES_DB}}
   POSTGRES_USER=${{Postgres.POSTGRES_USER}}
   POSTGRES_PASSWORD=${{Postgres.POSTGRES_PASSWORD}}
   ```

6. Deploy!

---

### DigitalOcean App Platform

**Best for:** Managed deployment with more control

**Pricing:** Starts at $5/month

**Setup:**

1. Create app from GitHub repository
2. Add managed PostgreSQL database
3. Configure environment variables
4. Set build command: `uv sync`
5. Set run command: `uv run tux start`
6. Deploy

---

### Render

**Best for:** Free tier and simple deployment

**Pros:**

- Free tier available
- Auto SSL
- Auto deploy from GitHub

**Setup:**

1. Connect GitHub repository
2. Create PostgreSQL database
3. Create web service (even though it's a bot)
4. Set environment variables
5. Build command: `uv sync`
6. Start command: `uv run tux start`

---

### Heroku

**Best for:** Traditional PaaS experience

**Note:** No longer has free tier

**Setup:**

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login

# Create app
heroku create your-tux-bot

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set BOT_TOKEN=your_token
heroku config:set ENVIRONMENT=production

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

---

## General Cloud Deployment Steps

### 1. Prepare Repository

- Fork Tux repository
- Or create your own deploy branch
- Configure for your cloud platform

### 2. Set Up Database

Most platforms offer managed PostgreSQL:

- Create PostgreSQL instance
- Note connection details
- Usually get DATABASE_URL or individual connection params

### 3. Configure Environment

Set environment variables in platform dashboard:

```bash
BOT_TOKEN=your_discord_token
POSTGRES_HOST=db_host
POSTGRES_PORT=5432
POSTGRES_DB=tuxdb
POSTGRES_USER=user
POSTGRES_PASSWORD=password
ENVIRONMENT=production
DEBUG=false
```

### 4. Configure Build

**Build Command:**

```bash
uv sync
```

**Start Command:**

```bash
uv run tux start
```

Or create a `Procfile`:

```text
worker: uv run tux start
```

### 5. Deploy

- Connect GitHub repository
- Trigger deployment
- Watch build logs
- Verify bot comes online in Discord

### 6. Run Migrations

After first deploy:

```bash
# Via platform CLI or console
uv run db push
```

## Platform-Specific Considerations

### Railway Considerations

- Uses Nixpacks for build detection
- Automatic PORT assignment (not needed for Discord bot)
- Easy database connection via variables
- Free $5/month credit

### DigitalOcean

- Requires explicit build/run commands
- Good monitoring built-in
- Easy scaling
- Managed database recommended

### Render Considerations

- Free tier available (limited)
- Auto-deploy from GitHub
- Good for small bots
- May sleep on free tier

### Heroku Considerations

- Mature platform
- Extensive add-ons
- No free tier anymore
- Good documentation

## Cost Estimates

| Platform | Compute | Database | Total/Month |
|----------|---------|----------|-------------|
| Railway | Free ($5 credit) | $5-10 | ~$5-10 |
| DigitalOcean | $5 | $15 | $20 |
| Render | Free-$7 | $7 | $7-14 |
| Heroku | $7 | $5 | $12 |
| VPS (Hetzner) | €4 | Self-host | €4 (~$4) |

*Prices approximate, check current pricing

## Advantages & Disadvantages

### ✅ Advantages

- No server management
- Automatic backups (usually)
- Built-in monitoring
- Easy scaling
- Professional infrastructure

### ❌ Disadvantages

- Monthly costs
- Platform lock-in
- Less control
- May have limitations
- Potential cold starts (free tiers)

## Migration Between Platforms

### Backup Current Data

```bash
# Export database
pg_dump postgres://user:pass@host:port/db > backup.sql

# Export configuration
tar -czf config_backup.tar.gz .env config/
```

### Deploy to New Platform

1. Set up new platform
2. Deploy Tux
3. Restore database
4. Test functionality
5. Update DNS/webhooks if needed

### Rollback Plan

- Keep old deployment running during migration
- Test thoroughly before shutting down old instance
- Have database backups ready

## Monitoring on Cloud Platforms

Most platforms provide:

- **Logs** - Application logs viewer
- **Metrics** - CPU, RAM, network usage
- **Alerts** - Uptime and error alerts
- **Health Checks** - Automatic restart on failure

Configure health check endpoint if supported.

## Tips

!!! tip "Use Managed Database"
    For cloud deployments, use the platform's managed database - much easier than self-hosting PostgreSQL.

!!! tip "Watch Costs"
    Monitor your usage to avoid unexpected bills. Set up billing alerts.

!!! tip "Environment Variables"
    Use platform environment variables, not committed `.env` files!

!!! warning "Free Tiers"
    Free tiers may have limitations like cold starts, sleep after inactivity, or usage caps.

## Troubleshooting

### Build Failures

- Check build logs carefully
- Verify `pyproject.toml` and `uv.lock` are committed
- Ensure Python 3.13+ is available
- Check for platform-specific build requirements

### Database Connection Failed

- Verify DATABASE_URL or connection parameters
- Check database is in same region
- Verify network connectivity
- Check database is running

### Bot Offline

- Check platform dashboard for errors
- View application logs
- Verify bot token is correct
- Check Discord API status

## Best Practices

- **Use managed database** - Don't self-host DB on cloud
- **Set up alerts** - Know when things break
- **Enable auto-deploy** - From GitHub pushes
- **Monitor costs** - Set billing alerts
- **Regular backups** - Even with managed DB
- **Test before production** - Use staging environment

## Next Steps

1. **[Configure Tux](../configuration/index.md)** - Set up your instance
2. **[Set Up Monitoring](../operations/monitoring.md)** - Watch for issues
3. **[Configure Backups](../database/backups.md)** - Protect data

---

**Easier Alternative:** Try [Docker Compose](docker-compose.md) on your own VPS.
