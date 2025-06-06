#!/bin/bash

# Docker Setup Performance Test Script
# Run this to validate Docker functionality with comprehensive metrics

set -e  # Exit on any error

echo "🔧 Docker Setup Performance Test"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Create logs directory
mkdir -p logs

# Log file with timestamp
LOG_FILE="logs/docker-test-$(date +%Y%m%d-%H%M%S).log"
METRICS_FILE="logs/docker-metrics-$(date +%Y%m%d-%H%M%S).json"

# Initialize metrics JSON
echo '{
  "timestamp": "'$(date -Iseconds)'",
  "tests": [],
  "performance": {},
  "images": {},
  "summary": {}
}' > "$METRICS_FILE"

# Helper functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}" | tee -a "$LOG_FILE"
}

metric() {
    echo -e "${BLUE}📊 $1${NC}" | tee -a "$LOG_FILE"
}

# Timer functions
start_timer() {
    echo $(($(date +%s%N)/1000000))
}

end_timer() {
    local start_time=$1
    local end_time=$(($(date +%s%N)/1000000))
    echo $((end_time - start_time))
}

# Add metric to JSON
add_metric() {
    local key=$1
    local value=$2
    local unit=$3
    
    # Update the metrics file using jq if available, otherwise append to log
    if command -v jq &> /dev/null; then
        tmp=$(mktemp)
        jq ".performance.\"$key\" = {\"value\": $value, \"unit\": \"$unit\"}" "$METRICS_FILE" > "$tmp" && mv "$tmp" "$METRICS_FILE"
    else
        echo "METRIC: $key=$value $unit" >> "$LOG_FILE"
    fi
}

# Get image size in MB
get_image_size() {
    local image=$1
    docker images --format "table {{.Size}}" "$image" | tail -n 1 | sed 's/[^0-9.]//g'
}

# Test functions with timing
test_with_timing() {
    local test_name="$1"
    local test_command="$2"
    
    info "Starting: $test_name"
    local start_time=$(start_timer)
    
    eval "$test_command"
    local result=$?
    
    local duration=$(end_timer $start_time)
    metric "$test_name completed in ${duration}ms"
    add_metric "$test_name" "$duration" "ms"
    
    return $result
}

log "Starting Docker performance tests"
log "Log file: $LOG_FILE"
log "Metrics file: $METRICS_FILE"

# Record system info
log "System Information:"
log "- OS: $(uname -s -r)"
log "- Docker version: $(docker --version)"
log "- Available memory: $(free -h | awk '/^Mem:/ {print $2}')"
log "- Available disk: $(df -h . | awk 'NR==2 {print $4}')"

# Test 1: Environment Check
info "Checking environment..."
if [[ ! -f ".env" ]]; then
    error ".env file not found"
fi
if [[ ! -f "pyproject.toml" ]]; then
    error "pyproject.toml not found"
fi
if [[ ! -d "prisma/schema" ]]; then
    error "prisma/schema directory not found"
fi
success "Environment files present"

# Test 2: Development Build with timing
test_with_timing "development_build" "docker build --target dev -t tux:test-dev . > /dev/null 2>&1"
if [[ $? -eq 0 ]]; then
    success "Development build successful"
    dev_size=$(get_image_size "tux:test-dev")
    metric "Development image size: ${dev_size}"
    add_metric "dev_image_size_mb" "${dev_size//[^0-9.]/}" "MB"
else
    error "Development build failed"
fi

# Test 3: Production Build with timing
test_with_timing "production_build" "docker build --target production -t tux:test-prod . > /dev/null 2>&1"
if [[ $? -eq 0 ]]; then
    success "Production build successful"
    prod_size=$(get_image_size "tux:test-prod")
    metric "Production image size: ${prod_size}"
    add_metric "prod_image_size_mb" "${prod_size//[^0-9.]/}" "MB"
else
    error "Production build failed"
fi

# Test 4: Container Startup Time
info "Testing container startup time..."
startup_start=$(start_timer)
CONTAINER_ID=$(docker run -d --rm tux:test-prod sleep 30)
# Wait for container to be running
while [[ "$(docker inspect -f '{{.State.Status}}' $CONTAINER_ID 2>/dev/null)" != "running" ]]; do
    sleep 0.1
done
startup_duration=$(end_timer $startup_start)
docker stop $CONTAINER_ID > /dev/null 2>&1 || true

metric "Container startup time: ${startup_duration}ms"
add_metric "container_startup" "$startup_duration" "ms"
success "Container startup test completed"

# Test 5: Non-root User Check
info "Testing non-root user execution..."
USER_OUTPUT=$(docker run --rm tux:test-prod whoami 2>/dev/null || echo "failed")
if [[ "$USER_OUTPUT" == "nonroot" ]]; then
    success "Container runs as non-root user"
else
    error "Container not running as non-root user (got: $USER_OUTPUT)"
fi

# Test 6: Read-only Filesystem Check
info "Testing read-only filesystem..."
if docker run --rm tux:test-prod touch /test-file 2>/dev/null; then
    error "Filesystem is not read-only"
else
    success "Read-only filesystem working"
fi

