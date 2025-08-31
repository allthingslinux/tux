# Tux Setup Test Checklist

This checklist ensures the complete setup works from a clean slate for all user types.

## 🧪 **Pre-Test Setup**

### Prerequisites
- [ ] Fresh system/VM with no previous Tux installation
- [ ] Git installed
- [ ] Python 3.11+ installed (for non-Docker setups)
- [ ] Docker & Docker Compose v2 installed (for Docker setups)
- [ ] PostgreSQL instance available (or SQLite for development)

---

## 🚀 **Developer Setup (Local)**

### 1. Environment Setup
- [ ] Install `uv`: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [ ] Restart shell or source profile
- [ ] Verify: `uv --version`

### 2. Repository Setup
- [ ] `git clone https://github.com/allthingslinux/tux.git`
- [ ] `cd tux`
- [ ] Verify: `ls -la` shows project files

### 3. Configuration Setup
- [ ] `cp env.example .env`
- [ ] Edit `.env` with your settings:
  - [ ] `BOT_TOKEN=your_bot_token_here`
  - [ ] `DATABASE_URL=postgresql://user:pass@localhost:5432/tux`
  - [ ] Or for SQLite: `DATABASE_URL=sqlite:///tux.db`
  - [ ] `BOT_INFO__BOT_NAME=YourBotName`
  - [ ] `BOT_INFO__PREFIX=!`

### 4. Dependencies & Environment
- [ ] `uv sync`
- [ ] Activate virtual environment: `uv venv`
- [ ] Verify: `which python` points to uv venv
- [ ] If Python not found: `uv python install`

### 5. Database Setup
- [ ] Ensure PostgreSQL is running (or SQLite file is writable)
- [ ] `make db-upgrade`
- [ ] Verify: Database tables created successfully
- [ ] Verify: `make db-current` shows current version
- [ ] Verify: `make db-health` shows healthy status

### 6. Bot Startup
- [ ] `make dev` or `make start`
- [ ] Verify: Bot connects to Discord
- [ ] Verify: Bot responds to commands
- [ ] Verify: Bot prefix works correctly

### 7. Feature Testing
- [ ] Test basic commands: `!help`, `!ping`
- [ ] Test bot info: `!botinfo`
- [ ] Verify environment detection: `!env`
- [ ] Test database operations (if applicable)
- [ ] Verify: Database tables exist and are accessible
- [ ] Test: `make db-tables` shows all expected tables

### 8. New Server Scenario Testing
- [ ] Test bot joining new server (if possible)
- [ ] Verify: New guild record created automatically
- [ ] Verify: Default configuration initialized
- [ ] Verify: All feature tables accessible for new server
- [ ] Test: Bot responds to commands in new server immediately

---

## 🐳 **Developer Setup (Docker)**

### 1. Environment Setup
- [ ] Install Docker & Docker Compose v2
- [ ] Verify: `docker --version` and `docker compose version`
- [ ] Ensure Docker daemon is running

### 2. Repository Setup
- [ ] `git clone https://github.com/allthingslinux/tux.git`
- [ ] `cd tux`
- [ ] Verify: `ls -la` shows project files

### 3. Configuration Setup
- [ ] `cp env.example .env`
- [ ] Edit `.env`:
  - [ ] `BOT_TOKEN=your_bot_token_here`
  - [ ] `DATABASE_URL=postgresql://user:pass@localhost:5432/tux`
  - [ ] `DEBUG=true`

### 4. Docker Startup
- [ ] `make docker-dev` or `make prod`
- [ ] Verify: Containers start successfully
- [ ] Verify: Database connection established
- [ ] Verify: Bot connects to Discord
- [ ] Verify: Database migrations run automatically (check logs)
- [ ] Verify: `make db-current` shows expected version

### 5. Testing
- [ ] Check logs: `docker compose logs -f`
- [ ] Test bot functionality
- [ ] Verify environment variables are loaded correctly

---

## 🏭 **Production Setup**

### 1. Environment Setup
- [ ] Install Docker & Docker Compose v2
- [ ] Verify: `docker --version` and `docker compose version`
- [ ] Ensure Docker daemon is running

### 2. Repository Setup
- [ ] `git clone https://github.com/allthingslinux/tux.git`
- [ ] `cd tux`
- [ ] Checkout stable version: `git checkout v1.0.0` (or latest stable)
- [ ] Verify: `git describe --tags`

