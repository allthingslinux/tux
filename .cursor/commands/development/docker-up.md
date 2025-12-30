# Docker Up

## Overview

Start Docker services (PostgreSQL, Adminer) for local development.

## Steps

1. **Start Docker Services**
   - Run `docker compose up -d`
   - Wait for services to start
   - Verify containers are running
   - Check service health

2. **Verify Services**
   - Check PostgreSQL is accessible
   - Verify Adminer is available
   - Test database connection
   - Check service logs if needed

3. **Check Service Status**
   - Review container status
   - Verify ports are exposed correctly
   - Check for any startup errors
   - Ensure services are healthy

## Checklist

- [ ] Docker services started
- [ ] PostgreSQL container running
- [ ] Adminer container running
- [ ] Database connection works
- [ ] Services are healthy
- [ ] No startup errors

## See Also

- Related command: `/docker-down`
- Related command: `/setup-project`
- Related command: `/health`
