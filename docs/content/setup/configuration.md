# Configuration

Complete configuration guide for Tux including environment variables, Discord setup, and database
configuration.

## Environment Variables

### Required Variables

**Discord Configuration:**

```bash
# Your Discord bot token
DISCORD_TOKEN=<your_discord_token>
```

**Database Configuration:**

```bash
# PostgreSQL connection details
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=your_secure_password

# OR use complete database URL override
DATABASE_URL=postgresql+psycopg://user:password@host:port/database
```

### Optional Variables

**Environment Settings:**

```bash
# Enable debug mode
DEBUG=true  # true/false

# External services (optional)
EXTERNAL_SERVICES__SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

**Performance Tuning:**

```bash
# Database connection pool size
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Worker processes (for high-load deployments)
MAX_WORKERS=4

# Enable performance monitoring
ENABLE_METRICS=true
ENABLE_TRACING=false
```

**Feature Toggles:**

```bash
# Enable/disable specific features
ENABLE_LEVELS=true
ENABLE_STARBOARD=true
ENABLE_SNIPPETS=true
```

### Environment File Setup

**Create .env file:**

```bash
# Copy template
cp .env.example .env

# Edit with your settings
nano .env
```

**Example .env file:**

```bash
# Discord
DISCORD_TOKEN=<your_discord_token>

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=secure_password

# Optional: Debug mode
DEBUG=false

# Optional: Error tracking
EXTERNAL_SERVICES__SENTRY_DSN=https://abc123@o123456.ingest.sentry.io/123456
```

## Discord Bot Setup

### Creating Discord Application

1. **Developer Portal**
   - Visit <https://discord.com/developers/applications>
   - Click "New Application"
   - Enter application name

2. **Bot Configuration**
   - Go to "Bot" section
   - Click "Add Bot"
   - Configure bot settings:
     - Username
     - Avatar
     - Public Bot (recommended: disabled)
     - Requires OAuth2 Code Grant (recommended: disabled)

3. **Bot Token**
   - Click "Reset Token"
   - Copy token securely
   - Add to environment variables

### Bot Permissions

**Required Permissions:**

```text
Read Messages/View Channels    - Basic functionality
Send Messages                  - Command responses
Send Messages in Threads       - Thread support
Embed Links                    - Rich embeds
Attach Files                   - File uploads
Read Message History           - Context awareness
Use External Emojis           - Custom emojis
Add Reactions                 - Reaction features
```

**Moderation Permissions:**

```text
Manage Messages               - Message deletion
Kick Members                  - Kick command
Ban Members                   - Ban command
Moderate Members              - Timeout command
Manage Roles                  - Jail system
```

**Permission Integer:** `1099511627775`

### OAuth2 Configuration

**Scopes:**

- `bot` - Basic bot functionality
- `applications.commands` - Slash commands

**Invite URL Template:**

```text
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=1099511627775&scope=bot%20applications.commands
```

### Intents Configuration

**Required Intents:**

```python
# Automatically configured in bot
intents = discord.Intents.default()
intents.message_content = True  # For prefix commands
intents.members = True          # For member events
intents.guilds = True          # For guild events
```

## Database Configuration

### PostgreSQL Setup

**Local Installation:**

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql

# Start service
sudo systemctl start postgresql
# or
brew services start postgresql
```

**Database Creation:**

```sql
-- Connect as postgres user
sudo -u postgres psql

-- Create database and user
CREATE DATABASE tux;
CREATE USER tux WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE tux TO tux;

-- Optional: Set connection limit
ALTER USER tux CONNECTION LIMIT 20;
```

**Connection String Format:**

```text
postgresql://[user[:password]@][host][:port][/database][?param1=value1&...]

Examples:
postgresql://tux:password@localhost:5432/tux
postgresql://tux:password@localhost:5432/tux?sslmode=require
postgresql://tux:password@db.example.com:5432/tux?pool_size=20
```

### Database Migrations

**Initial Setup:**

```bash
# Run all migrations
uv run db migrate-push

# Check migration status
uv run db status

# Check database health
uv run db health
```

**Creating Migrations:**

```bash
# Generate new migration
uv run db migrate-generate "description of changes"

# Review generated migration file
# Edit if necessary

# Apply migration
uv run db migrate-push
```

### Connection Pooling

**Configuration:**

```bash
# Environment variables
DB_POOL_SIZE=20        # Initial pool size
DB_MAX_OVERFLOW=30     # Maximum overflow connections
DB_POOL_TIMEOUT=30     # Connection timeout (seconds)
DB_POOL_RECYCLE=3600   # Connection recycle time (seconds)
```

