# Docker Setup Testing Guide

This guide provides comprehensive tests to validate all Docker improvements with detailed performance metrics and monitoring.

## 🚀 **Quick Validation Checklist**

- [ ] Development container builds successfully
- [ ] Production container builds successfully
- [ ] File watching works for code changes
- [ ] Schema changes trigger rebuilds
- [ ] Temp file writing works (for eval scripts)
- [ ] Health checks pass
- [ ] Security scanning works
- [ ] Non-root user execution

## 🚀 **Quick Performance Test**

```bash
# Run automated performance test (includes timing, sizes, metrics)
./scripts/test-docker.sh

# View results
cat logs/docker-test-*.log          # Detailed logs
cat logs/docker-metrics-*.json     # JSON metrics data
```

## 📋 **Detailed Testing Steps**

### 1. **Environment Setup**

```bash
# Ensure you have the required files
ls -la .env                    # Should exist
ls -la pyproject.toml         # Should exist
ls -la prisma/schema/         # Should contain your schema files

# Clean up any existing containers/images
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.yml down -v
docker system prune -f
```

### 2. **Development Environment Testing**

#### 2.1 **Initial Build Test**

```bash
# Build and start development environment
poetry run tux --dev docker build
poetry run tux --dev docker up

# Expected: Container builds without errors
# Expected: Bot starts successfully
# Expected: Prisma client generates on startup
```

#### 2.2 **File Watching Test**

```bash
# In another terminal, make a simple code change
echo "# Test comment" >> tux/bot.py

# Expected: File syncs immediately (no rebuild)
# Expected: Bot restarts with hot reload
```

#### 2.3 **Schema Change Test**

```bash
# Make a minor schema change
echo "  // Test comment" >> prisma/schema/main.prisma

# Expected: Container rebuilds automatically
# Expected: Prisma client regenerates
# Expected: Bot restarts with new schema
```

#### 2.4 **Dependency Change Test**

```bash
# Touch a dependency file
touch pyproject.toml

# Expected: Container rebuilds
# Expected: Dependencies reinstall if needed
```

#### 2.5 **Temp File Writing Test**

```bash
# Test temp file creation (for eval scripts)
poetry run tux --dev docker exec app python -c "
import os
import tempfile

# Test persistent temp directory
temp_dir = '/app/temp'
test_file = os.path.join(temp_dir, 'test.py')
with open(test_file, 'w') as f:
    f.write('print(\"Hello from temp file\")')

# Test execution
exec(open(test_file).read())

# Test system temp
with tempfile.NamedTemporaryFile(dir='/tmp', suffix='.py', delete=False) as tmp:
    tmp.write(b'print(\"Hello from system temp\")')
    tmp.flush()
    exec(open(tmp.name).read())

print('✅ Temp file tests passed')
"

# Expected: No permission errors
# Expected: Files created successfully
# Expected: Execution works
```

### 3. **Production Environment Testing**

#### 3.1 **Production Build Test**

```bash
# Build production image
docker build --target production -t tux:prod-test .

# Expected: Build completes without errors
# Expected: Image size is reasonable (check with docker images)
```

#### 3.2 **Production Container Test**

```bash
# Start production container
docker run --rm --env-file .env tux:prod-test --help

# Expected: Container starts as non-root user
# Expected: Help command works
# Expected: No permission errors
```

#### 3.3 **Security Test**

```bash
# Check user execution
docker run --rm tux:prod-test whoami
# Expected: Output should be "nonroot" or similar

# Check read-only filesystem
docker run --rm tux:prod-test touch /test-file 2>&1 || echo "✅ Read-only filesystem working"
# Expected: Should fail (read-only filesystem)

# Check writable temp
docker run --rm tux:prod-test touch /app/temp/test-file && echo "✅ Temp directory writable"
# Expected: Should succeed
```

### 4. **CI/CD Pipeline Testing**

#### 4.1 **Local Multi-Platform Build**

```bash
# Test multi-platform build (if buildx available)
docker buildx build --platform linux/amd64,linux/arm64 --target production .

# Expected: Builds for both platforms
# Expected: No platform-specific errors
```

#### 4.2 **Security Scanning Test**

```bash
# Install Docker Scout if not available
docker scout --help

# Run vulnerability scan
docker scout cves tux:prod-test

# Expected: Scan completes
# Expected: Vulnerability report generated
# Note: Some vulnerabilities are expected, focus on critical/high
```

#### 4.3 **SBOM Generation Test**

```bash
# Build with SBOM and provenance
docker buildx build \
  --target production \
  --provenance=true \
  --sbom=true \
  -t tux:test-attestations .

# Expected: Build succeeds with attestations
# Expected: No attestation errors
```

### 5. **Performance & Resource Testing**

#### 5.1 **Resource Limits Test**

