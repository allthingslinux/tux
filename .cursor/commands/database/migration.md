# Database Migration

## Overview

Create and apply Alembic database migrations for schema changes in the Tux project.

## Steps

1. **Create Migration**
   - Run `uv run db dev "description of changes"`
   - Review generated migration file in `src/tux/database/migrations/versions/`
   - Verify upgrade and downgrade functions are correct
   - Check for proper constraint naming

2. **Review Migration**
   - Ensure both `upgrade()` and `downgrade()` are implemented
   - Verify all table/column operations are included
   - Check index creation/dropping
   - Validate enum type handling if applicable

3. **Test Migration**
   - Test upgrade: `uv run db push` (applies pending migrations)
   - Test downgrade: Manually test rollback if needed
   - Verify migration with `uv run db status`
   - Run tests to ensure schema changes work

4. **Apply Migration**
   - Apply to development: `uv run db push`
   - Check migration status: `uv run db status`
   - Verify database health: `uv run db health`

## Checklist

- [ ] Migration file created with descriptive name
- [ ] Both upgrade and downgrade functions implemented
- [ ] All schema changes included (tables, columns, indexes, constraints)
- [ ] Enum types handled correctly if applicable
- [ ] Migration tested (upgrade and downgrade)
- [ ] Tests pass with new schema
- [ ] Migration applied to development database
- [ ] Database health check passes

## See Also

- Related rule: @database/migrations.mdc
- Related command: `/database-health`
- Related command: `/database-reset`
