# Setup Project

## Overview

Set up the Tux project for local development with all required dependencies and configuration.

## Steps

1. **Install Dependencies**
   - Run `uv sync` to install all dependencies
   - Verify dependencies installed correctly
   - Check for any installation errors
   - Review installed packages

2. **Configure Environment**
   - Copy `.env.example` to `.env`
   - Configure required environment variables
   - Set Discord bot token
   - Configure database connection

3. **Configure Application**
   - Copy `config/config.toml.example` to `config/config.toml`
   - Update configuration as needed
   - Verify configuration is valid
   - Test configuration loading

4. **Start Services**
   - Start Docker services: `docker compose up -d`
   - Wait for PostgreSQL to be ready
   - Verify database connection: `uv run db health`
   - Check all services are running

5. **Initialize Database**
   - Run `uv run db init` to initialize database
   - Apply migrations: `uv run db push`
   - Verify database schema
   - Test database operations

6. **Verify Setup**
   - Run quality checks: `uv run dev all`
   - Run tests: `uv run test quick`
   - Start bot: `uv run tux start --debug`
   - Verify bot connects to Discord

## Checklist

- [ ] Dependencies installed with `uv sync`
- [ ] Environment variables configured
- [ ] Configuration files created
- [ ] Docker services started
- [ ] Database initialized
- [ ] Migrations applied
- [ ] Quality checks pass
- [ ] Tests pass
- [ ] Bot starts successfully

## See Also

- Related command: `/docker-up`
- Related command: `/docker-down`
- Related rule: @core/tech-stack.mdc
