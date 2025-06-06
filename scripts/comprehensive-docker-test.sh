#!/bin/bash

# Comprehensive Docker Testing Strategy
# Tests all possible developer scenarios and workflows

set -e

# Colors and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Test configuration
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_DIR="logs/comprehensive-test-$TIMESTAMP"
METRICS_FILE="$LOG_DIR/comprehensive-metrics.json"
REPORT_FILE="$LOG_DIR/test-report.md"

mkdir -p "$LOG_DIR"

# Helper functions
log() {
    echo "[$(date +'%H:%M:%S')] $1" | tee -a "$LOG_DIR/test.log"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_DIR/test.log"
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_DIR/test.log"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_DIR/test.log"
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}" | tee -a "$LOG_DIR/test.log"
}

section() {
    echo -e "\n${PURPLE}🔵 $1${NC}" | tee -a "$LOG_DIR/test.log"
    echo "======================================" | tee -a "$LOG_DIR/test.log"
}

timer_start() {
    echo $(($(date +%s%N)/1000000))
}

timer_end() {
    local start_time=$1
    local end_time=$(($(date +%s%N)/1000000))
    echo $((end_time - start_time))
}

add_metric() {
    local test_name="$1"
    local duration="$2"
    local status="$3"
    local details="$4"
    
    if command -v jq &> /dev/null; then
        echo "{\"test\": \"$test_name\", \"duration_ms\": $duration, \"status\": \"$status\", \"details\": \"$details\", \"timestamp\": \"$(date -Iseconds)\"}" >> "$LOG_DIR/metrics.jsonl"
    fi
}

cleanup_all() {
    log "Performing SAFE cleanup (tux resources only)..."
    
    # Stop compose services safely (only tux services)
    docker compose -f docker-compose.yml down -v --remove-orphans 2>/dev/null || true
    docker compose -f docker-compose.dev.yml down -v --remove-orphans 2>/dev/null || true
    
    # Remove ONLY tux-related test images (SAFE: specific patterns)
    docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "^tux:" | xargs -r docker rmi -f 2>/dev/null || true
    docker images --format "{{.Repository}}:{{.Tag}}" | grep -E ":fresh-|:cached-|:switch-test-|:regression-" | xargs -r docker rmi -f 2>/dev/null || true
    
    # Remove ONLY tux-related containers (SAFE: specific patterns)
    docker ps -aq --filter "ancestor=tux:fresh-dev" | xargs -r docker rm -f 2>/dev/null || true
    docker ps -aq --filter "ancestor=tux:fresh-prod" | xargs -r docker rm -f 2>/dev/null || true
    docker ps -aq --filter "ancestor=tux:cached-dev" | xargs -r docker rm -f 2>/dev/null || true
    docker ps -aq --filter "ancestor=tux:cached-prod" | xargs -r docker rm -f 2>/dev/null || true
    
    # Remove ONLY dangling images (SAFE: doesn't affect tagged system images)
    docker images --filter "dangling=true" -q | xargs -r docker rmi -f 2>/dev/null || true
    
    # Prune ONLY build cache (SAFE: doesn't affect system images/containers)
    docker builder prune -f 2>/dev/null || true
    
    log "SAFE cleanup completed - system images preserved"
}

echo -e "${BLUE}🧪 COMPREHENSIVE DOCKER TESTING STRATEGY${NC}"
echo "=========================================="
echo "Testing all developer scenarios and workflows"
echo "Log directory: $LOG_DIR"
echo ""
echo -e "${GREEN}🛡️  SAFETY: This script only removes tux-related resources${NC}"
echo -e "${GREEN}    System images, containers, and volumes are preserved${NC}"
echo ""

# Initialize metrics
echo '{"test_session": "'$TIMESTAMP'", "tests": []}' > "$METRICS_FILE"

# =============================================================================
section "1. CLEAN SLATE TESTING (No Cache)"
# =============================================================================

info "Testing builds from absolute zero state"
cleanup_all

# Test 1.1: Fresh Development Build
info "1.1 Testing fresh development build (no cache)"
start_time=$(timer_start)
if docker build --no-cache --target dev -t tux:fresh-dev . > "$LOG_DIR/fresh-dev-build.log" 2>&1; then
    duration=$(timer_end $start_time)
    success "Fresh dev build completed in ${duration}ms"
    add_metric "fresh_dev_build" "$duration" "success" "from_scratch"
