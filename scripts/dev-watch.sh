#!/bin/bash
set -e

# Development watch script with automatic cleanup on failure
# This script starts the bot with watch mode and automatically shuts down
# all services if the bot fails to start or crashes

echo "🚀 Starting Tux with Docker Compose Watch"
echo "=========================================="

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🧹 Cleaning up services..."
    docker compose down
    echo "✅ Cleanup complete"
}

# Set up trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Start services with watch mode
echo "⏳ Starting services with watch mode..."
if ! docker compose up --watch; then
    echo "❌ Services failed to start or crashed"
    echo "🛑 Automatic cleanup will occur on script exit"
    exit 1
fi
