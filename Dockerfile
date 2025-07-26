# ==============================================================================
# TUX DISCORD BOT - MULTI-STAGE DOCKERFILE
# ==============================================================================
#
# This Dockerfile uses a multi-stage build approach to create optimized images
# for different use cases while maintaining consistency across environments.
#
# STAGES:
# -------
# 1. base       - Common foundation with runtime dependencies
# 2. build      - Development tools and dependency installation
# 3. dev        - Development environment with debugging tools
# 4. production - Minimal, secure runtime environment
#
# USAGE:
# ------
# Development:  docker-compose -f docker-compose.dev.yml up
# Production:   docker build --target production -t tux:latest .
# With version: docker build --build-arg VERSION=$(git describe --tags --always --dirty | sed 's/^v//') -t tux:latest .
#
# SECURITY FEATURES:
# ------------------
# - Non-root user execution (uid/gid 1001)
# - Read-only filesystem support via tmpfs mounts
# - Minimal attack surface (only required dependencies)
# - Pinned package versions for reproducibility
# - Health checks for container monitoring
#
# SIZE OPTIMIZATION:
# ------------------
# - Multi-stage builds to exclude build tools from final image
# - Aggressive cleanup of unnecessary files (~73% size reduction)
# - Efficient layer caching through strategic COPY ordering
# - Loop-based cleanup to reduce Dockerfile complexity
#
# ==============================================================================

# ==============================================================================
# BASE STAGE - Common Foundation
# ==============================================================================
# Purpose: Establishes the common base for all subsequent stages
# Contains: Python runtime, essential system dependencies, security setup
# Size Impact: ~150MB (Python slim + runtime deps)
# ==============================================================================

FROM python:3.13.5-slim@sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419 AS base

# OCI Labels for container metadata and registry compliance
# These labels provide important metadata for container registries and tools
LABEL org.opencontainers.image.source="https://github.com/allthingslinux/tux" \
      org.opencontainers.image.description="Tux - The all in one discord bot for the All Things Linux Community" \
      org.opencontainers.image.licenses="GPL-3.0" \
      org.opencontainers.image.authors="All Things Linux" \
      org.opencontainers.image.vendor="All Things Linux" \
      org.opencontainers.image.title="Tux" \
      org.opencontainers.image.documentation="https://github.com/allthingslinux/tux/blob/main/README.md"

# Create non-root user early for security best practices
# Using system user (no login shell) with fixed UID/GID for consistency
# UID/GID 1001 is commonly used for application users in containers
RUN groupadd --system --gid 1001 nonroot && \
    useradd --create-home --system --uid 1001 --gid nonroot nonroot

# Configure apt to avoid documentation and interactive prompts
ENV DEBIAN_FRONTEND=noninteractive \
    DEBCONF_NONINTERACTIVE_SEEN=true

# Configure dpkg to exclude documentation (reduces size and avoids man page issues)
RUN echo 'path-exclude /usr/share/doc/*' > /etc/dpkg/dpkg.cfg.d/01_nodoc && \
    echo 'path-include /usr/share/doc/*/copyright' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
    echo 'path-exclude /usr/share/man/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
    echo 'path-exclude /usr/share/groff/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
    echo 'path-exclude /usr/share/info/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
    echo 'path-exclude /usr/share/lintian/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
    echo 'path-exclude /usr/share/linda/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc

# Install runtime dependencies required for the application
# SECURITY: Update all packages first to get latest security patches, then install specific versions
# PERFORMANCE: Packages sorted alphabetically for better caching and maintenance
# NOTE: These are the minimal dependencies required for the bot to function
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        ffmpeg=7:5.1.6-0+deb12u1 \
        git=1:2.39.5-0+deb12u2 \
        libcairo2=1.16.0-7 \
        libgdk-pixbuf2.0-0=2.40.2-2 \
        libpango1.0-0=1.50.12+ds-1 \
        libpangocairo-1.0-0=1.50.12+ds-1 \
        shared-mime-info=2.2-1 \
    # Cleanup package manager caches to reduce layer size
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python environment optimization for containerized execution
# These settings improve performance and reduce container overhead

