# Comprehensive Docker Testing Strategy

## 🧪 **Testing All Developer Scenarios & Workflows**

This document outlines a complete testing matrix covering every possible developer experience scenario to ensure robust Docker functionality across all use cases.

## 🎯 **Quick Run - All Scenarios**

```bash
# Run the comprehensive test suite
chmod +x scripts/comprehensive-docker-test.sh
./scripts/comprehensive-docker-test.sh

# View detailed results
cat logs/comprehensive-test-*/test-report.md
```

## 📋 **Complete Test Matrix**

### 1. **🚀 Clean Slate Testing (Zero State)**

**Scenario:** Developer starting from absolute zero - no images, no cache, no containers.

```bash
# Manual testing (SAFE: only tux resources)
poetry run tux docker cleanup --force --volumes
docker builder prune -f

# Fresh development build
time docker build --no-cache --target dev -t tux:fresh-dev .

# Fresh production build  
time docker build --no-cache --target production -t tux:fresh-prod .

# Verify non-root execution
docker run --rm tux:fresh-prod whoami  # Should output: nonroot

# Verify read-only filesystem
docker run --rm tux:fresh-prod touch /test-file 2>&1 || echo "✅ Read-only working"
```

**Expected Results:**

- Dev build: < 5 minutes (worst case)
- Prod build: < 5 minutes (worst case)
- All security constraints working
- No permission errors

### 2. **⚡ Cached Build Testing**

**Scenario:** Developer with existing builds, testing incremental changes.

```bash
# Should reuse layers from previous builds
time docker build --target dev -t tux:cached-dev .
time docker build --target production -t tux:cached-prod .

# Test cache efficiency
docker history tux:cached-dev | grep -c "CACHED"
```

**Expected Results:**

- Dev build: < 30 seconds
- Prod build: < 60 seconds
- High cache hit ratio (>80%)

### 3. **💻 Development Workflow Testing**

**Scenario:** Active development with file watching, hot reload, and iterative changes.

#### 3.1 **File Watching & Sync Performance**

```bash
# Start development environment
poetry run tux --dev docker up -d

# Test file sync speed
echo "# Test change $(date)" > test_file.py
time docker compose -f docker-compose.dev.yml exec -T tux test -f /app/test_file.py

# Test directory sync
mkdir test_dir && echo "test" > test_dir/file.txt
sleep 2
docker compose -f docker-compose.dev.yml exec -T tux test -f /app/test_dir/file.txt

# Cleanup
rm -rf test_file.py test_dir
```

**Expected Results:**

- File sync: < 2 seconds
- Directory sync: < 5 seconds
- No sync failures

#### 3.2 **Hot Reload Testing**

```bash
# Monitor container logs
docker compose -f docker-compose.dev.yml logs -f &
LOG_PID=$!

# Make code change
echo "# Hot reload test $(date)" >> tux/bot.py

# Wait for reload detection
sleep 5
kill $LOG_PID

# Revert change
git checkout -- tux/bot.py
```

**Expected Results:**

- Change detection: < 3 seconds
- Container restart: < 10 seconds
- No data loss

#### 3.3 **Schema Change Rebuild**

```bash
# Make schema change (triggers rebuild)
echo "  // Test comment $(date)" >> prisma/schema/main.prisma

# Monitor for rebuild trigger
docker compose -f docker-compose.dev.yml logs --tail 50

# Revert change
git checkout -- prisma/schema/main.prisma
```

**Expected Results:**

- Rebuild triggered automatically
- Prisma client regenerated
- Container restarted successfully

#### 3.4 **Dependency Change Testing**

```bash
# Simulate dependency change
touch pyproject.toml

# Should trigger full rebuild
docker compose -f docker-compose.dev.yml logs --tail 50
```

**Expected Results:**

- Full rebuild triggered
- New dependencies installed
- Container fully restarted

### 4. **🏭 Production Workflow Testing**

**Scenario:** Production deployment and monitoring scenarios.

#### 4.1 **Production Startup & Health**

```bash
# Start production environment
poetry run tux docker up -d

# Monitor startup
docker compose -f docker-compose.yml logs -f &
LOG_PID=$!

# Wait for health check
for i in {1..12}; do
    if docker compose -f docker-compose.yml ps | grep -q "healthy"; then
        echo "✅ Health check passed at iteration $i"
        break
    fi
    sleep 5
done

kill $LOG_PID
```

