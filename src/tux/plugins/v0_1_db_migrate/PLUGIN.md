# Database Migration Plugin

Plugin for migrating data from the old Prisma/Supabase database (pre v0.1.0) to the new SQLModel/PostgreSQL database (v0.1.0+).

## Overview

This plugin provides a comprehensive migration solution with:

- **Schema Inspection**: Audit old database structure
- **Model Mapping**: Convert Prisma models to SQLModel models
- **Data Extraction**: Batch processing with transformation
- **Migration Execution**: Transaction-based migration with rollback support
- **Validation**: Post-migration verification and reporting

## Installation

The plugin is automatically loaded from `src/tux/plugins/v0_1_db_migrate/`.

## Configuration

Set the old database URL (required for real migrations):

```bash
export OLD_DATABASE_URL="postgresql://user:password@host:port/database"
```

Or add to your `.env` file:

```bash
OLD_DATABASE_URL=postgresql://user:password@host:port/database
```

## Commands

All commands require bot owner or sysadmin permissions.

### `$migrate audit`

Inspect the old database schema and generate a comprehensive report.

```bash
$migrate audit
```

Generates:

- List of all tables
- Column metadata for each table
- Foreign key relationships
- Index information

### `$migrate validate-schema`

Validate old database schema for migration compatibility.

```bash
$migrate validate-schema
```

Checks the schema report against expected mappings to identify potential issues before migration execution.

### `$migrate check-pk [table_name]`

Check primary key constraint for a specific table.

```bash
$migrate check-pk AFKModel
```

### `$migrate check-duplicates [table_name]`

Check for duplicate member_id values across guilds in a table.

```bash
$migrate check-duplicates AFKModel
```

### `$migrate map`

Display model mapping configuration showing how old Prisma models map to new SQLModel models.

```bash
$migrate map
```

### `$migrate dry-run [table_name]`

Test migration without committing changes. Use this to verify the migration will work correctly.

```bash
$migrate dry-run          # Test all tables
$migrate dry-run guild    # Test single table
```

### `$migrate table <table_name>`

Migrate a single table from old to new database.

```bash
$migrate table guild
```

### `$migrate all`

Migrate all tables in dependency order. **Requires confirmation**.

```bash
$migrate all
```

⚠️ **WARNING**: This will migrate ALL data. Make sure you have backups and have tested with dry-run first!

### `$migrate validate`

Validate migrated data by comparing row counts, spot-checking records, and verifying relationships.

```bash
$migrate validate
```

### `$migrate status`

Show migration status and row counts for each table.

```bash
$migrate status
```

## Migration Workflow

### 1. Preparation

1. **Backup databases**: Create backups of both old and new databases
2. **Set environment**: Configure `OLD_DATABASE_URL` if needed
3. **Initialize new database**: Ensure new database is initialized with migrations

### 2. Audit Phase

```bash
$migrate audit
```

Review the schema report to understand the old database structure.

### 3. Testing Phase

```bash
$migrate dry-run
```

Test the migration without committing changes. Review any errors or warnings.

### 4. Migration Phase

For single table:

```bash
$migrate table guild
```

For all tables:

```bash
$migrate all
```

Confirm when prompted. Monitor progress and handle any errors.

### 5. Validation Phase

```bash
$migrate validate
```

Review the validation report to ensure data integrity.

### 6. Verification

```bash
$migrate status
```

Check row counts and verify all tables were migrated successfully.

## ⚠️ CRITICAL: Migration Safety

**IMPORTANT**: Migration commands (`$migrate all`, etc.) are Discord bot commands that require the bot to be running. However, the bot should **NOT be processing user events** during migration to prevent data conflicts.

### DO NOT

1. **Start new bot with fresh database and let users interact before migration**
   - Users will create new data (levels, XP, etc.)
   - Migration will try to insert old data
   - This causes conflicts and potential data loss

2. **Run migration while old bot is still active**
   - Old bot continues writing to old database
   - Migration reads from old database
   - New bot writes to new database
   - Data gets out of sync

