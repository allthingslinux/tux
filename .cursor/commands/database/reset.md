# Database Reset

## Overview

Safely reset the database by dropping all tables and reapplying migrations from scratch. Use with caution - this will delete all data.

## Steps

1. **Backup Data (if needed)**
   - Export important data if this is production
   - Note any custom data that needs to be preserved
   - Document current database state

2. **Reset Database**
   - Run `uv run db reset` for safe reset
   - This drops all tables and reapplies all migrations
   - Verify reset completed successfully
   - Check database is in clean state

3. **Verify Reset**
   - Check migration status: `uv run db status`
   - Verify all tables recreated
   - Test basic database operations
   - Run health check: `uv run db health`

4. **Re-seed Data (if needed)**
   - Restore any required seed data
   - Verify test data is correct
   - Run tests to ensure everything works

## Warning

⚠️ **This will delete all data in the database!** Only use in development or when you're certain you want to lose all data.

## Checklist

- [ ] Data backed up (if needed)
- [ ] Database reset command executed
- [ ] All migrations reapplied successfully
- [ ] Database health check passes
- [ ] Basic operations work correctly
- [ ] Test data restored (if needed)
- [ ] Tests pass with reset database

## See Also

- Related rule: @database/migrations.mdc
- Related command: `/database-migration`
- Related command: `/database-health`
