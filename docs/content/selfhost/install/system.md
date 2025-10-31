# Bare Metal Installation

Install Tux directly on your system without Docker.

## Prerequisites

- Python 3.11+
- PostgreSQL 13+ (or SQLite for development)
- Git
- Bot token from Discord Developer Portal

## Installation Steps

1. **Clone the repository**:

   ```bash
   git clone https://github.com/allthingslinux/tux.git
   cd tux
   ```

2. **Create virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**:

   ```bash
   pip install -e .
   ```

4. **Set up database**:

   ```bash
   # For PostgreSQL
   createdb tux
   
   # Run migrations
   tux db migrate
   ```

5. **Configure environment**:

   ```bash
   cp .env.example .env
   nano .env
   ```

## Configuration

### Environment Variables

```env
# Discord Bot Token
DISCORD_TOKEN=your_bot_token_here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/tux

# Bot Configuration
BOT_PREFIX=!
BOT_OWNER_ID=your_user_id
```

### Database Setup

#### PostgreSQL (Recommended)

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE tux;
CREATE USER tux_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE tux TO tux_user;
\q
```

#### SQLite (Development)

```env
DATABASE_URL=sqlite:///tux.db
```

## Running Tux

### Development Mode

```bash
tux run
```

### Production Mode

```bash
# Using systemd (recommended)
sudo systemctl enable tux
sudo systemctl start tux

# Or using screen/tmux
screen -S tux
tux run
# Ctrl+A, D to detach
```

## Service Management

### Systemd Service

Create `/etc/systemd/system/tux.service`:

```ini
[Unit]
Description=Tux
After=network.target

[Service]
Type=simple
User=tux
WorkingDirectory=/opt/tux
ExecStart=/opt/tux/venv/bin/tux run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Common Issues

**Permission errors**:

- Ensure user has proper permissions
- Check file ownership
- Verify database user permissions

**Database connection**:

- Verify PostgreSQL is running
- Check connection string format
- Test database connectivity

**Python dependencies**:

- Ensure virtual environment is activated
- Check Python version compatibility
- Reinstall dependencies if needed

## Next Steps

After successful installation:

- [First Run Setup](first-run.md) - Initial bot configuration
- [Environment Configuration](../config/environment.md) - Advanced settings
- [Monitoring Setup](../ops/monitoring.md) - Production monitoring