3. **Run migration while new bot is processing user events**
   - Users interacting during migration create new records
   - Migration may overwrite or conflict with new data
   - Timestamps get mixed up

### DO

1. **Stop old bot BEFORE migration**
   - Prevents new data creation in old database
   - Ensures consistent snapshot

2. **Run migration with bot in maintenance mode**
   - Bot must be running to execute Discord commands (`$migrate all`)
   - Enable maintenance mode to prevent user events from being processed
   - **How to enable**: Set `MAINTENANCE_MODE=true` in your `.env` file or environment
   - During maintenance mode:
     - Only bot owners and sysadmins can use commands (migration commands will work)
     - All event processing is skipped (no XP gain, no GIF limiting, etc.)
     - Users will see a maintenance message if they try to use commands
   - Alternative options:
     - Use a test/development bot token (not production)
     - Run migration during low-traffic period and monitor closely

3. **Test with dry-run first**
   - Validates migration will work
   - Identifies issues before committing

4. **Backup everything**
   - Both old and new databases
   - Old codebase
   - Configuration files

## Deployment Scenarios

### Scenario 1: Fresh Installation (Recommended)

**Use Case**: You're migrating from an old codebase to the new codebase for the first time.

**Prerequisites**:

- Old bot is still running with old database
- You have access to the old database connection string
- You have a new server/environment ready for the new bot

**Steps**:

1. **Prepare New Environment**

   ```bash
   # Clone the new codebase
   git clone <new-repo-url>
   cd tux
   uv sync
   
   # Configure new bot (but DON'T start it yet)
   cp .env.example .env
   cp config/config.toml.example config/config.toml
   # Edit .env and config/config.toml with new bot settings
   ```

2. **Set Up New Database**

   ```bash
   # Initialize new database (creates tables, runs migrations)
   uv run db push
   
   # Verify database is empty/ready
   uv run db status
   ```

3. **Configure Migration Plugin**

   ```bash
   # Set old database URL (from your old bot's database)
   export OLD_DATABASE_URL="postgresql://user:password@old-host:port/old-database"
   
   # Or add to .env file:
   # OLD_DATABASE_URL=postgresql://user:password@old-host:port/old-database
   ```

4. **Start New Bot (Migration Mode)**

   ```bash
   # Start the bot (it will connect but won't process events yet)
   # Use a different token or run in maintenance mode if possible
   uv run tux start
   ```

6. **Run Migration Commands** (in Discord or via script)

   ```bash
   # In Discord (as bot owner/sysadmin):
   $migrate audit          # Inspect old database schema
   $migrate validate-schema # Validate compatibility
   $migrate dry-run        # Test migration without committing
   $migrate all            # Run actual migration (requires confirmation)
   $migrate validate       # Verify migrated data
   $migrate status         # Check migration status
   ```

7. **Stop Old Bot**

   ```bash
   # On old server/environment
   # Stop the old bot process
   # This prevents users from creating new data in old database
   ```

8. **Disable Maintenance Mode** (after migration completes)

   ```bash
   # Remove from .env or set to false:
   MAINTENANCE_MODE=false
   ```

9. **Switch Bot Token** (if using same Discord bot)

   ```bash
   # Update .env with production bot token
   # Or switch environment variables
   ```

8. **Restart New Bot** (Production Mode)

   ```bash
   # Restart bot with production token
   uv run tux start
   ```

11. **Verify Everything Works**

- Test critical commands
- Check levels/XP are preserved
- Verify guild configs are intact
- Monitor for errors

### Scenario 2: Same Server Migration

**Use Case**: You're upgrading the bot on the same server.

**Steps**:

1. **Backup Everything**

   ```bash
   # Backup old database
   pg_dump old_database > backup_$(date +%Y%m%d).sql
   
   # Backup old codebase
   cp -r old-tux old-tux-backup
   ```

2. **Stop Old Bot**

   ```bash
   # Stop the old bot process completely
   # This is CRITICAL - prevents data conflicts
   systemctl stop old-tux  # or however you run it
   ```