**Expected Results:**

- Startup time: < 10 seconds
- Health check passes within 60 seconds
- No errors in logs

#### 4.2 **Resource Constraint Testing**

```bash
# Monitor resource usage
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" tux

# Test memory limits
docker compose -f docker-compose.yml exec tux python -c "
import sys
print(f'Memory limit test: {sys.getsizeof(list(range(100000)))} bytes')
"
```

**Expected Results:**

- Memory usage < 512MB
- CPU usage < 50% at idle
- Constraints respected

#### 4.3 **Production Security Testing**

```bash
# Verify security constraints
docker compose -f docker-compose.yml exec tux whoami  # Should be: nonroot
docker compose -f docker-compose.yml exec tux id      # UID should be 1001

# Test read-only filesystem
docker compose -f docker-compose.yml exec tux touch /test-file 2>&1 || echo "✅ Read-only working"

# Test writable temp
docker compose -f docker-compose.yml exec tux touch /app/temp/test-file && echo "✅ Temp writable"
```

**Expected Results:**

- Non-root execution enforced
- Read-only filesystem working
- Temp directories writable

### 5. **🔄 Mixed Scenario Testing**

**Scenario:** Switching between environments and configurations.

#### 5.1 **Environment Switching**

```bash
# Start dev environment
poetry run tux --dev docker up -d
sleep 10

# Switch to production
poetry run tux --dev docker down
poetry run tux docker up -d
sleep 10

# Switch back to dev
poetry run tux docker down
poetry run tux --dev docker up -d

# Cleanup
poetry run tux --dev docker down
```

**Expected Results:**

- Clean switches with no conflicts
- Port conflicts avoided
- Volume data preserved where appropriate

#### 5.2 **Build Target Switching**

```bash
# Rapid target switching
docker build --target dev -t tux:switch-dev .
docker build --target production -t tux:switch-prod .
docker build --target dev -t tux:switch-dev2 .

# Verify both work
docker run --rm tux:switch-dev python --version
docker run --rm tux:switch-prod python --version
```

**Expected Results:**

- Fast switching via cache
- Both targets functional
- No build conflicts

### 6. **❌ Error Scenario Testing**

**Scenario:** Testing graceful failure and recovery.

#### 6.1 **Invalid Configuration**

```bash
# Test invalid .env
cp .env .env.backup
echo "INVALID_VAR=" >> .env

# Should handle gracefully
docker compose -f docker-compose.dev.yml config || echo "✅ Invalid config detected"

# Restore
mv .env.backup .env
```

#### 6.2 **Resource Exhaustion**

```bash
# Test very low memory limit
docker run --rm --memory=10m tux:cached-prod echo "Low memory test" 2>&1 || echo "✅ Low memory handled"

# Test disk space (if safe)
# dd if=/dev/zero of=/tmp/test-disk-full bs=1M count=1000
```

#### 6.3 **Network Issues**

```bash
# Test with limited network (if applicable)
docker run --rm --network=none tux:cached-prod python -c "print('Network isolation test')"
```

#### 6.4 **Permission Recovery**

```bash
# Test permission issues
docker run --rm --user root tux:cached-prod whoami || echo "✅ Root access blocked"
```

### 7. **📊 Performance Regression Testing**

**Scenario:** Ensuring performance doesn't degrade over time.

#### 7.1 **Build Time Consistency**

```bash
# Run multiple builds and compare
for i in {1..3}; do
    echo "Build iteration $i"
    time docker build --target production -t "tux:perf-test-$i" . 2>&1 | grep real
done
```

#### 7.2 **Memory Usage Trending**

```bash
# Monitor memory over time
for i in {1..10}; do
    CONTAINER_ID=$(docker run -d tux:cached-prod sleep 30)
    sleep 2
    docker stats --no-stream "$CONTAINER_ID"
    docker stop "$CONTAINER_ID"
done
```

#### 7.3 **Startup Time Regression**

```bash
# Test startup consistency
for i in {1..5}; do
    echo "Startup test $i"
    time docker run --rm tux:cached-prod echo "Startup test complete"
done
```

### 8. **🔧 Advanced Scenarios**

#### 8.1 **Multi-platform Testing**

```bash
# Test if buildx is available
if docker buildx version &> /dev/null; then
    docker buildx build --platform linux/amd64,linux/arm64 --target production .
fi
```

