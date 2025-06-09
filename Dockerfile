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

FROM python:3.13.2-slim AS base

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

# Install runtime dependencies required for the application
# SECURITY: Pinned versions prevent supply chain attacks and ensure reproducibility
# PERFORMANCE: Packages sorted alphabetically for better caching and maintenance
# NOTE: These are the minimal dependencies required for the bot to function
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
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

# Copy dependency files first for optimal Docker layer caching
# Changes to these files will invalidate subsequent layers
# OPTIMIZATION: This pattern maximizes cache hits during development
COPY pyproject.toml poetry.lock ./

# Install Python dependencies using Poetry
# PERFORMANCE: Cache mount speeds up subsequent builds
# SECURITY: --only main excludes development dependencies from production
RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
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
COPY README.md LICENSE.md pyproject.toml ./

# Install the application and generate Prisma client
# COMPLEXITY: This step requires multiple operations that must be done together
RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    --mount=type=cache,target=/root/.cache \
    # Initialize minimal git repository for Poetry dynamic versioning
    # Poetry requires git for version detection from tags/commits
    git init --quiet . && \
    # Install the application package itself
    poetry install --only main && \
    # Clean up git repository (not needed in final image)
    rm -rf .git

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

# Configure Git and install development dependencies
# DEVELOPMENT: These tools are needed for linting, testing, and development workflow
RUN git init --quiet . && \
    # Allow git operations in the app directory (required for Poetry)
    git config --global --add safe.directory /app && \
    # Install development dependencies (linters, formatters, test tools, etc.)
    # NOTE: Cache mount removed due to network connectivity issues with Poetry
    poetry install --only dev --no-root --no-directory && \
    # Fetch Prisma binaries for the current platform (as nonroot user)
    poetry run prisma py fetch && \
    # Generate Prisma client code based on schema (as nonroot user)
    poetry run prisma generate && \
    # Clean up git repository
    rm -rf .git

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

FROM python:3.13.2-slim AS production

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

# Install ONLY runtime dependencies (minimal subset of base stage)
# SECURITY: Reduced attack surface by excluding unnecessary packages
# SIZE: Significantly smaller than build stage dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
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

# Aggressive cleanup and optimization in a single layer
# PERFORMANCE: Single RUN reduces layer count and enables atomic cleanup
# SIZE: Removes unnecessary files to minimize final image size
RUN set -eux; \
    # Fix permissions for virtual environment
    chown -R nonroot:nonroot /app/.venv; \
    # Create required runtime directories
    mkdir -p /app/.cache/tldr /app/temp; \
    # Create user cache directories (fixes permission issues for Prisma/npm)
    mkdir -p /home/nonroot/.cache /home/nonroot/.npm; \
    chown -R nonroot:nonroot /app/.cache /app/temp /home/nonroot/.cache /home/nonroot/.npm; \
    \
    # VIRTUAL ENVIRONMENT CLEANUP
    # The following operations remove unnecessary files from the Python environment
    # This can reduce the size by 30-50MB without affecting functionality
    \
    # Remove Python bytecode files (will be regenerated as needed)
    find /app/.venv -name "*.pyc" -delete; \
    find /app/.venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true; \
    \
    # Remove test directories from installed packages
    # These directories contain test files that are not needed in production
    for test_dir in tests testing "*test*"; do \
        find /app/.venv -name "$test_dir" -type d -exec rm -rf {} + 2>/dev/null || true; \
    done; \
    \
    # Remove documentation files from installed packages
    # These files take up significant space and are not needed in production
    for doc_pattern in "*.md" "*.txt" "*.rst" "LICENSE*" "NOTICE*" "COPYING*" "CHANGELOG*" "README*" "HISTORY*" "AUTHORS*" "CONTRIBUTORS*"; do \
        find /app/.venv -name "$doc_pattern" -delete 2>/dev/null || true; \
    done; \
    \
    # Remove large development packages that are not needed in production
    # These packages (pip, setuptools, wheel) are only needed for installing packages
    for pkg in pip setuptools wheel pkg_resources; do \
        rm -rf /app/.venv/lib/python3.13/site-packages/${pkg}* 2>/dev/null || true; \
        rm -rf /app/.venv/bin/${pkg}* 2>/dev/null || true; \
    done; \
    rm -rf /app/.venv/bin/easy_install* 2>/dev/null || true; \
    \
    # Compile Python bytecode for performance optimization
    # PERFORMANCE: Pre-compiled bytecode improves startup time
    # Note: Some compilation errors are expected and ignored
    /app/.venv/bin/python -m compileall -b -q /app/tux /app/.venv/lib/python3.13/site-packages/ 2>/dev/null || true

# Create convenient symlinks for Python and application binaries
# USABILITY: Allows running 'python' and 'tux' commands without full paths
# COMPATIBILITY: Maintains expected command locations for scripts and debugging
RUN ln -sf /app/.venv/bin/python /usr/local/bin/python && \
    ln -sf /app/.venv/bin/tux /usr/local/bin/tux

# Switch to non-root user for security and run Prisma setup
# SECURITY: Application runs with minimal privileges
# RUNTIME: Ensures Prisma binaries and client are properly configured as nonroot user
USER nonroot
RUN /app/.venv/bin/python -m prisma py fetch && \
    /app/.venv/bin/python -m prisma generate

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
