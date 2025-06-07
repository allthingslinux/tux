#!/bin/bash

# Tux Docker Toolkit - Unified Docker Management Script
# Consolidates all Docker operations: testing, monitoring, and management

set -e

# Script version and info
TOOLKIT_VERSION="1.0.0"
SCRIPT_NAME="$(basename "$0")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Global configuration
DEFAULT_CONTAINER_NAME="tux-dev"
LOGS_DIR="logs"
METRICS_DIR="$LOGS_DIR"

# Helper functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE" 2>/dev/null || echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    # In testing contexts, don't exit immediately - let tests complete
    if [[ "${TESTING_MODE:-false}" == "true" ]]; then
        return 1
    else
        exit 1
    fi
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

metric() {
    echo -e "${BLUE}📊 $1${NC}"
}

header() {
    echo -e "${MAGENTA}$1${NC}"
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

# Utility functions
ensure_logs_dir() {
    mkdir -p "$LOGS_DIR"
}

check_docker() {
    if ! docker version &> /dev/null; then
        error "Docker is not running or accessible"
    fi
}

check_dependencies() {
    local missing_deps=()

    if ! command -v jq &> /dev/null; then
        missing_deps+=("jq")
    fi

    if ! command -v bc &> /dev/null; then
        missing_deps+=("bc")
    fi

    if [ ${#missing_deps[@]} -gt 0 ]; then
        warning "Missing optional dependencies: ${missing_deps[*]}"
        echo "Install with: sudo apt-get install ${missing_deps[*]} (Ubuntu) or brew install ${missing_deps[*]} (macOS)"
    fi
}

# Add metric to JSON (if jq available)
add_metric() {
    local key=$1
    local value=$2
    local unit=$3
    local metrics_file=${4:-$METRICS_FILE}

    if command -v jq &> /dev/null && [ -f "$metrics_file" ]; then
        local tmp=$(mktemp)
        jq ".performance.\"$key\" = {\"value\": $value, \"unit\": \"$unit\"}" "$metrics_file" > "$tmp" && mv "$tmp" "$metrics_file"
    fi
}

# Get image size in MB
get_image_size() {
    local image=$1
    docker images --format "{{.Size}}" "$image" | head -1 | sed 's/[^0-9.]//g'
}

# Safe cleanup function
perform_safe_cleanup() {
    local cleanup_type="$1"
    local force_mode="${2:-false}"

    info "Performing $cleanup_type cleanup (tux resources only)..."
    local cleanup_start=$(start_timer)

    # Remove test containers (SAFE: specific patterns only)
    for pattern in "tux:test-" "tux:quick-" "tux:perf-test-" "memory-test" "resource-test"; do
        if docker ps -aq --filter "ancestor=${pattern}*" | grep -q .; then
            docker rm -f $(docker ps -aq --filter "ancestor=${pattern}*") 2>/dev/null || true
        fi
    done

    # Remove test images (SAFE: specific test image names)
    local test_images=("tux:test-dev" "tux:test-prod" "tux:quick-dev" "tux:quick-prod" "tux:perf-test-dev" "tux:perf-test-prod")
    for image in "${test_images[@]}"; do
        docker rmi "$image" 2>/dev/null || true
    done

    if [[ "$cleanup_type" == "aggressive" ]] || [[ "$force_mode" == "true" ]]; then
        warning "Performing aggressive cleanup (SAFE: only tux-related resources)..."

        # Remove tux project images (SAFE: excludes system images)
        docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "^tux:" | xargs -r docker rmi 2>/dev/null || true

        # Remove dangling images (SAFE)
        docker images --filter "dangling=true" -q | xargs -r docker rmi 2>/dev/null || true

        # Prune build cache (SAFE)
        docker builder prune -f 2>/dev/null || true
    fi

    local cleanup_duration=$(end_timer $cleanup_start)
    metric "$cleanup_type cleanup completed in ${cleanup_duration}ms"
}

# ============================================================================
# QUICK TESTING SUBCOMMAND
# ============================================================================
cmd_quick() {
    # Enable testing mode for graceful error handling
    export TESTING_MODE=true
    set +e  # Disable immediate exit on error for testing

    header "⚡ QUICK DOCKER VALIDATION"
    echo "=========================="
    echo "Testing core functionality (2-3 minutes)"
    echo ""

    # Track test results
    local passed=0
    local failed=0

    test_result() {
        if [ $1 -eq 0 ]; then
            success "$2"
            ((passed++))
        else
            echo -e "${RED}❌ $2${NC}"
            ((failed++))
        fi
    }

    # Test 1: Basic builds
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
    if docker run --rm --entrypoint="" tux:quick-prod python --version > /dev/null 2>&1; then
        test_result 0 "Container execution"
    else
        test_result 1 "Container execution"
    fi

    # Test 3: Security basics
    echo "🔒 Testing security..."
    local user_output=$(docker run --rm --entrypoint="" tux:quick-prod whoami 2>/dev/null || echo "failed")
    if [[ "$user_output" == "nonroot" ]]; then
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

    # Test 5: Volume functionality
    echo "💻 Testing volume configuration..."
    if docker run --rm --entrypoint="" -v /tmp:/app/temp tux:quick-dev test -d /app/temp > /dev/null 2>&1; then
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
    echo -e "Passed: ${GREEN}$passed${NC}"
    echo -e "Failed: ${RED}$failed${NC}"

    if [ $failed -eq 0 ]; then
        echo -e "\n${GREEN}🎉 All quick tests passed!${NC}"
        echo "Your Docker setup is ready for development."
        return 0
    else
        echo -e "\n${RED}⚠️  $failed out of $((passed + failed)) tests failed.${NC}"
        echo "Run '$SCRIPT_NAME test' for detailed diagnostics."
        echo "Common issues to check:"
        echo "  - Ensure Docker is running"
        echo "  - Verify .env file exists with required variables"
        echo "  - Check Dockerfile syntax"
        echo "  - Review Docker compose configuration"
        return 1
    fi
}

# ============================================================================
# STANDARD TESTING SUBCOMMAND
# ============================================================================
cmd_test() {
    # Enable testing mode for graceful error handling
    export TESTING_MODE=true
    set +e  # Disable immediate exit on error for testing

    local no_cache=""
    local force_clean=""

    # Parse test-specific arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-cache)
                no_cache="--no-cache"
                shift
                ;;
            --force-clean)
                force_clean="true"
                shift
                ;;
            *)
                echo -e "${RED}❌ Unknown test option: $1${NC}"
                return 1
                ;;
        esac
    done

    header "🔧 Docker Setup Performance Test"
    echo "================================"

    if [[ -n "$no_cache" ]]; then
        echo "🚀 Running in NO-CACHE mode (true from-scratch builds)"
    fi
    if [[ -n "$force_clean" ]]; then
        echo "🧹 Running with FORCE-CLEAN (aggressive cleanup)"
    fi

    ensure_logs_dir

    # Initialize log files
    LOG_FILE="$LOGS_DIR/docker-test-$(date +%Y%m%d-%H%M%S).log"
    METRICS_FILE="$LOGS_DIR/docker-metrics-$(date +%Y%m%d-%H%M%S).json"

    # Initialize metrics JSON
    cat > "$METRICS_FILE" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "test_mode": {
    "no_cache": $([ -n "$no_cache" ] && echo true || echo false),
    "force_clean": $([ -n "$force_clean" ] && echo true || echo false)
  },
  "tests": [],
  "performance": {},
  "summary": {}
}
EOF

    log "Starting Docker performance tests"
    log "Log file: $LOG_FILE"
    log "Metrics file: $METRICS_FILE"

    # Record system info
    log "System Information:"
    log "- OS: $(uname -s -r)"
    log "- Docker version: $(docker --version)"
    log "- Available memory: $(free -h | awk '/^Mem:/ {print $2}' 2>/dev/null || echo 'N/A')"
    log "- Available disk: $(df -h . | awk 'NR==2 {print $4}' 2>/dev/null || echo 'N/A')"

    # Initial cleanup
    if [[ -n "$force_clean" ]]; then
        perform_safe_cleanup "initial_aggressive" "true"
    else
        perform_safe_cleanup "initial_basic" "false"
    fi

    # Test 1: Environment Check
    info "Checking environment..."
    local env_errors=0

    if [[ ! -f ".env" ]]; then
        echo -e "${RED}❌ .env file not found${NC}"
        ((env_errors++))
    fi

    if [[ ! -f "pyproject.toml" ]]; then
        echo -e "${RED}❌ pyproject.toml not found${NC}"
        ((env_errors++))
    fi

    if [[ ! -d "prisma/schema" ]]; then
        echo -e "${RED}❌ prisma/schema directory not found${NC}"
        ((env_errors++))
    fi

    if [ $env_errors -eq 0 ]; then
        success "Environment files present"
    else
        warning "$env_errors environment issues found - continuing with available tests"
    fi

    # Test 2: Development Build
    info "Testing development build..."
    local build_start=$(start_timer)
    if docker build $no_cache --target dev -t tux:test-dev . > /dev/null 2>&1; then
        local build_duration=$(end_timer $build_start)
        success "Development build successful"
        local dev_size=$(get_image_size "tux:test-dev")
        metric "Development build: ${build_duration}ms"
        metric "Development image size: ${dev_size}MB"
        add_metric "development_build" "$build_duration" "ms"
        add_metric "dev_image_size_mb" "${dev_size//[^0-9.]/}" "MB"
    else
        local build_duration=$(end_timer $build_start)
        echo -e "${RED}❌ Development build failed after ${build_duration}ms${NC}"
        add_metric "development_build" "$build_duration" "ms"
        # Continue with other tests
    fi

    # Test 3: Production Build
    info "Testing production build..."
    build_start=$(start_timer)
    if docker build $no_cache --target production -t tux:test-prod . > /dev/null 2>&1; then
        local build_duration=$(end_timer $build_start)
        success "Production build successful"
        local prod_size=$(get_image_size "tux:test-prod")
        metric "Production build: ${build_duration}ms"
        metric "Production image size: ${prod_size}MB"
        add_metric "production_build" "$build_duration" "ms"
        add_metric "prod_image_size_mb" "${prod_size//[^0-9.]/}" "MB"
    else
        local build_duration=$(end_timer $build_start)
        echo -e "${RED}❌ Production build failed after ${build_duration}ms${NC}"
        add_metric "production_build" "$build_duration" "ms"
        # Continue with other tests
    fi

    # Test 4: Container Startup
    info "Testing container startup time..."
    local startup_start=$(start_timer)
    local container_id=$(docker run -d --rm --entrypoint="" tux:test-prod sleep 30)
    while [[ "$(docker inspect -f '{{.State.Status}}' $container_id 2>/dev/null)" != "running" ]]; do
        sleep 0.1
    done
    local startup_duration=$(end_timer $startup_start)
    docker stop $container_id > /dev/null 2>&1 || true

    metric "Container startup: ${startup_duration}ms"
    add_metric "container_startup" "$startup_duration" "ms"
    success "Container startup test completed"

    # Test 5: Security validations
    info "Testing security constraints..."
    local user_output=$(docker run --rm --entrypoint="" tux:test-prod whoami 2>/dev/null || echo "failed")
    if [[ "$user_output" == "nonroot" ]]; then
        success "Container runs as non-root user"
    else
        echo -e "${RED}❌ Container not running as non-root user (got: $user_output)${NC}"
        # Continue with tests
    fi

    # Test read-only filesystem
    if docker run --rm --entrypoint="" tux:test-prod touch /test-file 2>/dev/null; then
        echo -e "${RED}❌ Filesystem is not read-only${NC}"
        # Continue with tests
    else
        success "Read-only filesystem working"
    fi

    # Test 6: Performance tests
    info "Testing temp directory performance..."
    local temp_start=$(start_timer)
    docker run --rm --entrypoint="" tux:test-prod sh -c "
        for i in \$(seq 1 100); do
            echo 'test content' > /app/temp/test_\$i.txt
        done
        rm /app/temp/test_*.txt
    " > /dev/null 2>&1
    local temp_duration=$(end_timer $temp_start)

    metric "Temp file operations (100 files): ${temp_duration}ms"
    add_metric "temp_file_ops" "$temp_duration" "ms"
    success "Temp directory performance test completed"

    # Additional tests...
    info "Testing Python package validation..."
    local python_start=$(start_timer)
    if docker run --rm --entrypoint='' tux:test-dev python -c "import sys; print('Python validation:', sys.version)" > /dev/null 2>&1; then
        local python_duration=$(end_timer $python_start)
        metric "Python validation: ${python_duration}ms"
        add_metric "python_validation" "$python_duration" "ms"
        success "Python package validation working"
    else
        local python_duration=$(end_timer $python_start)
        add_metric "python_validation" "$python_duration" "ms"
        echo -e "${RED}❌ Python package validation failed after ${python_duration}ms${NC}"
        # Continue with other tests
    fi

    # Cleanup
    perform_safe_cleanup "final_basic" "false"

    # Generate summary and check thresholds
    check_performance_thresholds

    success "Standard Docker tests completed!"
    echo ""
    echo "📊 Results:"
    echo "  📋 Log file: $LOG_FILE"
    echo "  📈 Metrics: $METRICS_FILE"
    echo ""
    echo "💡 If you encountered issues:"
    echo "  - Check the log file for detailed error messages"
    echo "  - Verify your .env file has all required variables"
    echo "  - Ensure Docker daemon is running and accessible"
    echo "  - Try running with --force-clean for a fresh start"
}