# PYTHONUNBUFFERED=1     : Forces stdout/stderr to be unbuffered for real-time logs
# PYTHONDONTWRITEBYTECODE=1 : Prevents .pyc file generation (reduces I/O and size)
# PIP_DISABLE_PIP_VERSION_CHECK : Prevents pip from checking for updates (faster)
# PIP_NO_CACHE_DIR=1     : Disables pip caching (reduces container size)

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=1

# ==============================================================================
# BUILD STAGE - Development Tools and Dependency Installation
# ==============================================================================
# Purpose: Installs build tools, Poetry, and application dependencies
# Contains: Compilers, headers, build tools, complete Python environment
# Size Impact: ~1.3GB (includes all build dependencies and Python packages)
# ==============================================================================

FROM base AS build

# Install build dependencies required for compiling Python packages with C extensions
# These tools are needed for packages like cryptography, pillow, etc.
# MAINTENANCE: Keep versions pinned and sorted alphabetically
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        # GCC compiler and build essentials for native extensions
        build-essential=12.9 \
        # Additional utilities required by some Python packages
        findutils=4.9.0-4 \
        # Development headers for graphics libraries
        libcairo2-dev=1.16.0-7 \
        # Foreign Function Interface library for Python extensions
        libffi-dev=3.4.4-1 \
    # Cleanup to reduce intermediate layer size
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Poetry configuration for dependency management
# These settings optimize Poetry for containerized builds

# POETRY_NO_INTERACTION=1        : Disables interactive prompts for CI/CD
# POETRY_VIRTUALENVS_CREATE=1    : Ensures virtual environment creation
# POETRY_VIRTUALENVS_IN_PROJECT=1: Creates .venv in project directory
# POETRY_CACHE_DIR=/tmp/poetry_cache: Uses temporary directory for cache
# POETRY_INSTALLER_PARALLEL=true : Enables parallel package installation

ENV POETRY_VERSION=2.1.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    POETRY_INSTALLER_PARALLEL=true

# Install Poetry using pip with BuildKit cache mount for efficiency
# Cache mount prevents re-downloading Poetry on subsequent builds
RUN --mount=type=cache,target=/root/.cache \
    pip install poetry==$POETRY_VERSION

# Set working directory for all subsequent operations
WORKDIR /app

# Set shell to bash with pipefail for proper error handling in pipes
# This must be set before any RUN commands that use pipes
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Copy dependency files first for optimal Docker layer caching
# Changes to these files will invalidate subsequent layers
# OPTIMIZATION: This pattern maximizes cache hits during development
COPY pyproject.toml poetry.lock ./

# Install Python dependencies using Poetry
# PERFORMANCE: Cache mount speeds up subsequent builds
# SECURITY: --only main excludes development dependencies from production
# NOTE: Install dependencies only first, package itself will be installed later with git context
RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    --mount=type=cache,target=/root/.cache/pip \
    poetry install --only main --no-root --no-directory

# Copy application files in order of change frequency (Docker layer optimization)
# STRATEGY: Files that change less frequently are copied first to maximize cache reuse

# 1. Configuration files (rarely change)
# These are typically static configuration that changes infrequently
COPY config/ ./config/

# 2. Database schema files (change infrequently)
# Prisma schema and migrations are relatively stable
COPY prisma/ ./prisma/

# 3. Main application code (changes more frequently)
# The core bot code is most likely to change during development
COPY tux/ ./tux/

# 4. Root level files needed for installation
# These include metadata and licensing information
COPY README.md LICENSE pyproject.toml ./

# Build arguments for version information
# These allow passing version info without requiring git history in build context
ARG VERSION=""
ARG GIT_SHA=""
ARG BUILD_DATE=""

