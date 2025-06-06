# Docker Cleanup Safety Guide

This document outlines the safety improvements made to ensure all Docker scripts and CLI commands only affect tux-related resources and never accidentally remove system images, containers, or volumes.

## ⚠️ **Previous Safety Issues**

The following dangerous operations were present in the codebase:

### **Critical Issues Fixed:**

1. **`docker system prune -af --volumes`** - Removes ALL unused system resources
2. **`docker system prune -af`** - Removes ALL unused images, containers, and networks
3. **Overly broad patterns** like `*tux*` that could match system containers
4. **No safety confirmations** or dry-run options
5. **Aggressive CI cleanup** affecting shared runner resources

## 🛡️ **Safety Improvements Implemented**

### **1. Test Scripts Made Safe**

#### **`scripts/test-docker.sh`**

- ✅ **BEFORE:** Used `docker system prune -f` (dangerous)
- ✅ **AFTER:** Only removes specific test images (`tux:test-*`)
- ✅ Added safety checks with null checks before removal
- ✅ Explicit warnings about preserving system resources

#### **`scripts/comprehensive-docker-test.sh`**

- ✅ **BEFORE:** Used `docker system prune -af --volumes` (extremely dangerous)
- ✅ **AFTER:** Only removes specific tux test images and containers
- ✅ Added safety notices in output
- ✅ Preserves all system-wide Docker resources

### **2. CLI Commands Made Safe**

#### **`tux/cli/docker.py`**

- ✅ **BEFORE:** Patterns like `*tux*` could match system containers
- ✅ **AFTER:** Specific, explicit patterns for tux resources only
- ✅ Added safety documentation to pattern functions
- ✅ Dry-run option for cleanup command

**Safe Patterns Implemented:**

```python
# BEFORE (unsafe):
"*tux*"  # Could match system containers with "tux" in name

# AFTER (safe):
"tux-dev"           # Only development container
"tux-prod"          # Only production container  
"memory-test"       # Only test script containers
"resource-test"     # Only test script containers
```

### **3. CI/CD Pipeline Safety**

#### **`.github/workflows/docker-test.yml`**

- ✅ **BEFORE:** Used `docker system prune -af` (dangerous in shared CI)
- ✅ **AFTER:** Only removes test images created during the job
- ✅ Preserves all CI runner system resources
- ✅ Added safety confirmation messages

### **4. Documentation Safety**

#### **All Documentation Files Updated:**

- ✅ **DOCKER-TESTING.md** - Replaced unsafe cleanup commands
- ✅ **DOCKER-TESTING-SUMMARY.md** - Updated examples to use safe alternatives
- ✅ **DOCKER-TESTING-COMPREHENSIVE.md** - Removed dangerous system prune commands

## 🎯 **Safe Resource Patterns**

### **Images (Safe to Remove)**

```bash
tux:*                           # Official tux images
ghcr.io/allthingslinux/tux:*   # GitHub registry images
tux:test-*                     # Test images
tux:fresh-*                    # Comprehensive test images
tux:cached-*                   # Comprehensive test images
tux:perf-test-*               # Performance test images
```

### **Containers (Safe to Remove)**

```bash
tux                           # Main container
tux-dev                       # Development container
tux-prod                      # Production container
memory-test                   # Test script containers
resource-test                 # Test script containers
```

### **Volumes (Safe to Remove)**

```bash
tux_cache                     # Main cache volume
tux_temp                      # Main temp volume
tux_dev_cache                 # Dev cache volume
tux_dev_temp                  # Dev temp volume
```

### **Networks (Safe to Remove)**

```bash
tux_default                   # Default compose network
tux-*                         # Any tux-prefixed networks
```

## 🚨 **Never Removed (Protected)**

### **System Images**

- `python:*` - Base Python images
- `ubuntu:*` - Ubuntu base images
- `alpine:*` - Alpine base images
- `node:*` - Node.js images
- `postgres:*` - Database images
- Any other non-tux images

### **System Containers**