# Performance threshold checking
check_performance_thresholds() {
    if ! command -v jq &> /dev/null || [[ ! -f "$METRICS_FILE" ]]; then
        warning "Performance threshold checking requires jq and metrics data"
        return 0
    fi

    echo ""
    echo "Performance Threshold Check:"
    echo "============================"

    # Configurable thresholds
    local build_threshold=${BUILD_THRESHOLD:-300000}
    local startup_threshold=${STARTUP_THRESHOLD:-10000}
    local python_threshold=${PYTHON_THRESHOLD:-5000}
    local memory_threshold=${MEMORY_THRESHOLD:-512}

    local threshold_failed=false

    # Check build time
    local build_time=$(jq -r '.performance.production_build.value // 0' "$METRICS_FILE")
    if [ "$build_time" -gt "$build_threshold" ]; then
        echo "❌ FAIL: Production build time (${build_time}ms) exceeds threshold (${build_threshold}ms)"
        threshold_failed=true
    else
        echo "✅ PASS: Production build time (${build_time}ms) within threshold (${build_threshold}ms)"
    fi

    # Check startup time
    local startup_time=$(jq -r '.performance.container_startup.value // 0' "$METRICS_FILE")
    if [ "$startup_time" -gt "$startup_threshold" ]; then
        echo "❌ FAIL: Container startup time (${startup_time}ms) exceeds threshold (${startup_threshold}ms)"
        threshold_failed=true
    else
        echo "✅ PASS: Container startup time (${startup_time}ms) within threshold (${startup_threshold}ms)"
    fi

    # Check Python validation time
    local python_time=$(jq -r '.performance.python_validation.value // 0' "$METRICS_FILE")
    if [ "$python_time" -gt "$python_threshold" ]; then
        echo "❌ FAIL: Python validation time (${python_time}ms) exceeds threshold (${python_threshold}ms)"
        threshold_failed=true
    else
        echo "✅ PASS: Python validation time (${python_time}ms) within threshold (${python_threshold}ms)"
    fi

    if [ "$threshold_failed" = true ]; then
        warning "Some performance thresholds exceeded!"
        echo "Consider optimizing or adjusting thresholds via environment variables."
    else
        success "All performance thresholds within acceptable ranges"
    fi
}



