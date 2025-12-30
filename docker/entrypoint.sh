#!/bin/bash
set -e

echo "Tux Docker Entrypoint"
echo "====================="

# Configuration
MAX_STARTUP_ATTEMPTS=${MAX_STARTUP_ATTEMPTS:-3}
STARTUP_DELAY=${STARTUP_DELAY:-5}

# Function to check if database is ready (simple socket check)
wait_for_db() {
    local attempts=0
    local max_attempts=30

    # Check if POSTGRES_HOST is set, if not use default
    local db_host="${POSTGRES_HOST:-tux-postgres}"
    local db_port="${POSTGRES_PORT:-5432}"

    echo "Waiting for database at $db_host:$db_port..."

    until python -c "
import socket
import sys
import os
try:
    db_host = os.environ.get('POSTGRES_HOST', 'tux-postgres')
    db_port = int(os.environ.get('POSTGRES_PORT', 5432))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((db_host, db_port))
    sock.close()
    sys.exit(0 if result == 0 else 1)
except Exception as e:
    sys.exit(1)
" 2> /dev/null; do
        attempts=$((attempts + 1))
        if [ $attempts -ge $max_attempts ]; then
            echo "❌ Database connection timeout after $max_attempts attempts"
            echo "   Host: $db_host, Port: $db_port"
            echo "   Make sure the database container is running and accessible"
            exit 1
    fi
        echo "⏳ Database is unavailable - sleeping (attempt $attempts/$max_attempts)"
        sleep 2
  done
    echo "✅ Database is ready!"
}

# Function to validate configuration
validate_config() {
    echo "Validating configuration..."

    # Check for required environment variables
    if [ -z "$BOT_TOKEN" ]; then
        echo "BOT_TOKEN is not set"
        return 1
  fi

    # Test configuration loading
    if ! python -c "import tux.shared.config.settings; print('Configuration loaded successfully')"; then
        echo "Failed to load configuration"
        return 1
  fi

    echo "Configuration validation passed"
    return 0
}

# Function to start the bot with retry logic
# Note: Retry logic only applies to configuration validation failures.
# Once tux start is called successfully, it runs in foreground until stopped.
start_bot_with_retry() {
    local attempts=0

    while [ $attempts -lt "$MAX_STARTUP_ATTEMPTS" ]; do
        attempts=$((attempts + 1))
        echo "Validating configuration (attempt $attempts/$MAX_STARTUP_ATTEMPTS)..."

        # Validate configuration before starting
        if ! validate_config; then
            echo "Configuration validation failed"
            if [ $attempts -ge "$MAX_STARTUP_ATTEMPTS" ]; then
                echo "Maximum startup attempts reached. Exiting."
                exit 1
      fi
            echo "Waiting ${STARTUP_DELAY}s before retry..."
            sleep "$STARTUP_DELAY"
            continue
    fi

        # Configuration validated, start the bot
        # Use exec to replace shell process for proper signal handling (SIGTERM, SIGINT)
        # This ensures signals are delivered directly to the bot process
        echo "Configuration validated. Starting bot..."
        # shellcheck disable=SC2093
        exec tux start
  done
}

# Signal handlers for graceful shutdown
cleanup() {
    echo ""
    echo "Received shutdown signal"
    echo "Performing cleanup..."

    # Kill any child processes
    if [ -n "$BOT_PID" ]; then
        echo "Stopping bot process (PID: $BOT_PID)..."
        kill -TERM "$BOT_PID" 2> /dev/null || true
        wait "$BOT_PID" 2> /dev/null || true
  fi

    echo "Cleanup complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Main execution
echo "Waiting for database to be ready..."
wait_for_db

# Start bot with retry logic and validation (always enabled)
# Note: Database migrations are handled automatically by the bot during setup
echo "Starting bot with smart orchestration..."
start_bot_with_retry