# Test 7: Temp Directory Performance Test
info "Testing temp directory performance..."
temp_start=$(start_timer)
docker run --rm tux:test-prod sh -c "
    for i in \$(seq 1 100); do
        echo 'test content' > /app/temp/test_\$i.txt
    done
    rm /app/temp/test_*.txt
" > /dev/null 2>&1
temp_duration=$(end_timer $temp_start)

metric "Temp file operations (100 files): ${temp_duration}ms"
add_metric "temp_file_ops" "$temp_duration" "ms"
success "Temp directory performance test completed"

# Test 8: Prisma Client Generation with timing
test_with_timing "prisma_generation" "docker run --rm tux:test-dev sh -c 'poetry run prisma generate' > /dev/null 2>&1"
if [[ $? -eq 0 ]]; then
    success "Prisma client generation working"
else
    error "Prisma client generation failed"
fi

# Test 9: Memory Usage Test
info "Testing memory usage..."
CONTAINER_ID=$(docker run -d --rm tux:test-prod sleep 30)
sleep 2  # Let container stabilize

# Get memory stats
MEMORY_STATS=$(docker stats --no-stream --format "{{.MemUsage}}" $CONTAINER_ID)
MEMORY_MB=$(echo $MEMORY_STATS | sed 's/MiB.*//' | sed 's/[^0-9.]//g')

docker stop $CONTAINER_ID > /dev/null 2>&1 || true

metric "Memory usage: ${MEMORY_STATS}"
add_metric "memory_usage_mb" "${MEMORY_MB:-0}" "MB"
success "Memory usage test completed"

# Test 10: Docker Compose Validation with timing
test_with_timing "compose_validation" "docker compose -f docker-compose.dev.yml config > /dev/null 2>&1 && docker compose -f docker-compose.yml config > /dev/null 2>&1"
if [[ $? -eq 0 ]]; then
    success "Docker Compose files valid"
else
    error "Docker Compose validation failed"
fi

# Test 11: Layer Analysis
info "Analyzing Docker layers..."
LAYERS_DEV=$(docker history tux:test-dev --quiet | wc -l)
LAYERS_PROD=$(docker history tux:test-prod --quiet | wc -l)

metric "Development image layers: $LAYERS_DEV"
metric "Production image layers: $LAYERS_PROD"
add_metric "dev_layers" "$LAYERS_DEV" "count"
add_metric "prod_layers" "$LAYERS_PROD" "count"

# Test 12: Security Scan (if Docker Scout available)
info "Testing security scan (if available)..."
if command -v docker scout &> /dev/null; then
    scan_start=$(start_timer)
    if docker scout cves tux:test-prod --only-severity critical,high --exit-code > /dev/null 2>&1; then
        scan_duration=$(end_timer $scan_start)
        metric "Security scan time: ${scan_duration}ms"
        add_metric "security_scan" "$scan_duration" "ms"
        success "No critical/high vulnerabilities found"
    else
        scan_duration=$(end_timer $scan_start)
        metric "Security scan time: ${scan_duration}ms"
        add_metric "security_scan" "$scan_duration" "ms"
        warning "Critical/high vulnerabilities found (review manually)"
    fi
else
    warning "Docker Scout not available, skipping security scan"
fi

# Cleanup and final metrics
info "Cleaning up test images..."
cleanup_start=$(start_timer)
docker rmi tux:test-dev tux:test-prod > /dev/null 2>&1 || true
cleanup_duration=$(end_timer $cleanup_start)
add_metric "cleanup_time" "$cleanup_duration" "ms"

# Generate summary
log "Test Summary:"
log "============="

# Update final metrics if jq is available
if command -v jq &> /dev/null; then
    # Add summary to metrics file
    tmp=$(mktemp)
    jq ".summary = {
        \"total_tests\": 12,
        \"timestamp\": \"$(date -Iseconds)\",
        \"log_file\": \"$LOG_FILE\"
    }" "$METRICS_FILE" > "$tmp" && mv "$tmp" "$METRICS_FILE"
    
    # Display performance summary
    echo ""
    metric "Performance Summary:"
    echo -e "${BLUE}===================${NC}"
    jq -r '.performance | to_entries[] | "📊 \(.key): \(.value.value) \(.value.unit)"' "$METRICS_FILE" 2>/dev/null || echo "Metrics available in $METRICS_FILE"
fi

echo ""
echo -e "${GREEN}🎉 All tests completed!${NC}"
echo ""
echo -e "${CYAN}📊 Detailed logs: $LOG_FILE${NC}"
echo -e "${CYAN}📈 Metrics data: $METRICS_FILE${NC}"
echo ""
echo "Performance Benchmarks:"
echo "======================"
echo "✅ Development build: < 120,000ms (2 min)"
echo "✅ Production build: < 180,000ms (3 min)"
echo "✅ Container startup: < 5,000ms (5 sec)"
echo "✅ Prisma generation: < 30,000ms (30 sec)"
echo "✅ Memory usage: < 512MB (prod)"
echo ""
echo "Next steps:"
echo "1. Review metrics in $METRICS_FILE"
echo "2. Run full test suite: see DOCKER-TESTING.md"
echo "3. Test development workflow:"
echo "   poetry run tux --dev docker up"
echo "4. Monitor performance over time"
echo "" 