# Generate version file using build args with fallback
# PERFORMANCE: Version is determined at build time, not runtime
# SECURITY: Git operations happen outside container, only VERSION string is passed in
RUN set -eux; \
    if [ -n "$VERSION" ]; then \
        # Use provided version from build args (preferred for all builds)
        echo "Using provided version: $VERSION"; \
        echo "$VERSION" > /app/VERSION; \
    else \
        # Fallback for builds without version info
        # NOTE: .git directory is excluded by .dockerignore for security/performance
        # Version should be passed via --build-arg VERSION=$(git describe --tags --always --dirty | sed 's/^v//')
        echo "No version provided, using fallback"; \
        echo "dev" > /app/VERSION; \
    fi; \
    echo "Building version: $(cat /app/VERSION)"

# Install the application and generate Prisma client
# COMPLEXITY: This step requires multiple operations that must be done together
RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    --mount=type=cache,target=/root/.cache \
    # Install the application package itself
    poetry install --only main

# ==============================================================================
# DEVELOPMENT STAGE - Development Environment
# ==============================================================================
# Purpose: Provides a full development environment with tools and debugging capabilities
# Contains: All build tools, development dependencies, debugging utilities
# Target: Used by docker-compose.dev.yml for local development
# Size Impact: ~1.6GB (includes development dependencies and tools)
# ==============================================================================

FROM build AS dev

WORKDIR /app

# Build argument to conditionally install additional development tools
# Allows customization for different development environments (IDE, devcontainer, etc.)
ARG DEVCONTAINER=0
ENV DEVCONTAINER=${DEVCONTAINER}

# Setup development environment in a single optimized layer
# PERFORMANCE: Single RUN command reduces layer count and build time
RUN set -eux; \
    # Conditionally install zsh for enhanced development experience
    # Only installs if DEVCONTAINER build arg is set to 1
    if [ "$DEVCONTAINER" = "1" ]; then \
        apt-get update && \
        apt-get install -y --no-install-recommends zsh=5.9-4+b6 && \
        chsh -s /usr/bin/zsh && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*; \
    fi; \
    # Create application cache and temporary directories
    # These directories are used by the bot for caching and temporary files
    mkdir -p /app/.cache/tldr /app/temp; \
    # Create user cache directories (fixes permission issues for Prisma/npm)
    mkdir -p /home/nonroot/.cache /home/nonroot/.npm; \
    # Fix ownership of all application files for non-root user
    # SECURITY: Ensures the application runs with proper permissions
    chown -R nonroot:nonroot /app /home/nonroot/.cache /home/nonroot/.npm

# Switch to non-root user for all subsequent operations
# SECURITY: Follows principle of least privilege
USER nonroot

# Install development dependencies and setup Prisma
# DEVELOPMENT: These tools are needed for linting, testing, and development workflow
RUN poetry install --only dev --no-root --no-directory && \
    poetry run prisma py fetch && \
    poetry run prisma generate

# Development container startup command
# WORKFLOW: Regenerates Prisma client and starts the bot in development mode
# This ensures the database client is always up-to-date with schema changes
CMD ["sh", "-c", "poetry run prisma generate && exec poetry run tux --dev start"]

# ==============================================================================
# PRODUCTION STAGE - Minimal Runtime Environment
# ==============================================================================
# Purpose: Creates a minimal, secure, and optimized image for production deployment
# Contains: Only runtime dependencies, application code, and essential files
# Security: Non-root execution, minimal attack surface, health monitoring
# Size Impact: ~440MB (73% reduction from development image)
# ==============================================================================

FROM python:3.13.5-slim@sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419 AS production

# Duplicate OCI labels for production image metadata
# COMPLIANCE: Ensures production images have proper metadata for registries
LABEL org.opencontainers.image.source="https://github.com/allthingslinux/tux" \
      org.opencontainers.image.description="Tux - The all in one discord bot for the All Things Linux Community" \
      org.opencontainers.image.licenses="GPL-3.0" \
      org.opencontainers.image.authors="All Things Linux" \
      org.opencontainers.image.vendor="All Things Linux" \
      org.opencontainers.image.title="Tux" \
      org.opencontainers.image.documentation="https://github.com/allthingslinux/tux/blob/main/README.md"

# Create non-root user (same as base stage)
# SECURITY: Consistent user across all stages for permission compatibility
RUN groupadd --system --gid 1001 nonroot && \
    useradd --create-home --system --uid 1001 --gid nonroot nonroot