```bash
# Start with resource monitoring
poetry run tux --dev docker up

# Check resource usage
docker stats tux-dev

# Expected: Memory usage within 1GB limit
# Expected: CPU usage reasonable
```

#### 5.2 **Health Check Test**

```bash
# Start production container
docker compose -f docker-compose.yml up -d

# Wait for startup
sleep 45

# Check health status
docker compose -f docker-compose.yml ps

# Expected: Status should be "healthy"
# Expected: Health check passes
```

### 6. **Database Integration Testing**

#### 6.1 **Prisma Generation Test**

```bash
# Test Prisma client generation
poetry run tux --dev docker exec app poetry run prisma generate

# Expected: Client generates successfully
# Expected: No binary or path errors
```

#### 6.2 **Database Commands Test**

```bash
# Test database operations (if DB is configured)
poetry run tux --dev docker exec app poetry run prisma db push --accept-data-loss

# Expected: Schema pushes successfully
# Expected: No connection errors
```

## 🐛 **Troubleshooting Common Issues**

### Build Failures

```bash
# Clean build cache
docker builder prune -f

# Rebuild without cache
docker build --no-cache --target dev -t tux:dev .
```

### Permission Issues

```bash
# Check container user
docker run --rm tux:dev whoami

# Check file permissions
docker run --rm tux:dev ls -la /app
```

### Prisma Issues

```bash
# Regenerate Prisma client
poetry run tux --dev docker exec app poetry run prisma generate

# Check Prisma binaries
poetry run tux --dev docker exec app ls -la .venv/lib/python*/site-packages/prisma
```

### File Watching Issues

```bash
# Check if files are syncing
docker compose -f docker-compose.dev.yml logs -f

# Restart with rebuild
poetry run tux --dev docker up --build
```

## ✅ **Success Criteria**

All tests should pass with:

- ✅ No permission errors
- ✅ Non-root user execution
- ✅ File watching works correctly
- ✅ Schema changes trigger rebuilds
- ✅ Temp files can be created and executed
- ✅ Health checks pass
- ✅ Resource limits respected
- ✅ Security scans complete
- ✅ Multi-platform builds work

## 📊 **Performance Benchmarks**

Document these metrics:

- Development build time: `< 2 minutes`
- Production build time: `< 3 minutes`
- Schema rebuild time: `< 1 minute`
- Container startup time: `< 30 seconds`
- Memory usage: `< 512MB (prod), < 1GB (dev)`

## 🔄 **Automated Testing**

Consider adding these to your CI:

```yaml
# Add to .github/workflows/docker-test.yml
- name: Test development build
  run: docker build --target dev .

- name: Test production build  
  run: docker build --target production .

- name: Test security scan
  run: docker scout cves --exit-code --only-severity critical,high
```

Run these tests whenever you make Docker-related changes to ensure reliability!

## 📊 **Performance Monitoring Setup**

### Prerequisites

```bash
# Install jq for JSON metrics (optional but recommended)
sudo apt-get install jq -y  # Ubuntu/Debian
brew install jq             # macOS

# Create monitoring directory
mkdir -p logs performance-history
```

### Continuous Monitoring

```bash
# Run performance tests regularly and track trends
./scripts/test-docker.sh
cp logs/docker-metrics-*.json performance-history/

# Compare performance over time
./scripts/compare-performance.sh  # (See below)
```

## 📋 **Detailed Testing with Metrics**

### 1. **Build Performance Testing**

#### 1.1 **Timed Build Tests**

```bash
# Development build with detailed timing
time docker build --target dev -t tux:perf-test-dev . 2>&1 | tee build-dev.log

# Production build with detailed timing  
time docker build --target production -t tux:perf-test-prod . 2>&1 | tee build-prod.log

# No-cache build test (worst case)
time docker build --no-cache --target production -t tux:perf-test-prod-nocache . 2>&1 | tee build-nocache.log

# Analyze build logs
grep "Step" build-*.log | grep -o "Step [0-9]*/[0-9]*" | sort | uniq -c
```

#### 1.2 **Image Size Analysis**

```bash
# Compare image sizes
docker images | grep tux | awk '{print $1":"$2, $7$8}' | sort

# Layer analysis
docker history tux:perf-test-prod --human --format "table {{.CreatedBy}}\t{{.Size}}"

# Export size data
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" > image-sizes.log
```

#### 1.3 **Build Cache Efficiency**

```bash
# Test cache hit rates
echo "# Cache test" >> Dockerfile
time docker build --target production -t tux:cache-test . | tee cache-test.log

# Count cache hits vs rebuilds
grep -c "CACHED" cache-test.log
grep -c "RUN" cache-test.log
```

### 2. **Runtime Performance Testing**

#### 2.1 **Container Startup Benchmarks**

