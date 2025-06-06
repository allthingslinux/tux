#!/bin/bash

# Docker Recovery Script
# Use this to restore accidentally removed images and check system state

set -e

echo "🔧 Docker Recovery and System Check"
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check Docker status
info "Checking Docker system status..."
if ! docker version &> /dev/null; then
    error "Docker is not running or accessible"
    exit 1
fi
success "Docker is running"

# Show current system state
echo ""
info "Current Docker system state:"
echo "=========================="
docker system df
echo ""

# Check for common base images
echo ""
info "Checking for common base images:"
echo "==============================="

COMMON_IMAGES=(
    "python:3.13.2-slim"
    "python:3.13-slim"
    "python:3.12-slim"
    "ubuntu:22.04"
    "ubuntu:20.04"
    "alpine:latest"
    "node:18-slim"
    "node:20-slim"
)

MISSING_IMAGES=()

for image in "${COMMON_IMAGES[@]}"; do
    if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^$image$"; then
        success "$image is present"
    else
        warning "$image is missing"
        MISSING_IMAGES+=("$image")
    fi
done

# Restore missing critical images
if [ ${#MISSING_IMAGES[@]} -gt 0 ]; then
    echo ""
    warning "Found ${#MISSING_IMAGES[@]} missing common images"
    
    read -p "Would you like to restore missing images? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for image in "${MISSING_IMAGES[@]}"; do
            info "Pulling $image..."
            if docker pull "$image"; then
                success "Restored $image"
            else
                error "Failed to restore $image"
            fi
        done
    fi
fi

# Check for tux project images
echo ""
info "Checking tux project images:"
echo "==========================="

TUX_IMAGES=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "(tux|ghcr.io/allthingslinux/tux)" || echo "")

if [ -n "$TUX_IMAGES" ]; then
    echo "$TUX_IMAGES"
    success "Found tux project images"
else
    warning "No tux project images found"
    info "You can rebuild them with:"
    echo "  docker build --target dev -t tux:dev ."
    echo "  docker build --target production -t tux:prod ."
fi

# Check for containers
echo ""
info "Checking running containers:"
echo "=========================="

RUNNING_CONTAINERS=$(docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}")
if [ -n "$RUNNING_CONTAINERS" ]; then
    echo "$RUNNING_CONTAINERS"
else
    info "No running containers"
fi

# Check for stopped containers
STOPPED_CONTAINERS=$(docker ps -a --filter "status=exited" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}")
if [ -n "$STOPPED_CONTAINERS" ]; then
    echo ""
    info "Stopped containers:"
    echo "$STOPPED_CONTAINERS"
    
    read -p "Would you like to remove stopped containers? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker container prune -f
        success "Removed stopped containers"
    fi
fi

# Check for dangling images
echo ""
info "Checking for dangling images:"
echo "============================"

DANGLING_IMAGES=$(docker images --filter "dangling=true" -q)
if [ -n "$DANGLING_IMAGES" ]; then
    echo "Found $(echo "$DANGLING_IMAGES" | wc -l) dangling images"
    
    read -p "Would you like to remove dangling images? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker image prune -f
        success "Removed dangling images"
    fi
else
    success "No dangling images found"
fi

# Check build cache
echo ""
info "Checking build cache:"
echo "=================="

BUILD_CACHE=$(docker system df | grep "Build Cache" | awk '{print $2}')
if [ -n "$BUILD_CACHE" ] && [ "$BUILD_CACHE" != "0B" ]; then
    info "Build cache size: $BUILD_CACHE"
    
    read -p "Would you like to clean build cache? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker builder prune -f
        success "Cleaned build cache"
    fi
else
    success "Build cache is clean"
fi

# Final system state
echo ""
info "Final Docker system state:"
echo "========================"
docker system df

echo ""
success "Docker recovery check completed!"
echo ""
echo "Next steps:"
echo "1. If you need to rebuild tux images:"
echo "   docker build --target dev -t tux:dev ."
echo "   docker build --target production -t tux:prod ."
echo ""
echo "2. To prevent future issues, always use the safe test script:"
echo "   ./scripts/test-docker.sh"
echo ""
echo "3. For comprehensive testing (safe):"
echo "   ./scripts/test-docker.sh --force-clean" 