#### 8.2 **Security Scanning Integration**

```bash
# Test security scanning
if command -v docker scout &> /dev/null; then
    docker scout cves tux:cached-prod --only-severity critical,high
fi
```

#### 8.3 **Volume Persistence Testing**

```bash
# Test volume data persistence
poetry run tux --dev docker up -d
docker compose -f docker-compose.dev.yml exec tux touch /app/temp/persistent-test.txt

# Restart container
poetry run tux --dev docker restart

# Check if file persists
docker compose -f docker-compose.dev.yml exec tux test -f /app/temp/persistent-test.txt && echo "✅ Volume persistence working"

poetry run tux --dev docker down
```

## 🎯 **Scenario-Based Test Suites**

### **Quick Developer Validation**

```bash
# 5-minute validation for daily development
./scripts/test-docker.sh

# Should cover:
# - Basic build functionality
# - Development environment
# - File watching
# - Basic performance
```

### **Pre-Commit Testing**

```bash
# Before committing Docker changes
docker build --target dev .
docker build --target production .
docker compose -f docker-compose.dev.yml config
docker compose -f docker-compose.yml config
```

### **CI/CD Pipeline Testing**

```bash
# Full regression testing for CI
./scripts/comprehensive-docker-test.sh

# Additional CI-specific tests
docker buildx build --platform linux/amd64,linux/arm64 .
docker scout cves --exit-code --only-severity critical,high
```

### **Production Deployment Testing**

```bash
# Before production deployment
docker build --target production -t tux:prod-candidate .
docker run --rm --env-file .env.prod tux:prod-candidate --help
docker run -d --name prod-test --env-file .env.prod tux:prod-candidate
sleep 30
docker logs prod-test
docker stop prod-test
docker rm prod-test
```

## 📈 **Performance Baselines**

### **Expected Performance Targets**

| Scenario | Expected Time | Threshold |
|----------|---------------|-----------|
| Fresh dev build | < 300s | ❌ if > 600s |
| Fresh prod build | < 300s | ❌ if > 600s |
| Cached dev build | < 30s | ❌ if > 60s |
| Cached prod build | < 60s | ❌ if > 120s |
| File sync | < 2s | ❌ if > 5s |
| Container startup | < 10s | ❌ if > 30s |
| Health check | < 60s | ❌ if > 120s |
| Hot reload | < 10s | ❌ if > 30s |

### **Resource Limits**

| Environment | Memory | CPU | Disk |
|-------------|--------|-----|------|
| Development | < 1GB | < 1.0 | < 5GB |
| Production | < 512MB | < 0.5 | < 2GB |

## 🚨 **Failure Scenarios to Test**

1. **Out of disk space during build**
2. **Network timeout during dependency installation**
3. **Invalid Dockerfile syntax**
4. **Missing environment variables**
5. **Port conflicts**
6. **Permission denied errors**
7. **Resource limit exceeded**
8. **Corrupted cache**
9. **Invalid compose configuration**
10. **Missing base image**

## 🔄 **Automated Testing Integration**

### **Pre-commit Hook**

```bash
#!/bin/bash
# .git/hooks/pre-commit
if git diff --cached --name-only | grep -E "(Dockerfile|docker-compose.*\.yml|\.dockerignore)"; then
    echo "Docker files changed, running validation..."
    ./scripts/test-docker.sh --quick
fi
```

### **GitHub Actions Matrix**

```yaml
strategy:
  matrix:
    scenario: [
      "fresh-build",
      "cached-build", 
      "dev-workflow",
      "prod-deployment",
      "security-scan"
    ]
```

## 📊 **Metrics Collection**

The comprehensive test script automatically collects:

- **Build times** (fresh vs cached)
- **Container startup times**
- **File sync performance**
- **Memory usage patterns**
- **Resource constraint compliance**
- **Security scan results**
- **Error rates and recovery times**

All metrics are saved in JSON format for trend analysis and regression detection.

## 🎉 **Success Criteria**

✅ **All scenarios pass without errors**
✅ **Performance within expected thresholds**
✅ **Security constraints enforced**
✅ **Resource limits respected**
✅ **Developer workflow smooth**
✅ **Production deployment reliable**

Run the comprehensive test suite regularly to ensure your Docker setup remains robust across all developer scenarios! 🚀