3. **Set Up New Codebase**

   ```bash
   # Clone new codebase to different directory
   git clone <new-repo-url> new-tux
   cd new-tux
   uv sync
   
   # Configure with same bot token
   cp .env.example .env
   # Edit .env with same BOT_TOKEN but new DATABASE_URL
   ```

4. **Set Up New Database**

   ```bash
   # Create new database
   createdb new_tux_database
   
   # Initialize with migrations
   uv run db push
   ```

5. **Configure Migration**

   ```bash
   # Set old database URL (pointing to old database)
   export OLD_DATABASE_URL="postgresql://user:password@localhost:5432/old_database"
   ```

6. **Enable Maintenance Mode** (recommended)

   ```bash
   # Add to .env file:
   MAINTENANCE_MODE=true
   ```

7. **Run Migration**

   ```bash
   # Start bot - MUST be running to execute Discord commands
   # If MAINTENANCE_MODE=true, user events will be automatically skipped
   uv run tux start
   
   # In Discord (as bot owner/sysadmin), run migration commands:
   $migrate audit
   $migrate dry-run
   $migrate all
   $migrate validate
   ```

8. **Disable Maintenance Mode and Switch to Production**

   ```bash
   # Stop bot
   # Remove MAINTENANCE_MODE from .env or set to false
   MAINTENANCE_MODE=false
   # Update .env if needed
   # Restart bot
   uv run tux start
   ```

### Scenario 3: Testing Migration (Development)

**Use Case**: You want to test migration without affecting production.

**Steps**:

1. **Set Up Test Environment**

   ```bash
   # Clone new codebase
   git clone <new-repo-url> test-tux
   cd test-tux
   uv sync
   ```

2. **Create Test Database**

   ```bash
   # Create separate test database
   createdb test_tux_database
   
   # Update .env with test database URL
   # DATABASE_URL=postgresql://user:password@localhost:5432/test_tux_database
   
   # Initialize
   uv run db push
   ```

3. **Configure Migration**

   ```bash
   # Point to production old database (read-only if possible)
   export OLD_DATABASE_URL="postgresql://user:password@prod-host:5432/old_database"
   ```

4. **Test Migration**

   ```bash
   # Start bot with test token
   uv run tux start
   
   # Run migration in dry-run mode first
   $migrate dry-run
   
   # If successful, run actual migration
   $migrate all
   $migrate validate
   ```

5. **Verify Test Results**
   - Check all data migrated correctly
   - Test bot functionality
   - Compare with production data

## Migration Timing

### Best Practice: Zero-Downtime Window

1. **Preparation Phase** (can be done while old bot runs):
   - Set up new environment
   - Configure migration plugin
   - Run `migrate audit` and `migrate validate-schema`
   - Run `migrate dry-run` to test

2. **Migration Window** (requires downtime):
   - Stop old bot
   - Start new bot (in restricted mode - not processing user events)
   - Run `$migrate all` (bot must be running to execute Discord commands)
   - Run `$migrate validate`
   - Switch to production mode (if using test token) or enable event processing
   - Verify functionality

3. **Rollback Plan** (if migration fails):
   - Stop new bot
   - Restore new database from backup
   - Restart old bot
   - Fix issues and retry

## Production Deployment

### Pre-Migration Checklist

- [ ] Backups created for both databases
- [ ] Old database URL configured (`OLD_DATABASE_URL` environment variable)
- [ ] New database initialized with migrations (`uv run db push`)
- [ ] Dry-run completed successfully (`$migrate dry-run`)
- [ ] **Old bot stopped** (critical - prevents data conflicts)
- [ ] **Maintenance mode enabled** (`MAINTENANCE_MODE=true` in `.env`) - prevents user event processing
- [ ] **New bot ready** (must be running to execute Discord commands)
- [ ] Maintenance window scheduled
- [ ] Rollback plan prepared

### Migration Steps