### 3. Configuration Setup
- [ ] `cp env.example .env`
- [ ] Edit `.env` with production values:
  - [ ] `BOT_TOKEN=your_production_bot_token`
  - [ ] `DATABASE_URL=postgresql://user:pass@prod-host:5432/tux`
  - [ ] `DEBUG=false`
  - [ ] Configure external services (Sentry, GitHub, etc.)

### 4. Docker Production Startup
- [ ] `make docker-prod` or `make prod`
- [ ] Verify: Containers start in background
- [ ] Verify: Health checks pass
- [ ] Verify: Bot connects to Discord
- [ ] Verify: Production migrations run automatically
- [ ] Verify: No debug information in production logs

### 5. Production Verification
- [ ] Check logs: `docker compose logs -f`
- [ ] Verify: No debug information exposed
- [ ] Verify: Bot responds to production prefix
- [ ] Test production features
- [ ] Monitor resource usage

---

## 🔧 **Configuration Validation**

### Environment Variables
- [ ] `ENV` variable works correctly (dev/prod/test)
- [ ] Bot prefix changes based on environment
- [ ] Database URLs are environment-specific
- [ ] External services configuration loads

### Bot Configuration
- [ ] Bot name and version display correctly
- [ ] Command prefix works in all environments
- [ ] User permissions (owner, sysadmins) work
- [ ] Feature flags (XP, snippets, etc.) function

### Database Configuration
- [ ] Connection established successfully
- [ ] Migrations run without errors
- [ ] Tables created with correct schema
- [ ] Environment-specific databases work
- [ ] New server join automatically initializes database
- [ ] Migration rollback works correctly
- [ ] Database health checks pass

---

## 🧹 **Cleanup Testing**

### Local Development
- [ ] Stop bot: `Ctrl+C`
- [ ] Deactivate venv: `deactivate`
- [ ] Remove project: `cd .. && rm -rf tux`
- [ ] Verify: No leftover processes or files

### Docker Development
- [ ] Stop containers: `docker compose down`
- [ ] Remove volumes: `docker compose down -v`
- [ ] Remove project: `cd .. && rm -rf tux`
- [ ] Verify: No leftover containers or volumes

### Production
- [ ] Stop containers: `docker compose down`
- [ ] Remove project: `cd .. && rm -rf tux`
- [ ] Verify: No leftover containers or volumes
- [ ] Verify: No leftover network configurations

---

## 🚨 **Common Issues & Solutions**

### Python/UV Issues
- **Problem**: `uv: command not found`
- **Solution**: Restart shell or source profile after installation

- **Problem**: `uv sync` fails
- **Solution**: Ensure Python 3.11+ is installed, run `uv python install`

### Database Issues
- **Problem**: Migration failures during startup
- **Solution**: Check database permissions, verify connection string, run `make db-upgrade` manually

- **Problem**: New features not working after update
- **Solution**: Verify migrations completed with `make db-current`, check bot logs for errors

- **Problem**: Bot won't start after database changes
- **Solution**: Check migration status, verify database health, restore from backup if needed

### Database Issues
- **Problem**: Connection refused
- **Solution**: Verify PostgreSQL is running, check connection string

- **Problem**: Migration errors
- **Solution**: Check database permissions, ensure clean state

### Docker Issues
- **Problem**: Port conflicts
- **Solution**: Check if ports 5432, 8000 are available

- **Problem**: Build failures
- **Solution**: Ensure Docker has enough resources, check internet connection

### Bot Issues
- **Problem**: Bot doesn't connect
- **Solution**: Verify bot token, check Discord Developer Portal settings

- **Problem**: Commands don't work
- **Solution**: Check bot prefix, verify bot has proper permissions

---

## ✅ **Success Criteria**

### Developer Setup
- [ ] Bot connects to Discord successfully
- [ ] Commands respond with correct prefix
- [ ] Database operations work
- [ ] Environment detection works correctly
- [ ] No configuration errors in logs

### Production Setup
- [ ] Bot runs in production mode
- [ ] Production prefix works correctly
- [ ] No debug information exposed
- [ ] Health checks pass
- [ ] Resource usage is reasonable

### All Setups
- [ ] Configuration loads without errors
- [ ] Environment variables work correctly
- [ ] No leftover processes or files after cleanup
- [ ] Documentation matches actual behavior

---

## 📝 **Notes**

- Test with minimal configuration first, then add complexity
- Document any deviations from expected behavior
- Test both success and failure scenarios
- Verify cleanup removes all traces of the installation
- Test with different operating systems if possible
- Ensure all documented commands work as expected

---

**Last Updated**: $(date)
**Tester**: [Your Name]
**Version**: [Tux Version]
