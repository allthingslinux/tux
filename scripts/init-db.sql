-- =============================================================================
-- POSTGRESQL INITIALIZATION SCRIPT FOR TUX DEVELOPMENT
-- =============================================================================
-- Purpose: Initialize the development database with proper settings
-- Usage: Automatically runs when PostgreSQL container starts for the first time
-- =============================================================================

-- Create the database if it doesn't exist (PostgreSQL creates it automatically)
-- Set proper encoding and locale
-- Enable required extensions for TUX

-- Enable UUID extension (if needed)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable JSONB support (already enabled by default in PostgreSQL 15+)
-- CREATE EXTENSION IF NOT EXISTS "jsonb";

-- Set proper timezone
SET timezone = 'UTC';

-- Create a simple function to check database health
CREATE OR REPLACE FUNCTION check_db_health()
RETURNS text AS $$
BEGIN
    RETURN 'TUX Development Database is healthy!';
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE tuxdb TO tuxuser;
GRANT ALL PRIVILEGES ON SCHEMA public TO tuxuser;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'TUX Development Database initialized successfully!';
    RAISE NOTICE 'Database: %', current_database();
    RAISE NOTICE 'User: %', current_user;
    RAISE NOTICE 'Timezone: %', current_setting('timezone');
END $$;