1. **Stop old bot**: Shut down the old bot instance completely
   - This prevents new data from being created in the old database
   - Ensures a consistent snapshot for migration

2. **Enable maintenance mode** (recommended):

   ```bash
   # Add to .env file:
   MAINTENANCE_MODE=true
   
   # Or set as environment variable:
   export MAINTENANCE_MODE=true
   ```

   - Maintenance mode prevents user events from being processed
   - Only bot owners/sysadmins can use commands (migration commands will work)
   - Users will see a maintenance message if they try to use commands

3. **Start new bot** (required for Discord commands):
   - Bot MUST be running to execute `$migrate` commands via Discord
   - Bot should connect to the NEW database (empty or pre-migrated)
   - If maintenance mode is enabled, user events will be automatically skipped
   - **Alternative**: Use a test/development bot token if maintenance mode isn't available

4. **Run migration**: Execute `$migrate all` command in Discord
   - Requires confirmation (react with ✅)
   - Monitor progress and handle any errors
   - Migration runs in a transaction (all-or-nothing)
   - **Note**: Bot must be running to receive and process this command

5. **Disable maintenance mode** (after migration completes):

   ```bash
   # Remove from .env or set to false:
   MAINTENANCE_MODE=false
   
   # Then restart the bot
   ```

4. **Validate**: Run `$migrate validate` to verify data
   - Checks row counts match
   - Validates relationships
   - Spot-checks sample data

5. **Switch to production** (if using different token):
   - Update bot token in `.env`
   - Restart bot with production token

6. **Verify functionality**: Test critical features
   - Levels/XP system
   - Guild configurations
   - Moderation cases
   - Other critical features

7. **Monitor**: Watch for errors and performance issues
   - Check logs for migration-related errors
   - Monitor database performance
   - Verify data integrity

### Rollback Procedure

If migration fails:

1. **Stop new bot**: Shut down the new bot instance
2. **Restore backup**: Restore new database from backup

   ```bash
   psql new_database < backup_file.sql
   ```

3. **Restart old bot**: Start the old bot instance
4. **Investigate**: Review logs and fix issues
   - Check migration error messages
   - Review validation reports
   - Fix schema mismatches or data issues
5. **Retry**: Attempt migration again after fixes

## Table & Column Mappings

### Table Overview

| Old Table   | New Table             | Migrated | Notes                                                                 |
|-------------|-----------------------|----------|-----------------------------------------------------------------------|
| Guild       | guild                 | Yes      | PK `guild_id` → `id`                                                  |
| GuildConfig | guild_config          | Yes      | PK `guild_id` → `id`; `perm_level_*_role_id` → PermissionRank/Assignment |
| Case        | cases                 | Yes      | PK `case_id` → `id`; `case_tempban_expired` → `case_processed`        |
| Snippet     | snippet               | Yes      | PK `snippet_id` → `id`; `snippet_created_at` → `created_at`           |
| Reminder    | reminder              | Yes      | PK `reminder_id` → `id`; `reminder_created_at` → `created_at`         |
| AFKModel    | afk                   | Yes      | Old table is `AFKModel`; composite PK `(member_id, guild_id)`         |
| Levels      | levels                | Yes      | Composite PK `(member_id, guild_id)`                                  |
| Starboard   | starboard             | Yes      | PK `guild_id` → `id`                                                  |
| StarboardMessage | starboard_message | Yes      | PK `message_id` → `id`; `message_created_at` → `created_at`           |
| Note        | —                     | No       | Intentionally not migrated; table removed in new schema               |
| —           | permission_ranks      | Derived  | From `GuildConfig.perm_level_0..7_role_id` via `migrate_permission_ranks()` |
| —           | permission_assignments| Derived  | From `GuildConfig.perm_level_0..7_role_id` via `migrate_permission_ranks()` |
| —           | permission_commands   | —        | New feature; no old data                                              |

### Column Mappings by Table

#### Guild → guild