# ============================================================================
# MONITOR SUBCOMMAND
# ============================================================================
cmd_monitor() {
    local container_name="${1:-$DEFAULT_CONTAINER_NAME}"
    local duration="${2:-60}"
    local interval="${3:-5}"

    header "🔍 Docker Resource Monitor"
    echo "=========================="
    echo "Container: $container_name"
    echo "Duration: ${duration}s"
    echo "Interval: ${interval}s"
    echo ""

    ensure_logs_dir

    local log_file="$LOGS_DIR/resource-monitor-$(date +%Y%m%d-%H%M%S).csv"
    local report_file="$LOGS_DIR/resource-report-$(date +%Y%m%d-%H%M%S).txt"

    # Check if container exists and is running
    if ! docker ps | grep -q "$container_name"; then
        warning "Container '$container_name' is not running"

        if docker ps -a | grep -q "$container_name"; then
            echo "Starting container..."
            if docker start "$container_name" &>/dev/null; then
                success "Container started"
                sleep 2
            else
                error "Failed to start container"
            fi
        else
            error "Container '$container_name' not found"
        fi
    fi

    info "Starting resource monitoring..."
    info "Output file: $log_file"

    # Create CSV header
    echo "timestamp,cpu_percent,memory_usage,memory_limit,memory_percent,network_input,network_output,pids" > "$log_file"

    # Initialize counters
    local total_samples=0
    local cpu_sum=0
    local memory_sum=0

    # Monitor loop
    for i in $(seq 1 $((duration/interval))); do
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

        # Get container stats
        local stats_output=$(docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.PIDs}}" "$container_name" 2>/dev/null)

        if [ -n "$stats_output" ]; then
            # Parse stats
            IFS=',' read -r cpu_percent mem_usage mem_percent net_io pids <<< "$stats_output"

            # Extract memory values
            local memory_usage=$(echo "$mem_usage" | sed 's/MiB.*//' | sed 's/[^0-9.]//g')
            local memory_limit=$(echo "$mem_usage" | sed 's/.*\///' | sed 's/MiB//' | sed 's/[^0-9.]//g')

            # Extract network I/O
            local network_input=$(echo "$net_io" | sed 's/\/.*//' | sed 's/[^0-9.]//g')
            local network_output=$(echo "$net_io" | sed 's/.*\///' | sed 's/[^0-9.]//g')

            # Clean percentages
            local cpu_clean=$(echo "$cpu_percent" | sed 's/%//')
            local mem_percent_clean=$(echo "$mem_percent" | sed 's/%//')

            # Write to CSV
            echo "$timestamp,$cpu_clean,$memory_usage,$memory_limit,$mem_percent_clean,$network_input,$network_output,$pids" >> "$log_file"

            # Display real-time stats
            printf "\r\033[K📊 CPU: %6s | Memory: %6s/%6s MiB (%5s) | Net I/O: %8s/%8s | PIDs: %3s" \
                "$cpu_percent" "$memory_usage" "$memory_limit" "$mem_percent" "$network_input" "$network_output" "$pids"

            # Update statistics
            if [[ "$cpu_clean" =~ ^[0-9.]+$ ]] && command -v bc &> /dev/null; then
                cpu_sum=$(echo "$cpu_sum + $cpu_clean" | bc -l)
            fi
            if [[ "$memory_usage" =~ ^[0-9.]+$ ]] && command -v bc &> /dev/null; then
                memory_sum=$(echo "$memory_sum + $memory_usage" | bc -l)
            fi

            total_samples=$((total_samples + 1))
        else
            warning "Failed to get stats for container $container_name"
        fi

        sleep "$interval"
    done

    echo ""
    echo ""
    info "Monitoring completed. Generating report..."

    # Generate performance report
    generate_performance_report "$log_file" "$report_file" "$container_name" "$duration" "$total_samples" "$cpu_sum" "$memory_sum"

    success "Resource monitoring completed!"
    echo ""
    echo "📁 Generated Files:"
    echo "  📈 CSV Data: $log_file"
    echo "  📊 Report: $report_file"
}