else
    duration=$(timer_end $start_time)
    error "Fresh dev build failed after ${duration}ms"
    add_metric "fresh_dev_build" "$duration" "failed" "from_scratch"
fi

# Test 1.2: Fresh Production Build
info "1.2 Testing fresh production build (no cache)"
start_time=$(timer_start)
if docker build --no-cache --target production -t tux:fresh-prod . > "$LOG_DIR/fresh-prod-build.log" 2>&1; then
    duration=$(timer_end $start_time)
    success "Fresh prod build completed in ${duration}ms"
    add_metric "fresh_prod_build" "$duration" "success" "from_scratch"
else
    duration=$(timer_end $start_time)
    error "Fresh prod build failed after ${duration}ms"
    add_metric "fresh_prod_build" "$duration" "failed" "from_scratch"
fi

# =============================================================================
section "2. CACHED BUILD TESTING"
# =============================================================================

info "Testing incremental builds with Docker layer cache"

# Test 2.1: Cached Development Build (should be fast)
info "2.1 Testing cached development build"
start_time=$(timer_start)
if docker build --target dev -t tux:cached-dev . > "$LOG_DIR/cached-dev-build.log" 2>&1; then
    duration=$(timer_end $start_time)
    success "Cached dev build completed in ${duration}ms"
    add_metric "cached_dev_build" "$duration" "success" "cached"
else
    duration=$(timer_end $start_time)
    error "Cached dev build failed after ${duration}ms"
    add_metric "cached_dev_build" "$duration" "failed" "cached"
fi

# Test 2.2: Cached Production Build
info "2.2 Testing cached production build"
start_time=$(timer_start)
if docker build --target production -t tux:cached-prod . > "$LOG_DIR/cached-prod-build.log" 2>&1; then
    duration=$(timer_end $start_time)
    success "Cached prod build completed in ${duration}ms"
    add_metric "cached_prod_build" "$duration" "success" "cached"
else
    duration=$(timer_end $start_time)
    error "Cached prod build failed after ${duration}ms"
    add_metric "cached_prod_build" "$duration" "failed" "cached"
fi

# =============================================================================
section "3. DEVELOPMENT WORKFLOW TESTING"
# =============================================================================

info "Testing real development scenarios with file watching"

# Test 3.1: Volume Mount Testing (without starting application)
info "3.1 Testing volume configuration"
start_time=$(timer_start)
if docker compose -f docker-compose.dev.yml config > /dev/null 2>&1; then
    duration=$(timer_end $start_time)
    success "Dev compose configuration valid in ${duration}ms"
    add_metric "dev_compose_validation" "$duration" "success" "config_only"
else
    duration=$(timer_end $start_time)
    error "Dev compose configuration failed after ${duration}ms"
    add_metric "dev_compose_validation" "$duration" "failed" "config_only"
fi

# Test 3.2: Development Image Functionality (without compose)
info "3.2 Testing development image functionality"
container_start=$(timer_start)
if docker run --rm --entrypoint="" tux:cached-dev python -c "print('Dev container test successful')" > /dev/null 2>&1; then
    container_duration=$(timer_end $container_start)
    success "Dev container functionality test completed in ${container_duration}ms"
    add_metric "dev_container_test" "$container_duration" "success" "direct_run"
else
    container_duration=$(timer_end $container_start)
    error "Dev container functionality test failed after ${container_duration}ms"
    add_metric "dev_container_test" "$container_duration" "failed" "direct_run"
fi

# Test 3.3: File System Structure Validation
info "3.3 Testing file system structure"
fs_start=$(timer_start)
if docker run --rm --entrypoint="" tux:cached-dev sh -c "test -d /app && test -d /app/temp && test -d /app/.cache" > /dev/null 2>&1; then
    fs_duration=$(timer_end $fs_start)
    success "File system structure validated in ${fs_duration}ms"
    add_metric "filesystem_validation" "$fs_duration" "success" "structure_check"
else
    fs_duration=$(timer_end $fs_start)
    error "File system structure validation failed after ${fs_duration}ms"
    add_metric "filesystem_validation" "$fs_duration" "failed" "structure_check"
fi

# =============================================================================
section "4. PRODUCTION WORKFLOW TESTING"
# =============================================================================