| Old Column      | New Column    | Notes                                  |
|-----------------|---------------|----------------------------------------|
| `guild_id`      | `id`          | PK rename                              |
| `guild_joined_at` | `guild_joined_at` | 1:1                          |
| `case_count`    | `case_count`  | 1:1                                    |
| —               | `created_at`  | New (TimestampMixin); server default   |
| —               | `updated_at`  | New (TimestampMixin); server default   |

#### GuildConfig → guild_config

| Old Column            | New Column           | Notes                                    |
|-----------------------|----------------------|------------------------------------------|
| `guild_id`            | `id`                 | PK/FK rename                             |
| `prefix`              | `prefix`             | 1:1                                      |
| `mod_log_id`          | `mod_log_id`         | 1:1                                      |
| `audit_log_id`        | `audit_log_id`       | 1:1                                      |
| `join_log_id`         | `join_log_id`        | 1:1                                      |
| `private_log_id`      | `private_log_id`     | 1:1                                      |
| `report_log_id`       | `report_log_id`      | 1:1                                      |
| `dev_log_id`          | `dev_log_id`         | 1:1                                      |
| `jail_channel_id`     | `jail_channel_id`    | 1:1                                      |
| `jail_role_id`        | `jail_role_id`       | 1:1                                      |
| `base_member_role_id` | —                    | **Deprecated**; skipped                  |
| `base_staff_role_id`  | —                    | **Deprecated**; skipped                  |
| `general_channel_id`  | —                    | **Deprecated**; skipped                  |
| `quarantine_role_id`  | —                    | **Deprecated**; skipped                  |
| `starboard_channel_id`| —                    | **Deprecated**; starboard in `starboard` |
| `perm_level_0_role_id` … `perm_level_7_role_id` | — | **Migrated** to `permission_ranks` + `permission_assignments` (not to guild_config) |
| —                     | `onboarding_completed` | New; default `false`                   |
| —                     | `onboarding_stage`   | New; default `None`                     |
| —                     | `created_at`         | New (TimestampMixin); server default    |
| —                     | `updated_at`         | New (TimestampMixin); server default    |

#### Case → cases

| Old Column            | New Column         | Notes                                |
|-----------------------|--------------------|--------------------------------------|
| `case_id`             | `id`               | PK rename                            |
| `case_status`         | `case_status`      | 1:1                                  |
| `case_type`           | `case_type`        | 1:1 (enum; normalized via CASE_TYPE_MAPPING) |
| `case_reason`         | `case_reason`      | 1:1                                  |
| `case_moderator_id`   | `case_moderator_id`| 1:1                                  |
| `case_user_id`        | `case_user_id`     | 1:1                                  |
| `case_user_roles`     | `case_user_roles`  | 1:1 (JSON/array)                     |
| `case_number`         | `case_number`      | 1:1                                  |
| `case_created_at`     | `created_at`       | TimestampMixin                       |
| `case_expires_at`     | `case_expires_at`  | 1:1                                  |
| `case_tempban_expired`| `case_processed`   | **Renamed**                          |
| `guild_id`            | `guild_id`         | 1:1                                  |
| —                     | `case_metadata`    | New; default `None`                  |
| —                     | `mod_log_message_id` | New; default `None`                |
| —                     | `updated_at`       | New (TimestampMixin); server default |

#### Snippet → snippet

| Old Column         | New Column    | Notes                                |
|--------------------|---------------|--------------------------------------|
| `snippet_id`       | `id`          | PK rename                            |
| `snippet_name`     | `snippet_name`| 1:1                                  |
| `snippet_content`  | `snippet_content` | 1:1                              |
| `snippet_user_id`  | `snippet_user_id` | 1:1                              |
| `guild_id`         | `guild_id`    | 1:1                                  |
| `uses`             | `uses`        | 1:1                                  |
| `locked`           | `locked`      | 1:1                                  |
| `alias`            | `alias`       | 1:1                                  |
| `snippet_created_at` | `created_at` | TimestampMixin                       |
| —                  | `updated_at`  | New (TimestampMixin); server default |

