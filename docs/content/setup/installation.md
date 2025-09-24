# Installation

This guide covers all installation methods for Tux, from inviting the bot to your server to
self-hosting.

## Inviting Tux to Your Server

### Prerequisites

- **Server Administrator** permissions in your Discord server
- **Discord account** with verified email

### Invitation Process

1. **Get the Invite Link**
   - Visit the official Tux website or GitHub repository
   - Click the "Invite Tux" button
   - Or use the direct invite link:
`https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=1099511627775&scope=bot%20applications.commands`

2. **Select Your Server**
   - Choose the server from the dropdown
   - Ensure you have Administrator permissions

3. **Configure Permissions**
   - Review the requested permissions
   - Recommended permissions for full functionality:
     - Read Messages/View Channels
     - Send Messages
     - Send Messages in Threads
     - Embed Links
     - Attach Files
     - Read Message History
     - Use External Emojis
     - Add Reactions
     - Manage Messages (for moderation)
     - Kick Members (for moderation)
     - Ban Members (for moderation)
     - Moderate Members (for timeouts)
     - Manage Roles (for jail system)

4. **Complete Setup**
   - Click "Authorize"
   - Complete any CAPTCHA if prompted
   - Tux will join your server

### Initial Configuration

After inviting Tux:

1. **Test Basic Functionality**

   ```bash
   !help
   /help
   ```

2. **Set Command Prefix** (optional)

   ```bash
   !config prefix ?
   ```

3. **Configure Logging Channel**

   ```bash
   !config log_channel #mod-logs
   ```

4. **Set Up Permissions**

   ```bash
   !permissions @Moderators moderator
   ```

## Self-Hosting Options

### Docker (Recommended)

**Prerequisites:**

- Docker and Docker Compose installed
- Basic command line knowledge
- Discord bot token

**Quick Start:**

```bash
# Clone repository
git clone https://github.com/allthingslinux/tux.git
cd tux

# Configure environment
cp .env.example .env
nano .env  # Edit with your settings

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f tux
```text

**Environment Configuration:**

```bash
# .env file
DISCORD_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://tux:password@postgres:5432/tux
LOG_LEVEL=INFO
ENVIRONMENT=production
```text

### Local Installation

**Prerequisites:**

- Python 3.13+
- PostgreSQL 12+
- Git

**Installation Steps:**

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Clone repository
git clone https://github.com/allthingslinux/tux.git
cd tux

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
nano .env

# Set up database
createdb tux
uv run db migrate-push

# Start bot
uv run tux start
```text

### Cloud Platforms

#### Railway

1. **Fork the Repository**
   - Fork Tux repository to your GitHub account

2. **Deploy on Railway**
   - Connect Railway to your GitHub account
   - Create new project from your forked repository
   - Add PostgreSQL plugin


3. **Configure Environment Variables**

   ```bash
   DISCORD_TOKEN=your_bot_token
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   LOG_LEVEL=INFO
   ```

4. **Deploy**
   - Railway will automatically build and deploy
   - Monitor logs for any issues

#### Heroku

1. **Create Heroku App**

   ```bash
   heroku create your-tux-bot
   heroku addons:create heroku-postgresql:mini
   ```

2. **Configure Environment**

   ```bash
   heroku config:set DISCORD_TOKEN=your_bot_token
   heroku config:set LOG_LEVEL=INFO
   ```

3. **Deploy**

   ```bash
   git push heroku main
   heroku logs --tail
   ```

#### DigitalOcean App Platform

1. **Create App**
   - Connect to GitHub repository
   - Configure build settings

2. **Add Database**
   - Add managed PostgreSQL database
   - Configure connection in environment variables

3. **Set Environment Variables**

   ```bash
   DISCORD_TOKEN=your_bot_token
   DATABASE_URL=postgresql://...
   ```

### VPS Installation

**System Requirements:**

- Ubuntu 20.04+ or similar
- 1GB+ RAM (2GB+ recommended)
- 10GB+ storage

**Installation Script:**

```bash
#!/bin/bash
# install.sh

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3 python3-pip postgresql postgresql-contrib git nginx -y

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Create user
sudo useradd -m -s /bin/bash tux
sudo -u tux -i

# Clone and setup
git clone https://github.com/allthingslinux/tux.git
cd tux
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Set up database
sudo -u postgres createdb tux
sudo -u postgres createuser tux
sudo -u postgres psql -c "ALTER USER tux PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE tux TO tux;"

# Run migrations
uv run db migrate-push

# Create systemd service
sudo tee /etc/systemd/system/tux.service > /dev/null <<EOF
[Unit]
Description=Tux Discord Bot
After=network.target postgresql.service

[Service]
Type=simple
User=tux
WorkingDirectory=/home/tux/tux
Environment=PATH=/home/tux/tux/.venv/bin
ExecStart=/home/tux/tux/.venv/bin/python -m tux
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable tux
sudo systemctl start tux
sudo systemctl status tux
```text

## Getting a Discord Bot Token

### Creating a Discord Application

1. **Visit Discord Developer Portal**
   - Go to <https://discord.com/developers/applications>
   - Log in with your Discord account

2. **Create New Application**
   - Click "New Application"
   - Enter a name for your bot
   - Click "Create"

3. **Configure Bot Settings**
   - Go to "Bot" section in sidebar
   - Click "Add Bot"
   - Customize bot username and avatar

4. **Get Bot Token**
   - In Bot section, click "Reset Token"
   - Copy the token (keep it secure!)
   - Never share this token publicly

5. **Configure Bot Permissions**
   - In "OAuth2" > "URL Generator"
   - Select "bot" and "applications.commands" scopes
   - Select required permissions
   - Use generated URL to invite bot

### Security Best Practices

**Token Security:**

- Never commit tokens to version control
- Use environment variables
- Regenerate tokens if compromised
- Restrict bot permissions to minimum required

**Bot Configuration:**

- Enable "Requires OAuth2 Code Grant" if needed
- Configure appropriate intents
- Set up proper permission hierarchy

## Troubleshooting Installation

### Common Issues

**Bot Not Responding:**

1. Check bot token validity
2. Verify bot is online in Discord
3. Check server permissions
4. Review application logs

**Database Connection Issues:**

1. Verify PostgreSQL is running
2. Check connection string format
3. Verify database exists
4. Check user permissions

**Permission Errors:**

1. Verify bot has required permissions
2. Check role hierarchy
3. Ensure bot role is above target roles
4. Re-invite bot with correct permissions

**Docker Issues:**

1. Check Docker daemon is running
2. Verify docker-compose.yml syntax
3. Check port conflicts
4. Review container logs

### Getting Help

**Documentation:**

- Check the troubleshooting section
- Review configuration examples
- Read error messages carefully

**Community Support:**

- Join the official Discord server
- Check GitHub issues
- Ask questions in appropriate channels

**Logs and Debugging:**

```bash
# Check application logs
journalctl -u tux -f

# Docker logs
docker-compose logs -f tux

# Database logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```text

This installation guide covers all major deployment methods. Choose the option that best fits your
technical expertise and requirements.
