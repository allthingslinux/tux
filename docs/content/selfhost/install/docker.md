# Docker Installation

Deploy Tux using Docker for easy setup and management.

## Prerequisites

- Docker and Docker Compose installed
- Git installed
- Bot token from Discord Developer Portal

## Quick Start

1. **Clone the repository**:

   ```bash
   git clone https://github.com/allthingslinux/tux.git
   cd tux
   ```

2. **Copy environment template**:

   ```bash
   cp .env.example .env
   ```

3. **Configure environment**:
   Edit `.env` with your settings:

   ```bash
   nano .env
   ```

4. **Start the services**:

   ```bash
   docker-compose up -d
   ```

## Configuration

### Environment Variables

Key variables to configure:

```env
# Discord Bot Token
DISCORD_TOKEN=your_bot_token_here

# Database Configuration
DATABASE_URL=postgresql://user:password@db:5432/tux

# Bot Configuration
BOT_PREFIX=!
BOT_OWNER_ID=your_user_id
```

### Database Setup

The Docker setup includes PostgreSQL. No additional database configuration needed.

## Management Commands

### View Logs

```bash
docker-compose logs -f tux
```

### Restart Services

```bash
docker-compose restart
```

### Update Tux

```bash
git pull
docker-compose down
docker-compose up -d --build
```

## Troubleshooting

### Common Issues

**Bot not starting**:

- Check Discord token is valid
- Verify database connection
- Check logs: `docker-compose logs tux`

**Database connection errors**:

- Ensure PostgreSQL container is running
- Verify DATABASE_URL format
- Check network connectivity

## Next Steps

After successful installation:

- [First Run Setup](first-run.md) - Initial bot configuration
- [Environment Configuration](../config/environment.md) - Advanced settings
- [Monitoring Setup](../ops/monitoring.md) - Production monitoring