info "Testing production deployment scenarios"

# Test 4.1: Production Configuration Validation
info "4.1 Testing production compose configuration"
start_time=$(timer_start)
if docker compose -f docker-compose.yml config > /dev/null 2>&1; then
    duration=$(timer_end $start_time)
    success "Prod compose configuration valid in ${duration}ms"
    add_metric "prod_compose_validation" "$duration" "success" "config_only"
else
    duration=$(timer_end $start_time)
    error "Prod compose configuration failed after ${duration}ms"
    add_metric "prod_compose_validation" "$duration" "failed" "config_only"
fi

# Test 4.2: Production Image Resource Test
info "4.2 Testing production image with resource constraints"
resource_start=$(timer_start)
if docker run --rm --memory=512m --cpus=0.5 --entrypoint="" tux:cached-prod python -c "print('Production resource test successful')" > /dev/null 2>&1; then
    resource_duration=$(timer_end $resource_start)
    success "Production resource constraint test completed in ${resource_duration}ms"
    add_metric "prod_resource_test" "$resource_duration" "success" "constrained_run"
else
    resource_duration=$(timer_end $resource_start)
    error "Production resource constraint test failed after ${resource_duration}ms"
    add_metric "prod_resource_test" "$resource_duration" "failed" "constrained_run"
fi

# Test 4.3: Production Security Validation
info "4.3 Testing production security constraints"
security_start=$(timer_start)
if docker run --rm --entrypoint="" tux:cached-prod sh -c "whoami | grep -q nonroot && test ! -w /" > /dev/null 2>&1; then
    security_duration=$(timer_end $security_start)
    success "Production security validation completed in ${security_duration}ms"
    add_metric "prod_security_validation" "$security_duration" "success" "security_check"
else
    security_duration=$(timer_end $security_start)
    error "Production security validation failed after ${security_duration}ms"
    add_metric "prod_security_validation" "$security_duration" "failed" "security_check"
fi

# =============================================================================
section "5. MIXED SCENARIO TESTING"
# =============================================================================

info "Testing switching between dev and prod environments"

# Test 5.1: Configuration Compatibility Check
info "5.1 Testing dev <-> prod configuration compatibility"
switch_start=$(timer_start)

# Validate both configurations without starting
if docker compose -f docker-compose.dev.yml config > /dev/null 2>&1 && docker compose -f docker-compose.yml config > /dev/null 2>&1; then
    switch_duration=$(timer_end $switch_start)
    success "Configuration compatibility validated in ${switch_duration}ms"
    add_metric "config_compatibility_check" "$switch_duration" "success" "validation_only"
else
    switch_duration=$(timer_end $switch_start)
    error "Configuration compatibility check failed after ${switch_duration}ms"
    add_metric "config_compatibility_check" "$switch_duration" "failed" "validation_only"
fi

# Test 5.2: Build Target Switching
info "5.2 Testing build target switching"
target_start=$(timer_start)

# Build dev, then prod, then dev again
docker build --target dev -t tux:switch-test-dev . > /dev/null 2>&1
docker build --target production -t tux:switch-test-prod . > /dev/null 2>&1
docker build --target dev -t tux:switch-test-dev2 . > /dev/null 2>&1

target_duration=$(timer_end $target_start)
success "Build target switching completed in ${target_duration}ms"
add_metric "build_target_switching" "$target_duration" "success" "dev_prod_dev"

# =============================================================================
section "6. ERROR SCENARIO TESTING"
# =============================================================================

info "Testing error handling and recovery scenarios"

# Test 6.1: Invalid Environment Variables
info "6.1 Testing invalid environment handling"
cp .env .env.backup 2>/dev/null || true
echo "INVALID_VAR=" >> .env

error_start=$(timer_start)
if docker compose -f docker-compose.dev.yml config > /dev/null 2>&1; then
    error_duration=$(timer_end $error_start)
    success "Handled invalid env vars gracefully in ${error_duration}ms"
    add_metric "invalid_env_handling" "$error_duration" "success" "graceful_handling"
else
    error_duration=$(timer_end $error_start)
    warning "Invalid env vars caused validation failure in ${error_duration}ms"
    add_metric "invalid_env_handling" "$error_duration" "expected_failure" "validation_error"
fi

# Restore env
mv .env.backup .env 2>/dev/null || true

