# Database Health Check

## Overview

Check database connection and health status for the Tux PostgreSQL database.

## Steps

1. **Check Connection**
   - Run `uv run db health`
   - Verify connection to PostgreSQL database
   - Check database URL configuration
   - Verify environment variables are set

2. **Verify Services**
   - Ensure Docker services are running: `uv run docker up`
   - Check PostgreSQL container status
   - Verify database is accessible
   - Check connection pool status

3. **Diagnose Issues**
   - Review connection errors in logs
   - Check `.env` file for correct database URL
   - Verify `POSTGRES_*` environment variables
   - Check Docker container logs if using Docker

4. **Test Operations**
   - Verify database service can create sessions
   - Test basic query execution
   - Check migration status: `uv run db status`
   - Verify models can be accessed

## Checklist

- [ ] Database connection successful
- [ ] Environment variables configured correctly
- [ ] Docker services running (if using Docker)
- [ ] Database URL is valid
- [ ] Connection pool working
- [ ] Basic queries execute successfully
- [ ] Migration status accessible

## See Also

- Related rule: @database/services.mdc
- Related command: `/database-migration`
- Related command: `/database-reset`
