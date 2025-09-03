#!/bin/bash
set -e

echo "🐧 Tux Docker Entrypoint"
echo "========================"

# Configuration
MAX_STARTUP_ATTEMPTS=${MAX_STARTUP_ATTEMPTS:-3}
STARTUP_DELAY=${STARTUP_DELAY:-5}

# Function to check if database is ready (simple socket check)
wait_for_db() {
    echo "⏳ Waiting for database to be ready..."
    local attempts=0
    local max_attempts=30

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
        attempts=$((attempts + 1))
        if [ $attempts -ge $max_attempts ]; then
            echo "❌ Database connection timeout after $max_attempts attempts"
            exit 1
        fi
        echo "Database is unavailable - sleeping (attempt $attempts/$max_attempts)"
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

# Function to validate configuration
validate_config() {
    echo "🔍 Validating configuration..."

    # Check for required environment variables
    if [ -z "$BOT_TOKEN" ]; then
        echo "❌ BOT_TOKEN is not set"
        return 1
    fi

    # Test configuration loading
    if ! python -c "import tux.shared.config.env; print('✅ Configuration loaded successfully')"; then
        echo "❌ Failed to load configuration"
        return 1
    fi

    echo "✅ Configuration validation passed"
    return 0
}

# Function to start the bot with retry logic
start_bot_with_retry() {
    local attempts=0

    while [ $attempts -lt $MAX_STARTUP_ATTEMPTS ]; do
        attempts=$((attempts + 1))
        echo "🚀 Starting Tux bot (attempt $attempts/$MAX_STARTUP_ATTEMPTS)..."

        # Validate configuration before starting
        if ! validate_config; then
            echo "❌ Configuration validation failed"
            if [ $attempts -ge $MAX_STARTUP_ATTEMPTS ]; then
                echo "🛑 Maximum startup attempts reached. Exiting."
                exit 1
            fi
            echo "⏳ Waiting ${STARTUP_DELAY}s before retry..."
            sleep $STARTUP_DELAY
            continue
        fi

        # Start the bot
        if exec tux start; then
            echo "✅ Bot started successfully"
            return 0
        else
            echo "❌ Bot failed to start (exit code: $?)"
            if [ $attempts -ge $MAX_STARTUP_ATTEMPTS ]; then
                echo "🛑 Maximum startup attempts reached. Exiting."
                exit 1
            fi
            echo "⏳ Waiting ${STARTUP_DELAY}s before retry..."
            sleep $STARTUP_DELAY
        fi
    done
}

# Signal handlers for graceful shutdown
cleanup() {
    echo ""
    echo "🛑 Received shutdown signal"
    echo "🧹 Performing cleanup..."

    # Kill any child processes
    if [ -n "$BOT_PID" ]; then
        echo "🔄 Stopping bot process (PID: $BOT_PID)..."
        kill -TERM "$BOT_PID" 2>/dev/null || true
        wait "$BOT_PID" 2>/dev/null || true
    fi

    echo "✅ Cleanup complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Main execution
echo "⏳ Waiting for database to be ready..."
wait_for_db

echo "🔄 Handling database migrations..."
handle_migrations

# Start bot with retry logic and validation (always enabled)
echo "🚀 Starting bot with smart orchestration..."
start_bot_with_retry