#### Reminder → reminder

| Old Column           | New Column    | Notes                                |
|----------------------|---------------|--------------------------------------|
| `reminder_id`        | `id`          | PK rename                            |
| `reminder_content`   | `reminder_content` | 1:1                              |
| `reminder_expires_at`| `reminder_expires_at` | 1:1                            |
| `reminder_channel_id`| `reminder_channel_id` | 1:1                            |
| `reminder_user_id`   | `reminder_user_id` | 1:1                              |
| `reminder_sent`      | `reminder_sent` | 1:1                                |
| `guild_id`           | `guild_id`    | 1:1                                  |
| `reminder_created_at`| `created_at`  | TimestampMixin                       |
| —                    | `updated_at`  | New (TimestampMixin); server default |

#### AFKModel → afk

| Old Column  | New Column  | Notes                        |
|-------------|-------------|------------------------------|
| `member_id` | `member_id` | Composite PK part 1          |
| `guild_id`  | `guild_id`  | Composite PK part 2, FK      |
| `nickname`  | `nickname`  | 1:1                          |
| `reason`    | `reason`    | 1:1                          |
| `since`     | `since`     | 1:1                          |
| `until`     | `until`     | 1:1                          |
| `enforced`  | `enforced`  | 1:1                          |
| `perm_afk`  | `perm_afk`  | 1:1                          |
| —            | `created_at` | New (TimestampMixin); server default |
| —            | `updated_at` | New (TimestampMixin); server default |

#### Levels → levels

| Old Column    | New Column   | Notes   |
|---------------|--------------|---------|
| `member_id`   | `member_id`  | Composite PK part 1 |
| `guild_id`    | `guild_id`   | Composite PK part 2, FK |
| `xp`          | `xp`         | 1:1     |
| `level`       | `level`      | 1:1     |
| `blacklisted` | `blacklisted`| 1:1     |
| `last_message`| `last_message` | 1:1   |
| —             | `created_at` | New (TimestampMixin); server default |
| —             | `updated_at` | New (TimestampMixin); server default |

#### Starboard → starboard

| Old Column           | New Column           | Notes     |
|----------------------|----------------------|-----------|
| `guild_id`           | `id`                 | PK/FK; same semantics |
| `starboard_channel_id` | `starboard_channel_id` | 1:1    |
| `starboard_emoji`    | `starboard_emoji`    | 1:1       |
| `starboard_threshold`| `starboard_threshold`| 1:1       |
| —                    | `created_at`         | New (TimestampMixin); server default |
| —                    | `updated_at`         | New (TimestampMixin); server default |

#### StarboardMessage → starboard_message

| Old Column           | New Column           | Notes                        |
|----------------------|----------------------|------------------------------|
| `message_id`         | `id`                 | PK rename                    |
| `message_content`    | `message_content`    | 1:1                          |
| `message_expires_at` | `message_expires_at` | 1:1                          |
| `message_channel_id` | `message_channel_id` | 1:1                          |
| `message_user_id`    | `message_user_id`    | 1:1                          |
| `message_guild_id`   | `message_guild_id`   | 1:1 (FK to `guild.id`; name kept) |
| `star_count`         | `star_count`         | 1:1                          |
| `starboard_message_id` | `starboard_message_id` | 1:1                      |
| `message_created_at` | `created_at`         | TimestampMixin               |
| —                    | `updated_at`         | New (TimestampMixin); server default |

### Tables Only in Old Schema

#### Note

| Old Column        | Migrated | Notes          |
|-------------------|----------|----------------|
| `note_id`         | No       | Table removed  |
| `note_content`    | No       | —              |
| `note_created_at` | No       | —              |
| `note_moderator_id` | No     | —              |
| `note_user_id`    | No       | —              |
| `note_number`     | No       | —              |
| `guild_id`        | No       | —              |

**Not migrated by design.**

### Tables Only in New Schema

#### permission_ranks (from `GuildConfig.perm_level_*_role_id`)