- Any containers not specifically created by tux
- CI/CD runner containers
- System service containers

### **System Volumes**

- Named volumes not created by tux
- System bind mounts
- CI/CD workspace volumes

## 🔧 **Safe Cleanup Commands**

### **Recommended Safe Commands:**

```bash
# Safe tux-only cleanup
poetry run tux docker cleanup --dry-run          # Preview what will be removed
poetry run tux docker cleanup --force --volumes  # Remove tux resources only

# Safe test cleanup
./scripts/test-docker.sh --force-clean          # Safe aggressive cleanup

# Safe manual cleanup
poetry run tux docker cleanup --force            # Remove tux images/containers
docker images --filter "dangling=true" -q | xargs -r docker rmi  # Remove dangling only
docker builder prune -f                          # Safe build cache cleanup
```

### **Dangerous Commands to NEVER Use:**

```bash
# ❌ NEVER USE THESE:
docker system prune -af --volumes    # Removes ALL system resources
docker system prune -af              # Removes ALL unused resources  
docker volume prune -f               # Removes ALL unused volumes
docker network prune -f              # Removes ALL unused networks
docker container prune -f            # Removes ALL stopped containers
```

## 🛠️ **Recovery Tools**

### **Recovery Script Created:**

```bash
./scripts/docker-recovery.sh
```

**What it does:**

- ✅ Checks for missing common system images
- ✅ Offers to restore missing Python/Ubuntu base images
- ✅ Validates Docker system state
- ✅ Provides recovery commands
- ✅ Never removes anything automatically

### **Manual Recovery:**

```bash
# If system images were accidentally removed:
docker pull python:3.13.2-slim       # Restore Python base
docker pull ubuntu:22.04             # Restore Ubuntu base

# Check system state:
docker system df                      # View disk usage
docker images                        # List all images
docker ps -a                         # List all containers
```

## 📋 **Safety Checklist**

### **Before Running Any Docker Cleanup:**

- [ ] ✅ Confirm you're using tux-safe commands only
- [ ] ✅ Use `--dry-run` flag when available
- [ ] ✅ Check current Docker state with `docker system df`
- [ ] ✅ Verify no important work containers are running
- [ ] ✅ Use specific tux cleanup commands instead of system-wide

### **Safe Development Workflow:**

```bash
# Daily development cleanup
poetry run tux docker cleanup --dry-run    # Preview
poetry run tux docker cleanup --force      # Execute if safe

# Performance testing
./scripts/test-docker.sh                   # Standard safe testing

# Comprehensive validation
./scripts/comprehensive-docker-test.sh     # Full safe testing

# Recovery if needed
./scripts/docker-recovery.sh              # Check and restore
```

## 🎉 **Benefits of Safety Improvements**

1. **🛡️ Protection:** System images and containers are never affected
2. **🔄 Reliability:** CI/CD pipelines won't break other jobs
3. **🚀 Efficiency:** Only removes what needs to be removed
4. **📊 Transparency:** Clear logging of what's being cleaned up
5. **🔧 Recovery:** Tools to restore accidentally removed resources
6. **📚 Documentation:** Clear guidance on safe vs unsafe commands

## 🔍 **Verification**

To verify safety improvements are working:

```bash
# Before cleanup - note system images
docker images | grep -E "(python|ubuntu|alpine)" > /tmp/before_images.txt

# Run safe cleanup
poetry run tux docker cleanup --force --volumes

# After cleanup - verify system images still present
docker images | grep -E "(python|ubuntu|alpine)" > /tmp/after_images.txt

# Compare (should be identical)
diff /tmp/before_images.txt /tmp/after_images.txt
```

**Expected result:** No differences - all system images preserved.

## 📞 **Support**

If you accidentally removed system resources:

1. **Run the recovery script:** `./scripts/docker-recovery.sh`
2. **Check the safety guide above for manual recovery**
3. **Use `docker pull` to restore specific images**
4. **Report the issue** so we can improve safety further

**Remember:** The new safe commands will NEVER remove system resources, only tux-specific ones.