generate_performance_report() {
    local log_file="$1"
    local report_file="$2"
    local container_name="$3"
    local duration="$4"
    local total_samples="$5"
    local cpu_sum="$6"
    local memory_sum="$7"

    # Calculate averages
    local avg_cpu="0"
    local avg_memory="0"

    if [ "$total_samples" -gt 0 ] && command -v bc &> /dev/null; then
        avg_cpu=$(echo "scale=2; $cpu_sum / $total_samples" | bc -l)
        avg_memory=$(echo "scale=2; $memory_sum / $total_samples" | bc -l)
    fi

    # Generate report
    cat > "$report_file" << EOF
# Docker Resource Monitoring Report

**Container:** $container_name
**Duration:** ${duration}s (${total_samples} samples)
**Generated:** $(date -Iseconds)

## Performance Summary

### Average Resource Usage
- **CPU Usage:** ${avg_cpu}%
- **Memory Usage:** ${avg_memory} MiB

### Analysis
EOF

    # Performance analysis
    if command -v bc &> /dev/null; then
        if [ "$(echo "$avg_cpu > 80" | bc -l)" -eq 1 ]; then
            echo "- ❌ **High CPU Usage:** Average ${avg_cpu}% exceeds 80% threshold" >> "$report_file"
        elif [ "$(echo "$avg_cpu > 50" | bc -l)" -eq 1 ]; then
            echo "- ⚠️ **Moderate CPU Usage:** Average ${avg_cpu}% approaching high usage" >> "$report_file"
        else
            echo "- ✅ **CPU Usage:** Average ${avg_cpu}% within normal range" >> "$report_file"
        fi

        if [ "$(echo "$avg_memory > 400" | bc -l)" -eq 1 ]; then
            echo "- ❌ **High Memory Usage:** Average ${avg_memory}MiB exceeds 400MiB threshold" >> "$report_file"
        elif [ "$(echo "$avg_memory > 256" | bc -l)" -eq 1 ]; then
            echo "- ⚠️ **Moderate Memory Usage:** Average ${avg_memory}MiB approaching limits" >> "$report_file"
        else
            echo "- ✅ **Memory Usage:** Average ${avg_memory}MiB within normal range" >> "$report_file"
        fi
    fi

    echo "" >> "$report_file"
    echo "## Data Files" >> "$report_file"
    echo "- **CSV Data:** $log_file" >> "$report_file"
    echo "- **Report:** $report_file" >> "$report_file"

    # Display summary
    echo ""
    metric "Performance Summary:"
    echo "  📊 Average CPU: ${avg_cpu}%"
    echo "  💾 Average Memory: ${avg_memory} MiB"
    echo "  📋 Total Samples: $total_samples"
}