Populated by `migrate_permission_ranks()` after `guild_config` is migrated. For each non-null `perm_level_X_role_id` (X = 0..7):

- Insert `PermissionRank`: `guild_id`, `rank` = X, `name` = `"Rank X"`, `description` = `"Migrated permission rank X"`.
- Insert `PermissionAssignment`: `guild_id`, `permission_rank_id` = that rank's `id`, `role_id` = `perm_level_X_role_id`.

| New Column   | Source / notes                           |
|--------------|------------------------------------------|
| `id`         | Auto-generated                           |
| `guild_id`   | From `GuildConfig.guild_id`              |
| `rank`       | 0–7 from `perm_level_X_role_id`          |
| `name`       | `"Rank X"`                               |
| `description`| `"Migrated permission rank X"`           |
| `created_at` | TimestampMixin; server default           |
| `updated_at` | TimestampMixin; server default           |

#### permission_assignments (from `GuildConfig.perm_level_*_role_id`)

| New Column          | Source / notes                                |
|---------------------|-----------------------------------------------|
| `id`                | Auto-generated                                |
| `guild_id`          | From `GuildConfig.guild_id`                   |
| `permission_rank_id`| ID of the created `PermissionRank` for rank X |
| `role_id`           | From `perm_level_X_role_id`                   |
| `created_at`        | TimestampMixin; server default                |
| `updated_at`        | TimestampMixin; server default                |

#### permission_commands

New feature only. No columns come from the old DB.

### Special Mappings

| Concept | Old | New |
|---------|-----|-----|
| PK `guild_id` | `Guild.guild_id` | `guild.id` (FKs reference `guild.id`) |
| PK `guild_id` | `GuildConfig.guild_id` | `guild_config.id` |
| PK `guild_id` | `Starboard.guild_id` | `starboard.id` |
| Tempban flag | `Case.case_tempban_expired` | `cases.case_processed` |
| Timestamps | `*_created_at` on Snippet, Reminder, StarboardMessage, Case | `created_at` (TimestampMixin) |
| AFK table name | `AFKModel` | `afk` |
| Case table name | `Case` | `cases` (reserved word) |
| Starboard FK | `StarboardMessage.message_guild_id` → Guild | `message_guild_id` → `guild.id` (name unchanged) |

## Architecture

### Components

- **SchemaInspector**: Inspects old database schema
- **ModelMapper**: Maps Prisma models to SQLModel models
- **DataExtractor**: Extracts and transforms data in batches
- **DatabaseMigrator**: Executes migrations with transactions
- **MigrationValidator**: Validates migrated data

### Migration Order

Tables are migrated in dependency order:

1. `guild` (no dependencies)
2. `guild_config`, `starboard` (depend on guild)
3. `permission_ranks` (depends on guild)
4. `cases`, `snippet`, `reminder`, `afk`, `levels`, `starboard_message` (depend on guild)
5. `permission_assignments` (depends on guild + permission_ranks)
6. `permission_commands` (depends on guild)

### Data Transformation

The migration handles:

- **Field name conversion**: `guildId` → `guild_id`
- **Type conversions**: Enums, JSON, datetime
- **Default values**: New required fields get defaults
- **Validation**: Pydantic validation ensures data integrity

### Special Ordering

**Cases**: Cases are migrated in chronological order (`guild_id`, `case_created_at`) rather than by `case_id`. This ensures proper insertion order even if the old database has missing or out-of-order case numbers. Cases with NULL `case_created_at` are ordered last, falling back to `case_id` ordering.

### Data Conflict Handling

The migration plugin handles existing records intelligently:

- **Primary Key Match**: Updates existing record with old data (preserves timestamps)
- **No Match**: Creates new record
- **Missing PK Fields**: Skips row and logs warning

However, this assumes:

- Migration runs on empty or pre-migrated database
- No concurrent writes during migration
- Bot is stopped during migration

## Post-Migration Verification

After migration completes:

1. **Check Row Counts**

   ```bash
   $migrate status
   ```

