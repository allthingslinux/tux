#!/bin/bash
set -e

echo "🐧 Tux Docker Entrypoint"
echo "========================"

# Function to check if database is ready (simple socket check)
wait_for_db() {
    echo "⏳ Waiting for database to be ready..."
    until python -c "
import socket
import sys
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('$POSTGRES_HOST', $POSTGRES_PORT))
    sock.close()
    sys.exit(0 if result == 0 else 1)
except Exception:
    sys.exit(1)
"; do
        echo "Database is unavailable - sleeping"
        sleep 2
    done
    echo "✅ Database is ready!"
}

# Function to handle migrations
handle_migrations() {
    echo "🔄 Handling database migrations..."

    # Change to the app directory where alembic.ini is located
    cd /app

    # Check if we need to force migration
    if [ "$FORCE_MIGRATE" = "true" ]; then
        echo "⚠️  WARNING: Force migration can cause data inconsistency!"
        echo "🔧 Force migrating database to head..."
        python -m alembic stamp head
        echo "✅ Database force migrated to head"
    else
        # Try normal migration
        echo "🔄 Running normal migrations..."
        if ! python -m alembic upgrade head; then
            echo "⚠️  Migration failed, attempting to fix..."
            echo "📊 Current migration status:"
            python -m alembic current
            echo "🔧 Attempting to stamp database as head..."
            python -m alembic stamp head
            echo "✅ Database stamped as head"
        else
            echo "✅ Migrations completed successfully"
        fi
    fi
}

# Main execution
echo "⏳ Waiting for database to be ready..."
wait_for_db

echo "🔄 Handling database migrations..."
handle_migrations

echo "🚀 Starting Tux bot..."
exec tux start