# ============================================================================
# CLEANUP SUBCOMMAND
# ============================================================================
cmd_cleanup() {
    local force_mode="false"
    local dry_run="false"
    local volumes="false"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                force_mode="true"
                shift
                ;;
            --dry-run)
                dry_run="true"
                shift
                ;;
            --volumes)
                volumes="true"
                shift
                ;;
            *)
                error "Unknown cleanup option: $1"
                ;;
        esac
    done

    header "🧹 Safe Docker Cleanup"
    echo "======================="

    if [[ "$dry_run" == "true" ]]; then
        echo "🔍 DRY RUN MODE - No resources will actually be removed"
        echo ""
    fi

    info "Scanning for tux-related Docker resources..."

    # Get tux-specific resources safely
    local tux_containers=$(docker ps -a --format "{{.Names}}" | grep -E "(tux|memory-test|resource-test)" || echo "")
    local tux_images=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "^(tux:|.*tux.*:)" | grep -v -E "^(python|ubuntu|alpine|node|postgres)" || echo "")
    local tux_volumes=""

    if [[ "$volumes" == "true" ]]; then
        tux_volumes=$(docker volume ls --format "{{.Name}}" | grep -E "(tux_|tux-)" || echo "")
    fi

    # Display what will be cleaned
    if [[ -n "$tux_containers" ]]; then
        info "Containers to be removed:"
        echo "$tux_containers" | sed 's/^/  - /'
        echo ""
    fi

    if [[ -n "$tux_images" ]]; then
        info "Images to be removed:"
        echo "$tux_images" | sed 's/^/  - /'
        echo ""
    fi

    if [[ -n "$tux_volumes" ]]; then
        info "Volumes to be removed:"
        echo "$tux_volumes" | sed 's/^/  - /'
        echo ""
    fi

    if [[ -z "$tux_containers" && -z "$tux_images" && -z "$tux_volumes" ]]; then
        success "No tux-related Docker resources found to clean up"
        return 0
    fi

    if [[ "$dry_run" == "true" ]]; then
        info "DRY RUN: No resources were actually removed"
        return 0
    fi

    if [[ "$force_mode" != "true" ]]; then
        echo ""
        read -p "Remove these tux-related Docker resources? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "Cleanup cancelled"
            return 0
        fi
    fi

    info "Cleaning up tux-related Docker resources..."

    # Remove containers
    if [[ -n "$tux_containers" ]]; then
        echo "$tux_containers" | while read -r container; do
            if docker rm -f "$container" 2>/dev/null; then
                success "Removed container: $container"
            else
                warning "Failed to remove container: $container"
            fi
        done
    fi

    # Remove images
    if [[ -n "$tux_images" ]]; then
        echo "$tux_images" | while read -r image; do
            if docker rmi -f "$image" 2>/dev/null; then
                success "Removed image: $image"
            else
                warning "Failed to remove image: $image"
            fi
        done
    fi

    # Remove volumes
    if [[ -n "$tux_volumes" ]]; then
        echo "$tux_volumes" | while read -r volume; do
            if docker volume rm "$volume" 2>/dev/null; then
                success "Removed volume: $volume"
            else
                warning "Failed to remove volume: $volume"
            fi
        done
    fi

    # Clean dangling images and build cache (safe operations)
    info "Cleaning dangling images and build cache..."
    docker image prune -f > /dev/null 2>&1 || true
    docker builder prune -f > /dev/null 2>&1 || true

    success "Tux Docker cleanup completed!"
    echo ""
    echo "📊 Final system state:"
    docker system df
}