```bash
# Multiple startup tests for average
for i in {1..5}; do
    echo "Test run $i:"
    time docker run --rm tux:perf-test-prod echo "Startup test $i"
done | tee startup-benchmarks.log

# Analyze startup times
grep "real" startup-benchmarks.log | awk '{sum+=$2} END {print "Average:", sum/NR}'
```

#### 2.2 **Memory Usage Monitoring**

```bash
# Start container and monitor memory
CONTAINER_ID=$(docker run -d --name memory-test tux:perf-test-prod sleep 60)

# Monitor memory usage over time
for i in {1..12}; do
    docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}" memory-test
    sleep 5
done | tee memory-usage.log

docker stop memory-test
docker rm memory-test

# Generate memory report
awk 'NR>1 {print $2}' memory-usage.log | sed 's/MiB//' | awk '{sum+=$1; count++} END {print "Average memory:", sum/count, "MiB"}'
```

#### 2.3 **Resource Limits Testing**

```bash
# Test with resource constraints
docker run --rm \
    --memory=256m \
    --cpus=0.5 \
    --name resource-test \
    tux:perf-test-prod python -c "
import sys
import time
import psutil

print(f'Memory limit: {psutil.virtual_memory().total / 1024 / 1024:.1f} MB')
print(f'CPU count: {psutil.cpu_count()}')

# Memory stress test
data = []
for i in range(100):
    data.append('x' * 1024 * 1024)  # 1MB chunks
    if i % 10 == 0:
        print(f'Allocated: {(i+1)} MB')
        time.sleep(0.1)
"
```

### 3. **File System Performance**

#### 3.1 **Temp Directory Benchmarks**

```bash
# Test temp file performance
docker run --rm tux:perf-test-prod sh -c "
    echo 'Testing temp directory performance...'
    
    # Write test
    time for i in \$(seq 1 1000); do
        echo 'test data \$i' > /app/temp/test_\$i.txt
    done
    
    # Read test  
    time for i in \$(seq 1 1000); do
        cat /app/temp/test_\$i.txt > /dev/null
    done
    
    # Cleanup test
    time rm /app/temp/test_*.txt
"
```

#### 3.2 **File Watching Performance**

```bash
# Start development environment
poetry run tux --dev docker up -d

# Test file sync performance
for i in {1..10}; do
    echo "# Test change $i $(date)" >> test_file.py
    sleep 2
    docker logs tux-dev --tail 5 | grep -q "Detected change" && echo "Change $i detected"
done

# Cleanup
rm test_file.py
poetry run tux --dev docker down
```

### 4. **Database Performance**

#### 4.1 **Prisma Generation Benchmarks**

```bash
# Multiple Prisma generation tests
for i in {1..3}; do
    echo "Prisma test run $i:"
    time docker run --rm tux:perf-test-dev sh -c "poetry run prisma generate"
done | tee prisma-benchmarks.log

# Average generation time
grep "real" prisma-benchmarks.log | awk -F 'm|s' '{sum+=$1*60+$2} END {print "Average:", sum/NR, "seconds"}'
```

#### 4.2 **Database Connection Testing**

```bash
# Test database operations (if DB configured)
docker run --rm --env-file .env tux:perf-test-dev sh -c "
    echo 'Testing database operations...'
    time poetry run prisma db push --accept-data-loss
    time poetry run python -c 'from tux.database.client import DatabaseClient; client = DatabaseClient(); print(\"DB client test:\", client.is_connected())'
"
```

### 5. **Security Performance**

#### 5.1 **Security Scan Benchmarks**

```bash
# Time security scans
if command -v docker scout &> /dev/null; then
    echo "Testing security scan performance..."
    time docker scout cves tux:perf-test-prod --only-severity critical,high | tee security-scan.log
    
    # Count vulnerabilities
    grep -c "critical" security-scan.log || echo "No critical vulnerabilities"
    grep -c "high" security-scan.log || echo "No high vulnerabilities"
fi
```

#### 5.2 **Multi-platform Build Performance**

```bash
# Test multi-platform build times
time docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --target production \
    -t tux:multiplatform-test . | tee multiplatform-build.log

# Analyze platform-specific times
grep "linux/" multiplatform-build.log
```

## 📈 **Performance Analysis Scripts**

### Performance Comparison Script