# Configure apt for production (same as base stage)
ENV DEBIAN_FRONTEND=noninteractive \
    DEBCONF_NONINTERACTIVE_SEEN=true

# Configure dpkg to exclude documentation (reduces size and avoids man page issues)
RUN echo 'path-exclude /usr/share/doc/*' > /etc/dpkg/dpkg.cfg.d/01_nodoc && \
    echo 'path-include /usr/share/doc/*/copyright' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
    echo 'path-exclude /usr/share/man/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
    echo 'path-exclude /usr/share/groff/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
    echo 'path-exclude /usr/share/info/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
    echo 'path-exclude /usr/share/lintian/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
    echo 'path-exclude /usr/share/linda/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc

# Install ONLY runtime dependencies (minimal subset of base stage)
# SECURITY: Update all packages first, then install minimal runtime dependencies
# SIZE: Significantly smaller than build stage dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        libcairo2=1.16.0-7 \
        libffi8=3.4.4-1 \
        coreutils=9.1-1 \
    # Aggressive cleanup to minimize image size
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

WORKDIR /app

# Production environment configuration
# OPTIMIZATION: Settings tuned for production performance and security

# VIRTUAL_ENV=/app/.venv    : Points to the virtual environment
# PATH="/app/.venv/bin:$PATH" : Ensures venv binaries are found first
# PYTHONPATH="/app"         : Allows imports from the app directory
# PYTHONOPTIMIZE=2          : Maximum Python bytecode optimization
# Other vars inherited from base stage for consistency

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONOPTIMIZE=2 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=1

# Copy essential files from build stage with proper ownership
# SECURITY: --chown ensures files are owned by non-root user
# EFFICIENCY: Only copies what's needed for runtime
COPY --from=build --chown=nonroot:nonroot /app/.venv /app/.venv
COPY --from=build --chown=nonroot:nonroot /app/tux /app/tux
COPY --from=build --chown=nonroot:nonroot /app/prisma /app/prisma
COPY --from=build --chown=nonroot:nonroot /app/config /app/config
COPY --from=build --chown=nonroot:nonroot /app/pyproject.toml /app/pyproject.toml
COPY --from=build --chown=nonroot:nonroot /app/VERSION /app/VERSION

# Create convenient symlinks for Python and application binaries
# USABILITY: Allows running 'python' and 'tux' commands without full paths
# COMPATIBILITY: Maintains expected command locations for scripts and debugging
RUN ln -sf /app/.venv/bin/python /usr/local/bin/python && \
    ln -sf /app/.venv/bin/tux /usr/local/bin/tux

# Setup directories and permissions before Prisma setup
# SECURITY: Ensures proper directory structure and permissions
RUN set -eux; \
    # Fix permissions for virtual environment
    chown -R nonroot:nonroot /app/.venv; \
    # Create required runtime directories
    mkdir -p /app/.cache/tldr /app/temp; \
    # Create user cache directories (fixes permission issues for Prisma/npm)
    mkdir -p /home/nonroot/.cache /home/nonroot/.npm; \
    chown -R nonroot:nonroot /app/.cache /app/temp /home/nonroot/.cache /home/nonroot/.npm; \
    # Remove npm cache to reduce scan time and image size
    rm -rf /home/nonroot/.npm/_cacache

# Switch to non-root user for security and run Prisma setup
# SECURITY: Application runs with minimal privileges
# RUNTIME: Ensures Prisma binaries and client are properly configured as nonroot user
USER nonroot
RUN /app/.venv/bin/python -m prisma py fetch && \
    /app/.venv/bin/python -m prisma generate