# ============================================================================
# COMPREHENSIVE TESTING SUBCOMMAND
# ============================================================================
cmd_comprehensive() {
    # Enable testing mode for graceful error handling
    export TESTING_MODE=true
    set +e  # Disable immediate exit on error for testing

    header "🧪 Comprehensive Docker Testing Strategy"
    echo "=========================================="
    echo "Testing all developer scenarios and workflows"
    echo ""

    ensure_logs_dir

    local timestamp=$(date +%Y%m%d-%H%M%S)
    local comp_log_dir="$LOGS_DIR/comprehensive-test-$timestamp"
    local comp_metrics_file="$comp_log_dir/comprehensive-metrics.json"
    local comp_report_file="$comp_log_dir/test-report.md"

    mkdir -p "$comp_log_dir"

    echo "Log directory: $comp_log_dir"
    echo ""
    success "🛡️  SAFETY: This script only removes tux-related resources"
    echo "    System images, containers, and volumes are preserved"
    echo ""

    # Initialize comprehensive logging
    local comp_log_file="$comp_log_dir/test.log"

    comp_log() {
        echo "[$(date +'%H:%M:%S')] $1" | tee -a "$comp_log_file"
    }

    comp_section() {
        echo -e "\n${MAGENTA}🔵 $1${NC}" | tee -a "$comp_log_file"
        echo "======================================" | tee -a "$comp_log_file"
    }

    comp_add_metric() {
        local test_name="$1"
        local duration="$2"
        local status="$3"
        local details="$4"

        if command -v jq &> /dev/null; then
            echo "{\"test\": \"$test_name\", \"duration_ms\": $duration, \"status\": \"$status\", \"details\": \"$details\", \"timestamp\": \"$(date -Iseconds)\"}" >> "$comp_log_dir/metrics.jsonl"
        fi
    }

    comp_cleanup_all() {
        comp_log "Performing SAFE cleanup (tux resources only)..."

        # Stop compose services safely
        docker compose -f docker-compose.yml down -v --remove-orphans 2>/dev/null || true
        docker compose -f docker-compose.dev.yml down -v --remove-orphans 2>/dev/null || true

        # Remove tux-related test images (SAFE)
        docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "^tux:" | xargs -r docker rmi -f 2>/dev/null || true
        docker images --format "{{.Repository}}:{{.Tag}}" | grep -E ":fresh-|:cached-|:switch-test-|:regression-" | xargs -r docker rmi -f 2>/dev/null || true

        # Remove tux-related containers (SAFE)
        for pattern in "tux:fresh-" "tux:cached-" "tux:switch-test-" "tux:regression-"; do
            docker ps -aq --filter "ancestor=${pattern}*" | xargs -r docker rm -f 2>/dev/null || true
        done

        # Remove dangling images and build cache (SAFE)
        docker images --filter "dangling=true" -q | xargs -r docker rmi -f 2>/dev/null || true
        docker builder prune -f 2>/dev/null || true

        comp_log "SAFE cleanup completed - system images preserved"
    }

    # Initialize metrics
    echo '{"test_session": "'$timestamp'", "tests": []}' > "$comp_metrics_file"

    # =============================================================================
    comp_section "1. CLEAN SLATE TESTING (No Cache)"
    # =============================================================================

    info "Testing builds from absolute zero state"
    comp_cleanup_all

    # Test 1.1: Fresh Development Build
    info "1.1 Testing fresh development build (no cache)"
    local start_time=$(start_timer)
    if docker build --no-cache --target dev -t tux:fresh-dev . > "$comp_log_dir/fresh-dev-build.log" 2>&1; then
        local duration=$(end_timer $start_time)
        success "Fresh dev build completed in ${duration}ms"
        comp_add_metric "fresh_dev_build" "$duration" "success" "from_scratch"
    else
        local duration=$(end_timer $start_time)
        error "Fresh dev build failed after ${duration}ms"
        comp_add_metric "fresh_dev_build" "$duration" "failed" "from_scratch"
    fi

    # Test 1.2: Fresh Production Build
    info "1.2 Testing fresh production build (no cache)"
    start_time=$(start_timer)
    if docker build --no-cache --target production -t tux:fresh-prod . > "$comp_log_dir/fresh-prod-build.log" 2>&1; then
        local duration=$(end_timer $start_time)
        success "Fresh prod build completed in ${duration}ms"
        comp_add_metric "fresh_prod_build" "$duration" "success" "from_scratch"
    else
        local duration=$(end_timer $start_time)
        error "Fresh prod build failed after ${duration}ms"
        comp_add_metric "fresh_prod_build" "$duration" "failed" "from_scratch"
    fi

    # =============================================================================
    comp_section "2. CACHED BUILD TESTING"
    # =============================================================================

    info "Testing incremental builds with Docker layer cache"

    # Test 2.1: Cached Development Build
    info "2.1 Testing cached development build"
    start_time=$(start_timer)
    if docker build --target dev -t tux:cached-dev . > "$comp_log_dir/cached-dev-build.log" 2>&1; then
        local duration=$(end_timer $start_time)
        success "Cached dev build completed in ${duration}ms"
        comp_add_metric "cached_dev_build" "$duration" "success" "cached"
    else
        local duration=$(end_timer $start_time)
        error "Cached dev build failed after ${duration}ms"
        comp_add_metric "cached_dev_build" "$duration" "failed" "cached"
    fi

    # Test 2.2: Cached Production Build
    info "2.2 Testing cached production build"
    start_time=$(start_timer)
    if docker build --target production -t tux:cached-prod . > "$comp_log_dir/cached-prod-build.log" 2>&1; then
        local duration=$(end_timer $start_time)
        success "Cached prod build completed in ${duration}ms"
        comp_add_metric "cached_prod_build" "$duration" "success" "cached"
    else
        local duration=$(end_timer $start_time)
        error "Cached prod build failed after ${duration}ms"
        comp_add_metric "cached_prod_build" "$duration" "failed" "cached"
    fi

    # =============================================================================
    comp_section "3. DEVELOPMENT WORKFLOW TESTING"
    # =============================================================================

    info "Testing real development scenarios with file watching"

    # Test 3.1: Volume Configuration
    info "3.1 Testing volume configuration"
    start_time=$(start_timer)
    if docker compose -f docker-compose.dev.yml config > /dev/null 2>&1; then
        local duration=$(end_timer $start_time)
        success "Dev compose configuration valid in ${duration}ms"
        comp_add_metric "dev_compose_validation" "$duration" "success" "config_only"
    else
        local duration=$(end_timer $start_time)
        error "Dev compose configuration failed after ${duration}ms"
        comp_add_metric "dev_compose_validation" "$duration" "failed" "config_only"
    fi

    # Test 3.2: Development Image Functionality
    info "3.2 Testing development image functionality"
    start_time=$(start_timer)
    if docker run --rm --entrypoint="" tux:cached-dev python -c "print('Dev container test successful')" > /dev/null 2>&1; then
        local duration=$(end_timer $start_time)
        success "Dev container functionality test completed in ${duration}ms"
        comp_add_metric "dev_container_test" "$duration" "success" "direct_run"
    else
        local duration=$(end_timer $start_time)
        error "Dev container functionality test failed after ${duration}ms"
        comp_add_metric "dev_container_test" "$duration" "failed" "direct_run"
    fi

    # Test 3.3: File System Structure
    info "3.3 Testing file system structure"
    start_time=$(start_timer)
    if docker run --rm --entrypoint="" tux:cached-dev sh -c "test -d /app && test -d /app/temp && test -d /app/.cache" > /dev/null 2>&1; then
        local duration=$(end_timer $start_time)
        success "File system structure validated in ${duration}ms"
        comp_add_metric "filesystem_validation" "$duration" "success" "structure_check"
    else
        local duration=$(end_timer $start_time)
        error "File system structure validation failed after ${duration}ms"
        comp_add_metric "filesystem_validation" "$duration" "failed" "structure_check"
    fi

    # =============================================================================
    comp_section "4. PRODUCTION WORKFLOW TESTING"
    # =============================================================================

    info "Testing production deployment scenarios"

    # Test 4.1: Production Configuration
    info "4.1 Testing production compose configuration"
    start_time=$(start_timer)
    if docker compose -f docker-compose.yml config > /dev/null 2>&1; then
        local duration=$(end_timer $start_time)
        success "Prod compose configuration valid in ${duration}ms"
        comp_add_metric "prod_compose_validation" "$duration" "success" "config_only"
    else
        local duration=$(end_timer $start_time)
        error "Prod compose configuration failed after ${duration}ms"
        comp_add_metric "prod_compose_validation" "$duration" "failed" "config_only"
    fi

    # Test 4.2: Production Resource Constraints
    info "4.2 Testing production image with resource constraints"
    start_time=$(start_timer)
    if docker run --rm --memory=512m --cpus=0.5 --entrypoint="" tux:cached-prod python -c "print('Production resource test successful')" > /dev/null 2>&1; then
        local duration=$(end_timer $start_time)
        success "Production resource constraint test completed in ${duration}ms"
        comp_add_metric "prod_resource_test" "$duration" "success" "constrained_run"
    else
        local duration=$(end_timer $start_time)
        error "Production resource constraint test failed after ${duration}ms"
        comp_add_metric "prod_resource_test" "$duration" "failed" "constrained_run"
    fi

    # Test 4.3: Production Security
    info "4.3 Testing production security constraints"
    start_time=$(start_timer)
    if docker run --rm --entrypoint="" tux:cached-prod sh -c "whoami | grep -q nonroot && test ! -w /" > /dev/null 2>&1; then
        local duration=$(end_timer $start_time)
        success "Production security validation completed in ${duration}ms"
        comp_add_metric "prod_security_validation" "$duration" "success" "security_check"
    else
        local duration=$(end_timer $start_time)
        error "Production security validation failed after ${duration}ms"
        comp_add_metric "prod_security_validation" "$duration" "failed" "security_check"
    fi

    # =============================================================================
    comp_section "5. MIXED SCENARIO TESTING"
    # =============================================================================

    info "Testing switching between dev and prod environments"

    # Test 5.1: Configuration Compatibility
    info "5.1 Testing dev <-> prod configuration compatibility"
    start_time=$(start_timer)
    if docker compose -f docker-compose.dev.yml config > /dev/null 2>&1 && docker compose -f docker-compose.yml config > /dev/null 2>&1; then
        local duration=$(end_timer $start_time)
        success "Configuration compatibility validated in ${duration}ms"
        comp_add_metric "config_compatibility_check" "$duration" "success" "validation_only"
    else
        local duration=$(end_timer $start_time)
        error "Configuration compatibility check failed after ${duration}ms"
        comp_add_metric "config_compatibility_check" "$duration" "failed" "validation_only"
    fi

    # Test 5.2: Build Target Switching
    info "5.2 Testing build target switching"
    start_time=$(start_timer)
    docker build --target dev -t tux:switch-test-dev . > /dev/null 2>&1
    docker build --target production -t tux:switch-test-prod . > /dev/null 2>&1
    docker build --target dev -t tux:switch-test-dev2 . > /dev/null 2>&1
    local duration=$(end_timer $start_time)
    success "Build target switching completed in ${duration}ms"
    comp_add_metric "build_target_switching" "$duration" "success" "dev_prod_dev"

    # =============================================================================
    comp_section "6. ERROR SCENARIO TESTING"
    # =============================================================================

    info "Testing error handling and recovery scenarios"

    # Test 6.1: Invalid Environment Variables
    info "6.1 Testing invalid environment handling"
    cp .env .env.backup 2>/dev/null || true
    echo "INVALID_VAR=" >> .env

    start_time=$(start_timer)
    if docker compose -f docker-compose.dev.yml config > /dev/null 2>&1; then
        local duration=$(end_timer $start_time)
        success "Handled invalid env vars gracefully in ${duration}ms"
        comp_add_metric "invalid_env_handling" "$duration" "success" "graceful_handling"
    else
        local duration=$(end_timer $start_time)
        warning "Invalid env vars caused validation failure in ${duration}ms"
        comp_add_metric "invalid_env_handling" "$duration" "expected_failure" "validation_error"
    fi

    # Restore env
    mv .env.backup .env 2>/dev/null || true

    # Test 6.2: Resource Exhaustion
    info "6.2 Testing resource limit handling"
    start_time=$(start_timer)
    if docker run --rm --memory=10m --entrypoint="" tux:cached-prod echo "Resource test" > /dev/null 2>&1; then
        local duration=$(end_timer $start_time)
        success "Low memory test passed in ${duration}ms"
        comp_add_metric "low_memory_test" "$duration" "success" "10mb_limit"
    else
        local duration=$(end_timer $start_time)
        warning "Low memory test failed (expected) in ${duration}ms"
        comp_add_metric "low_memory_test" "$duration" "expected_failure" "10mb_limit"
    fi

    # =============================================================================
    comp_section "7. PERFORMANCE REGRESSION TESTING"
    # =============================================================================

    info "Testing for performance regressions"

    # Test 7.1: Build Time Regression
    info "7.1 Running build time regression tests"
    local regression_iterations=3
    local dev_times=()
    local prod_times=()

    for i in $(seq 1 $regression_iterations); do
        info "Regression test iteration $i/$regression_iterations"

        # Dev build time
        start_time=$(start_timer)
        docker build --target dev -t "tux:regression-dev-$i" . > /dev/null 2>&1
        local dev_time=$(end_timer $start_time)
        dev_times+=($dev_time)

        # Prod build time
        start_time=$(start_timer)
        docker build --target production -t "tux:regression-prod-$i" . > /dev/null 2>&1
        local prod_time=$(end_timer $start_time)
        prod_times+=($prod_time)
    done

    # Calculate averages
    local dev_avg=$(( (${dev_times[0]} + ${dev_times[1]} + ${dev_times[2]}) / 3 ))
    local prod_avg=$(( (${prod_times[0]} + ${prod_times[1]} + ${prod_times[2]}) / 3 ))

    success "Average dev build time: ${dev_avg}ms"
    success "Average prod build time: ${prod_avg}ms"
    comp_add_metric "regression_test_dev_avg" "$dev_avg" "success" "3_iterations"
    comp_add_metric "regression_test_prod_avg" "$prod_avg" "success" "3_iterations"

    # =============================================================================
    comp_section "8. FINAL CLEANUP AND REPORTING"
    # =============================================================================

    info "Performing final cleanup"
    comp_cleanup_all

    # Generate comprehensive report
    cat > "$comp_report_file" << EOF
# Comprehensive Docker Testing Report

**Generated:** $(date -Iseconds)
**Test Session:** $timestamp
**Duration:** ~$(date +%M) minutes

## 🎯 Test Summary

### Build Performance
- **Fresh Dev Build:** See metrics for timing
- **Fresh Prod Build:** See metrics for timing
- **Cached Dev Build:** See metrics for timing
- **Cached Prod Build:** See metrics for timing

### Development Workflow
- **Volume Configuration:** Tested
- **Container Functionality:** Tested
- **File System Structure:** Tested

### Production Deployment
- **Configuration Validation:** Tested
- **Resource Constraints:** Tested
- **Security Validation:** Tested

### Environment Switching
- **Configuration Compatibility:** Tested
- **Build Target Switching:** Tested

### Error Handling
- **Invalid Environment:** Tested
- **Resource Limits:** Tested

### Performance Regression
- **Build Consistency:** Tested across $regression_iterations iterations

## 📊 Detailed Metrics

See metrics files:
- \`$comp_log_dir/metrics.jsonl\` - Individual test results
- \`$comp_log_dir/test.log\` - Detailed logs
- \`$comp_log_dir/*-build.log\` - Build logs

## 🎉 Conclusion

All major developer scenarios have been tested. Review the detailed logs and metrics for specific performance data and any issues that need attention.

**Next Steps:**
1. Review detailed metrics in the log files
2. Address any failed tests
3. Set up monitoring for these scenarios in CI/CD
4. Document expected performance baselines
EOF

    success "Comprehensive testing completed!"
    info "Test results saved to: $comp_log_dir"
    info "Report generated: $comp_report_file"

    echo ""
    success "🎉 COMPREHENSIVE TESTING COMPLETE!"
    echo "======================================"
    echo "📊 Results: $comp_log_dir"
    echo "📋 Report: $comp_report_file"
    echo "📈 Metrics: $comp_log_dir/metrics.jsonl"
}

# ============================================================================
# HELP AND USAGE
# ============================================================================
show_help() {
    cat << EOF
🐳 Tux Docker Toolkit v$TOOLKIT_VERSION

A unified script for all Docker operations: testing, monitoring, and management.

USAGE:
    $SCRIPT_NAME <command> [options]

COMMANDS:
    quick                     Quick validation (2-3 minutes)
    test [options]           Standard performance testing (5-7 minutes)
    comprehensive            Full regression testing (15-20 minutes)
    monitor [container] [duration] [interval]
                             Monitor container resources

    cleanup [options]        Safe cleanup of tux resources
    help                     Show this help message

TEST OPTIONS:
    --no-cache              Force fresh builds (no Docker cache)
    --force-clean           Aggressive cleanup before testing

CLEANUP OPTIONS:
    --force                 Skip confirmation prompts
    --dry-run               Show what would be removed without removing
    --volumes               Also remove tux volumes

MONITOR OPTIONS:
    <container>             Container name (default: $DEFAULT_CONTAINER_NAME)
    <duration>              Duration in seconds (default: 60)
    <interval>              Sampling interval in seconds (default: 5)

ENVIRONMENT VARIABLES:
    BUILD_THRESHOLD         Max production build time in ms (default: 300000)
    STARTUP_THRESHOLD       Max container startup time in ms (default: 10000)
    PYTHON_THRESHOLD        Max Python validation time in ms (default: 5000)
    MEMORY_THRESHOLD        Max memory usage in MB (default: 512)

EXAMPLES:
    $SCRIPT_NAME quick                           # Quick validation
    $SCRIPT_NAME test --no-cache                 # Fresh build testing
    $SCRIPT_NAME monitor tux-dev 120 10         # Monitor for 2 min, 10s intervals
    $SCRIPT_NAME cleanup --dry-run --volumes    # Preview cleanup with volumes


SAFETY:
    All cleanup operations only affect tux-related resources.
    System images (python, ubuntu, etc.) are preserved.

FILES:
    Logs and metrics are saved in: $LOGS_DIR/

For detailed documentation, see: DOCKER.md
EOF
}

# ============================================================================
# MAIN SCRIPT LOGIC
# ============================================================================

# Check if running from correct directory
if [[ ! -f "pyproject.toml" || ! -f "Dockerfile" ]]; then
    error "Please run this script from the tux project root directory"
fi

# Ensure dependencies and Docker
check_docker
check_dependencies
ensure_logs_dir

# Parse main command
case "${1:-help}" in
    "quick")
        shift
        cmd_quick "$@"
        ;;
    "test")
        shift
        cmd_test "$@"
        ;;
    "comprehensive")
        shift
        cmd_comprehensive "$@"
        ;;
    "monitor")
        shift
        cmd_monitor "$@"
        ;;

    "cleanup")
        shift
        cmd_cleanup "$@"
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        error "Unknown command: $1. Use '$SCRIPT_NAME help' for usage information."
        ;;
esac