```bash
# Create comparison script
cat > scripts/compare-performance.sh << 'EOF'
#!/bin/bash

echo "📊 Performance History Analysis"
echo "=============================="

if [ ! -d "performance-history" ]; then
    echo "No performance history found. Run tests first."
    exit 1
fi

if command -v jq &> /dev/null; then
    echo "Build Performance Trend:"
    echo "======================="
    for file in performance-history/docker-metrics-*.json; do
        timestamp=$(jq -r '.timestamp' "$file")
        dev_build=$(jq -r '.performance.development_build.value // "N/A"' "$file")
        prod_build=$(jq -r '.performance.production_build.value // "N/A"' "$file")
        echo "$timestamp: Dev=${dev_build}ms, Prod=${prod_build}ms"
    done
    
    echo ""
    echo "Image Size Trend:"
    echo "================"
    for file in performance-history/docker-metrics-*.json; do
        timestamp=$(jq -r '.timestamp' "$file")
        dev_size=$(jq -r '.performance.dev_image_size_mb.value // "N/A"' "$file")
        prod_size=$(jq -r '.performance.prod_image_size_mb.value // "N/A"' "$file")
        echo "$timestamp: Dev=${dev_size}MB, Prod=${prod_size}MB"
    done
else
    echo "Install jq for detailed analysis: sudo apt-get install jq"
    ls -la performance-history/
fi
EOF

chmod +x scripts/compare-performance.sh
```

### Resource Monitoring Script

```bash
# Create resource monitoring script
cat > scripts/monitor-resources.sh << 'EOF'
#!/bin/bash

CONTAINER_NAME=${1:-"tux-dev"}
DURATION=${2:-60}

echo "🔍 Monitoring container: $CONTAINER_NAME for ${DURATION}s"
echo "======================================================="

# Check if container exists
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "Container $CONTAINER_NAME not found"
    exit 1
fi

# Monitor resources
for i in $(seq 1 $((DURATION/5))); do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    stats=$(docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}" "$CONTAINER_NAME")
    echo "$timestamp,$stats"
    sleep 5
done | tee "logs/resource-monitor-$(date +%Y%m%d-%H%M%S).csv"

echo "Resource monitoring complete"
EOF

chmod +x scripts/monitor-resources.sh
```

## 🎯 **Performance Benchmarks**

### Expected Performance Targets

| Metric | Development | Production | Notes |
|--------|-------------|------------|-------|
| **Build Time** | < 120s | < 180s | With cache hits |
| **No-cache Build** | < 300s | < 400s | Cold build |
| **Container Startup** | < 5s | < 3s | Ready to serve |
| **Image Size** | < 2GB | < 1GB | Optimized layers |
| **Memory Usage** | < 1GB | < 512MB | Runtime average |
| **Prisma Generation** | < 30s | < 20s | Client rebuild |
| **File Sync** | < 2s | N/A | Dev file watching |
| **Security Scan** | < 60s | < 60s | Scout analysis |

### Performance Alerts

```bash
# Add to your CI or monitoring
./scripts/test-docker.sh

# Check if performance regressed
if command -v jq &> /dev/null; then
    build_time=$(jq -r '.performance.production_build.value' logs/docker-metrics-*.json | tail -1)
    if [ "$build_time" -gt 180000 ]; then
        echo "⚠️ WARNING: Production build time exceeded 3 minutes ($build_time ms)"
    fi
    
    image_size=$(jq -r '.performance.prod_image_size_mb.value' logs/docker-metrics-*.json | tail -1)
    if [ "${image_size%.*}" -gt 1000 ]; then
        echo "⚠️ WARNING: Production image size exceeded 1GB (${image_size}MB)"
    fi
fi
```

## 📊 **Metrics Dashboard**

### JSON Metrics Structure

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "performance": {
    "development_build": {"value": 95420, "unit": "ms"},
    "production_build": {"value": 142350, "unit": "ms"},
    "container_startup": {"value": 2150, "unit": "ms"},
    "prisma_generation": {"value": 18600, "unit": "ms"},
    "dev_image_size_mb": {"value": 1.85, "unit": "MB"},
    "prod_image_size_mb": {"value": 0.92, "unit": "MB"},
    "memory_usage_mb": {"value": 285, "unit": "MB"},
    "temp_file_ops": {"value": 1250, "unit": "ms"},
    "security_scan": {"value": 45200, "unit": "ms"},
    "dev_layers": {"value": 24, "unit": "count"},
    "prod_layers": {"value": 18, "unit": "count"}
  },
  "summary": {
    "total_tests": 12,
    "timestamp": "2024-01-15T10:35:00Z",
    "log_file": "logs/docker-test-20240115-103000.log"
  }
}
```

### Viewing Metrics

```bash
# Pretty print latest metrics
jq '.' logs/docker-metrics-*.json | tail -n +1

# Get specific metrics
jq '.performance | to_entries[] | select(.key | contains("build")) | "\(.key): \(.value.value) \(.value.unit)"' logs/docker-metrics-*.json

# Export to CSV for analysis
jq -r '[.timestamp, .performance.production_build.value, .performance.prod_image_size_mb.value, .performance.memory_usage_mb.value] | @csv' logs/docker-metrics-*.json > performance-data.csv
```

Run these performance tests regularly to track your Docker setup's efficiency and catch any regressions early! 🚀