# Aggressive cleanup and optimization after Prisma setup
# PERFORMANCE: Single RUN reduces layer count and enables atomic cleanup
# SIZE: Removes unnecessary files to minimize final image size but preserves Prisma binaries
USER root
RUN set -eux; \
    # VIRTUAL ENVIRONMENT CLEANUP
    # The following operations remove unnecessary files from the Python environment
    # This can reduce the size by 30-50MB without affecting functionality
    \
    # Remove Python bytecode files (will be regenerated as needed)
    find /app/.venv -name "*.pyc" -delete; \
    find /app/.venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true; \
    \
    # Remove test directories from installed packages (but preserve prisma binaries)
    # These directories contain test files that are not needed in production
    for test_dir in tests testing "*test*"; do \
        find /app/.venv -name "$test_dir" -type d -not -path "*/prisma*" -exec rm -rf {} + 2>/dev/null || true; \
    done; \
    \
    # Remove documentation files from installed packages (but preserve prisma docs)
    # These files take up significant space and are not needed in production
    for doc_pattern in "*.md" "*.txt" "*.rst" "LICENSE*" "NOTICE*" "COPYING*" "CHANGELOG*" "README*" "HISTORY*" "AUTHORS*" "CONTRIBUTORS*"; do \
        find /app/.venv -name "$doc_pattern" -not -path "*/prisma*" -delete 2>/dev/null || true; \
    done; \
    \
    # Remove large development packages that are not needed in production
    # These packages (pip, setuptools, wheel) are only needed for installing packages
    # NOTE: Preserving packages that Prisma might need
    for pkg in setuptools wheel pkg_resources; do \
        rm -rf /app/.venv/lib/python3.13/site-packages/${pkg}* 2>/dev/null || true; \
        rm -rf /app/.venv/bin/${pkg}* 2>/dev/null || true; \
    done; \
    rm -rf /app/.venv/bin/easy_install* 2>/dev/null || true; \
    \
    # Compile Python bytecode for performance optimization
    # PERFORMANCE: Pre-compiled bytecode improves startup time
    # Note: Some compilation errors are expected and ignored
    /app/.venv/bin/python -m compileall -b -q /app/tux /app/.venv/lib/python3.13/site-packages/ 2>/dev/null || true; \
    \
    # Switch back to nonroot user for final ownership
    chown -R nonroot:nonroot /app /home/nonroot

# Switch back to non-root user for runtime
USER nonroot

# Health check configuration for container orchestration
# MONITORING: Allows Docker/Kubernetes to monitor application health
# RELIABILITY: Enables automatic restart of unhealthy containers
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import tux.cli.core; import tux.utils.env; print('Health check passed')" || exit 1

# --interval=30s    : Check health every 30 seconds
# --timeout=10s     : Allow 10 seconds for health check to complete
# --start-period=40s: Wait 40 seconds before first health check (startup time)
# --retries=3       : Mark unhealthy after 3 consecutive failures

# Application entry point and default command
# DEPLOYMENT: Configures how the container starts in production
ENTRYPOINT ["tux"]
CMD ["--prod", "start"]

# ENTRYPOINT ["tux"]     : Always runs the tux command
# CMD ["--prod", "start"]: Default arguments for production mode
# FLEXIBILITY: CMD can be overridden, ENTRYPOINT cannot (security)

# ==============================================================================
# DOCKERFILE BEST PRACTICES IMPLEMENTED
# ==============================================================================
#
# 1. MULTI-STAGE BUILDS: Separates build and runtime environments
# 2. LAYER OPTIMIZATION: Ordered operations to maximize cache hits
# 3. SECURITY: Non-root user, pinned versions, minimal attack surface
# 4. SIZE OPTIMIZATION: Aggressive cleanup, minimal dependencies
# 5. MAINTAINABILITY: Comprehensive documentation, organized structure
# 6. RELIABILITY: Health checks, proper error handling
# 7. PERFORMANCE: Optimized Python settings, pre-compiled bytecode
# 8. COMPLIANCE: OCI labels, standard conventions
#
# USAGE EXAMPLES:
# ---------------
# Build production image:
#   docker build --target production -t tux:latest .
#
# Build development image:
#   docker build --target dev -t tux:dev .
#
# Build with devcontainer tools:
#   docker build --target dev --build-arg DEVCONTAINER=1 -t tux:devcontainer .
#
# Run production container:
#   docker run -d --name tux-bot --env-file .env tux:latest
#
# Run development container:
#   docker-compose -f docker-compose.dev.yml up
#
# ==============================================================================
