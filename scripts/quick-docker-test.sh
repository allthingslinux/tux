#!/bin/bash

# Quick Docker Validation Test
# 2-3 minute validation for daily development workflow

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}⚡ QUICK DOCKER VALIDATION${NC}"
echo "=========================="
echo "Testing core functionality (2-3 minutes)"
echo ""

# Track test results
PASSED=0
FAILED=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ $2${NC}"
        ((FAILED++))
    fi
}

# Test 1: Basic build test
echo "🔨 Testing builds..."
if docker build --target dev -t tux:quick-dev . > /dev/null 2>&1; then
    test_result 0 "Development build"
else
    test_result 1 "Development build"
fi

if docker build --target production -t tux:quick-prod . > /dev/null 2>&1; then
    test_result 0 "Production build"
else
    test_result 1 "Production build"
fi

# Test 2: Container execution
echo "🏃 Testing container execution..."
if docker run --rm tux:quick-prod python --version > /dev/null 2>&1; then
    test_result 0 "Container execution"
else
    test_result 1 "Container execution"
fi

# Test 3: Security basics
echo "🔒 Testing security..."
USER_OUTPUT=$(docker run --rm tux:quick-prod whoami 2>/dev/null || echo "failed")
if [[ "$USER_OUTPUT" == "nonroot" ]]; then
    test_result 0 "Non-root execution"
else
    test_result 1 "Non-root execution"
fi

# Test 4: Compose validation
echo "📋 Testing compose files..."
if docker compose -f docker-compose.dev.yml config > /dev/null 2>&1; then
    test_result 0 "Dev compose config"
else
    test_result 1 "Dev compose config"
fi

if docker compose -f docker-compose.yml config > /dev/null 2>&1; then
    test_result 0 "Prod compose config"
else
    test_result 1 "Prod compose config"
fi

# Test 5: Volume and mount configuration test
echo "💻 Testing volume configuration..."
if docker run --rm -v /tmp:/app/temp tux:quick-dev test -d /app/temp > /dev/null 2>&1; then
    test_result 0 "Volume mount functionality"
else
    test_result 1 "Volume mount functionality"
fi

# Cleanup
docker rmi tux:quick-dev tux:quick-prod > /dev/null 2>&1 || true

# Summary
echo ""
echo "📊 Quick Test Summary:"
echo "====================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All quick tests passed!${NC}"
    echo "Your Docker setup is ready for development."
    exit 0
else
    echo -e "\n${RED}⚠️  Some tests failed.${NC}"
    echo "Run './scripts/test-docker.sh' for detailed diagnostics."
    exit 1
fi 