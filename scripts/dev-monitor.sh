#!/bin/bash
set -e

# Advanced development monitor with automatic cleanup
# Monitors the bot container and shuts down all services if it fails

echo "🚀 Starting Tux Development Monitor"
echo "===================================="

# Configuration
BOT_CONTAINER="tux"
MAX_RESTART_ATTEMPTS=3
RESTART_DELAY=5
MONITOR_INTERVAL=10

# Function to cleanup all services
cleanup() {
    echo ""
    echo "🧹 Cleaning up all services..."
    docker compose down
    echo "✅ Cleanup complete"
}

# Function to check if bot container is running and healthy
check_bot_health() {
    local container_status=$(docker inspect --format='{{.State.Status}}' "$BOT_CONTAINER" 2>/dev/null || echo "not_found")
    local exit_code=$(docker inspect --format='{{.State.ExitCode}}' "$BOT_CONTAINER" 2>/dev/null || echo "0")

    if [ "$container_status" = "not_found" ]; then
        echo "❌ Bot container not found"
        return 1
    elif [ "$container_status" = "exited" ]; then
        echo "❌ Bot container exited with code: $exit_code"
        return 1
    elif [ "$container_status" = "running" ]; then
        echo "✅ Bot container is running"
        return 0
    else
        echo "⚠️  Bot container status: $container_status"
        return 1
    fi
}

# Function to start services
start_services() {
    echo "⏳ Starting services..."
    if ! docker compose up -d; then
        echo "❌ Failed to start services"
        return 1
    fi

    # Wait for bot to start
    echo "⏳ Waiting for bot to start..."
    local attempts=0
    while [ $attempts -lt 30 ]; do
        if check_bot_health; then
            echo "✅ Bot started successfully"
            return 0
        fi
        sleep 2
        attempts=$((attempts + 1))
    done

    echo "❌ Bot failed to start within timeout"
    return 1
}

# Set up trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Start services
if ! start_services; then
    echo "❌ Failed to start services"
    exit 1
fi

# Monitor loop
echo "👀 Starting monitor loop..."
restart_attempts=0

while true; do
    if ! check_bot_health; then
        restart_attempts=$((restart_attempts + 1))
        echo "⚠️  Bot failure detected (attempt $restart_attempts/$MAX_RESTART_ATTEMPTS)"

        if [ $restart_attempts -ge $MAX_RESTART_ATTEMPTS ]; then
            echo "❌ Maximum restart attempts reached. Shutting down all services."
            cleanup
            exit 1
        fi

        echo "🔄 Restarting services in ${RESTART_DELAY} seconds..."
        sleep $RESTART_DELAY

        if ! start_services; then
            echo "❌ Failed to restart services"
            cleanup
            exit 1
        fi
    else
        # Reset restart counter on successful health check
        restart_attempts=0
    fi

    sleep $MONITOR_INTERVAL
done
