#!/bin/bash
set -e

# Ensure POSTGRES_PASSWORD environment variable is set
if [ -z "$POSTGRES_PASSWORD" ]; then
  echo "Error: POSTGRES_PASSWORD environment variable is not set."
  exit 1
fi

# Log that we are setting up the init.sql file
echo "Creating init.sql with POSTGRES_PASSWORD=${POSTGRES_PASSWORD}"

# Generate init.sql dynamically based on POSTGRES_PASSWORD
cat <<EOF >/docker-entrypoint-initdb.d/init.sql
DO \$\$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'postgres'
    ) THEN
        CREATE USER postgres WITH PASSWORD '${POSTGRES_PASSWORD}';
        ALTER USER postgres WITH SUPERUSER;
    END IF;
END
\$$;
EOF

# Set permissions for the SQL file
chmod 644 /docker-entrypoint-initdb.d/init.sql # Read permissions for everyone, write permission for owner only

# Execute the original entrypoint script from the Postgres image
exec docker-entrypoint.sh postgres