**Connection String Parameters:**

```text
postgresql://user:pass@host:5432/db?pool_size=20&max_overflow=30&pool_timeout=30
```

### Backup Configuration

**Automated Backups:**

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U tux tux | gzip > /backups/tux_$DATE.sql.gz

# Keep only last 30 days
find /backups -name "tux_*.sql.gz" -mtime +30 -delete
```

**Cron Job:**

```bash
# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh
```

## Bot Configuration

### In-Discord Configuration

**Basic Settings:**

```bash
# Configure logging
/config logs set Public

# Set up channels (interactive setup)
/config channels set

# Change command prefix
/config prefix set ?
```

**Permission Levels:**

```bash
# Set user permission levels
!permissions @user moderator
!permissions @role supporter

# Available levels:
# member, supporter, junior_moderator, moderator, 
# senior_moderator, administrator, owner
```

**Feature Configuration:**

```bash
# Starboard setup
!config starboard_channel #starboard
!config starboard_threshold 5

# Auto-role for new members
!config autorole @Member

# Welcome messages
!config welcome_channel #general
!config welcome_message "Welcome {user} to {guild}!"
```

### Configuration File

**config.yml (optional):**

```yaml
# Guild-specific settings
guilds:
  123456789012345678:  # Guild ID
    prefix: "?"
    log_channel: 987654321098765432
    jail_role: 111222333444555666
    
# Global settings
global:
  default_prefix: "!"
  max_cases_per_page: 10
  command_cooldown: 5
```

## External Services Configuration

### Sentry Error Tracking

**Setup:**

1. Create Sentry account at <https://sentry.io>
2. Create new project
3. Get DSN from project settings
4. Add to environment variables

**Configuration:**

```bash
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=v1.0.0

# Optional: Performance monitoring
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

**Features:**

- Automatic error capture
- Performance monitoring
- Release tracking
- User context
- Custom tags and context

### Logging Configuration

**Log Levels:**

- `DEBUG` - Detailed diagnostic information
- `INFO` - General operational messages
- `WARNING` - Warning messages for potential issues
- `ERROR` - Error messages for failures

**Log Formats:**

```python
# Structured logging with context
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "message": "Command executed",
  "command": "ban",
  "user_id": 123456789,
  "guild_id": 987654321
}
```

**Log Rotation:**

```bash
# /etc/logrotate.d/tux
/var/log/tux/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 tux tux
}
```

## Security Configuration

### Token Security

**Best Practices:**

- Never commit tokens to version control
- Use environment variables or secrets management
- Rotate tokens regularly
- Monitor for token leaks

**Secrets Management:**

```bash
# Docker secrets
echo "your_token" | docker secret create discord_token -

# Kubernetes secrets
kubectl create secret generic tux-secrets --from-literal=discord-token=your_token

# HashiCorp Vault
vault kv put secret/tux discord_token=your_token
```

### Database Security

**Connection Security:**

```bash
# SSL/TLS connections
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Certificate verification
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=verify-full&sslcert=client.crt&sslkey=client.key&sslrootcert=ca.crt
```

**Access Control:**

```sql
-- Restrict database access
REVOKE ALL ON DATABASE tux FROM PUBLIC;
GRANT CONNECT ON DATABASE tux TO tux;

-- Limit connection sources
# pg_hba.conf
host tux tux 10.0.0.0/8 md5
```

### Network Security

**Firewall Configuration:**

```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 5432/tcp  # PostgreSQL (if external)
sudo ufw enable

# iptables
iptables -A INPUT -p tcp --dport 5432 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 5432 -j DROP
```

## Monitoring Configuration

### Health Checks

**Application Health:**

```bash
# Built-in health check endpoint
curl http://localhost:8080/health

# Database connectivity check
uv run db health

# Bot status check
uv run tux status
```

**Automated Monitoring:**

```bash
#!/bin/bash
# monitor.sh
if ! systemctl is-active --quiet tux; then
    echo "Tux service is down"
    systemctl restart tux
    # Send alert
fi
```

### Metrics Collection

**Prometheus Metrics:**

```bash
# Enable metrics endpoint
ENABLE_METRICS=true
METRICS_PORT=8080

# Metrics available at http://localhost:8080/metrics
```

**Key Metrics:**

- Command execution count
- Command response time
- Database query performance
- Error rates
- Memory usage
- Active connections

This configuration guide covers all aspects of setting up and configuring Tux for optimal
performance and security.