2. **Validate Data Integrity**

   ```bash
   $migrate validate
   ```

3. **Test Critical Features**
   - Levels/XP system
   - Guild configurations
   - Moderation cases
   - Starboard
   - Reminders
   - AFK status

4. **Monitor Logs**
   - Watch for errors
   - Check for missing data
   - Verify relationships

## Troubleshooting

### Connection Errors

If you get connection errors:

1. Check `OLD_DATABASE_URL` is correct
2. Verify network connectivity
3. Check firewall rules
4. Ensure database is accessible

### Validation Failures

If validation fails:

1. Review validation report for details
2. Check row count mismatches
3. Verify foreign key relationships
4. Spot-check sample data

### Migration Errors

If migration fails:

1. Check logs for detailed error messages
2. Review dry-run results
3. Verify model mappings are correct
4. Check database constraints

### Migration Fails Mid-Way

1. **Check Logs**: Review error messages
2. **Rollback**: Restore database from backup
3. **Fix Issues**: Address schema mismatches or data issues
4. **Retry**: Run migration again after fixes

### Data Mismatches After Migration

1. **Run Validation**: `$migrate validate`
2. **Check Specific Tables**: `$migrate status`
3. **Compare Row Counts**: Old vs new database
4. **Spot Check**: Manually verify sample records

### Bot Won't Start After Migration

1. **Check Database Connection**: `uv run db health`
2. **Verify Migrations**: `uv run db status`
3. **Check Logs**: Look for schema errors
4. **Validate Models**: Ensure models match database

### Unique Constraint Violations

If you encounter unique constraint violations (e.g., duplicate `case_number`):

1. Check the old database for duplicate `(guild_id, case_number)` pairs
2. Review migration logs for specific error details
3. Consider cleaning the old database before migration
4. Use `$migrate check-duplicates` to identify issues

## Security Considerations

- **Admin-only commands**: All migration commands require bot owner/sysadmin permissions
- **No sensitive data logging**: Passwords and tokens are never logged
- **Transaction safety**: Each migration runs in a transaction
- **Dry-run mode**: Test migrations without committing changes

## Performance

- **Batch processing**: Processes data in configurable batches (default: 1000 rows)
- **Progress tracking**: Shows progress during migration
- **Resume capability**: Can resume after failures
- **Parallel extraction**: Read operations can be parallelized

## Limitations

- **One-way migration**: This plugin migrates from old to new, not reverse
- **Schema changes**: Requires manual mapping for schema changes
- **Large datasets**: May take time for very large databases
- **Downtime**: Requires brief downtime during migration

## Code Quality Notes

### Strengths

1. **Transaction Safety**: Migration runs in transactions (all-or-nothing)
2. **Dry-Run Support**: Can test without committing changes
3. **Batch Processing**: Handles large datasets efficiently
4. **Error Handling**: Comprehensive error handling with rollback
5. **Validation**: Post-migration validation tools
6. **Existing Record Handling**: Updates existing records intelligently (preserves timestamps)
7. **Primary Key Handling**: Properly handles composite primary keys
8. **Permission Checks**: Admin-only commands (bot owner/sysadmin)

### Areas for Improvement

1. **Concurrent Write Detection**: No check for concurrent writes during migration
2. **Progress Reporting**: Could benefit from more detailed progress reporting for large migrations
3. **Resume Capability**: No ability to resume failed migrations (starts from beginning)
4. **Migration State Tracking**: No persistent state tracking (which tables migrated, when)

## Support

If you encounter issues:

1. Check migration logs for detailed errors
2. Review validation reports
3. Test with dry-run mode first
4. Consult migration documentation
5. Check GitHub issues for known problems

## See Also

- [Database Models](../../../database/models/models.py)
- [Database Service](../../../database/service.py)
- [Migration Documentation](../../../../docs/content/developer/concepts/database/migrations.md)
- [mapper.py](mapper.py) — `field_mappings`, `deprecated_fields`, `get_table_mapping`, `get_field_mapping`