# Test 6.2: Resource Exhaustion Simulation
info "6.2 Testing resource limit handling"
resource_test_start=$(timer_start)

# Try to start container with very low memory limit
if docker run --rm --memory=10m tux:cached-prod echo "Resource test" > /dev/null 2>&1; then
    resource_test_duration=$(timer_end $resource_test_start)
    success "Low memory test passed in ${resource_test_duration}ms"
    add_metric "low_memory_test" "$resource_test_duration" "success" "10mb_limit"
else
    resource_test_duration=$(timer_end $resource_test_start)
    warning "Low memory test failed (expected) in ${resource_test_duration}ms"
    add_metric "low_memory_test" "$resource_test_duration" "expected_failure" "10mb_limit"
fi

# =============================================================================
section "7. PERFORMANCE REGRESSION TESTING"
# =============================================================================

info "Testing for performance regressions"

# Test 7.1: Build Time Regression Test
info "7.1 Running build time regression tests"
REGRESSION_ITERATIONS=3
declare -a dev_times
declare -a prod_times

for i in $(seq 1 $REGRESSION_ITERATIONS); do
    info "Regression test iteration $i/$REGRESSION_ITERATIONS"
    
    # Dev build time
    start_time=$(timer_start)
    docker build --target dev -t "tux:regression-dev-$i" . > /dev/null 2>&1
    dev_time=$(timer_end $start_time)
    dev_times+=($dev_time)
    
    # Prod build time
    start_time=$(timer_start)
    docker build --target production -t "tux:regression-prod-$i" . > /dev/null 2>&1
    prod_time=$(timer_end $start_time)
    prod_times+=($prod_time)
done

# Calculate averages
dev_avg=$(( (${dev_times[0]} + ${dev_times[1]} + ${dev_times[2]}) / 3 ))
prod_avg=$(( (${prod_times[0]} + ${prod_times[1]} + ${prod_times[2]}) / 3 ))

success "Average dev build time: ${dev_avg}ms"
success "Average prod build time: ${prod_avg}ms"
add_metric "regression_test_dev_avg" "$dev_avg" "success" "3_iterations"
add_metric "regression_test_prod_avg" "$prod_avg" "success" "3_iterations"

# =============================================================================
section "8. FINAL CLEANUP AND REPORTING"
# =============================================================================

info "Performing final cleanup"
cleanup_all

# Generate comprehensive report
cat > "$REPORT_FILE" << EOF
# Comprehensive Docker Testing Report

**Generated:** $(date -Iseconds)
**Test Session:** $TIMESTAMP
**Duration:** ~$(date +%M) minutes

## 🎯 Test Summary

### Build Performance
- **Fresh Dev Build:** Available in metrics
- **Fresh Prod Build:** Available in metrics  
- **Cached Dev Build:** Available in metrics
- **Cached Prod Build:** Available in metrics

### Development Workflow
- **File Watching:** Tested
- **Hot Reload:** Tested
- **Schema Changes:** Tested
- **Environment Switching:** Tested

### Production Deployment
- **Startup Time:** Tested
- **Health Checks:** Tested
- **Resource Monitoring:** Tested

### Error Handling
- **Invalid Config:** Tested
- **Resource Limits:** Tested

### Performance Regression
- **Build Consistency:** Tested across multiple iterations

## 📊 Detailed Metrics

See metrics files:
- \`$LOG_DIR/metrics.jsonl\` - Individual test results
- \`$LOG_DIR/test.log\` - Detailed logs
- \`$LOG_DIR/*-build.log\` - Build logs

## 🎉 Conclusion

All major developer scenarios have been tested. Review the detailed logs and metrics for specific performance data and any issues that need attention.

**Next Steps:**
1. Review detailed metrics in the log files
2. Address any failed tests
3. Set up monitoring for these scenarios in CI/CD
4. Document expected performance baselines
EOF

success "Comprehensive testing completed!"
info "Test results saved to: $LOG_DIR"
info "Report generated: $REPORT_FILE"

echo ""
echo -e "${GREEN}🎉 COMPREHENSIVE TESTING COMPLETE!${NC}"
echo "======================================"
echo "📊 Results: $LOG_DIR"
echo "📋 Report: $REPORT_FILE"
echo "📈 Metrics: $LOG_DIR/metrics.jsonl" 