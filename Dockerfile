FROM python:3.13.7-slim@sha256:27f90d79cc85e9b7b2560063ef44fa0e9eaae7a7c3f5a9f74563065c5477cc24 AS base

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
        git \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        shared-mime-info \
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
# Purpose: Installs build tools, Uv, and application dependencies
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
        build-essential \
        # Additional utilities required by some Python packages
        findutils \
        # Development headers for graphics libraries
        libcairo2-dev \
        # Foreign Function Interface library for Python extensions
        libffi8 \
    # Cleanup to reduce intermediate layer size
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV UV_VERSION=0.8.0

# Install Uv using pip
RUN pip install uv==$UV_VERSION

# Set working directory for all subsequent operations
WORKDIR /app

# Set shell to bash with pipefail for proper error handling in pipes
# This must be set before any RUN commands that use pipes
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Copy dependency files first for optimal Docker layer caching
# Changes to these files will invalidate subsequent layers
# OPTIMIZATION: This pattern maximizes cache hits during development
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy application files in order of change frequency (Docker layer optimization)
# STRATEGY: Files that change less frequently are copied first to maximize cache reuse

# 1. Configuration files (rarely change)
# These are typically static configuration that changes infrequently
# Note: Configuration is now handled via environment variables

# 2. Database migration files (change infrequently)
# Alembic migrations are relatively stable
COPY src/tux/database/migrations/ ./src/tux/database/migrations/

# 3. Main application code (changes more frequently)
# The core bot code is most likely to change during development
# Copy the entire src tree so Poetry can find packages from "src"
COPY src/ ./src/
# Keep runtime path stable at /app/tux for later stages and health checks
RUN cp -a src/tux ./tux

# 4. Root level files needed for installation
# These include metadata and licensing information
COPY README.md LICENSE pyproject.toml alembic.ini ./

# 5. Copy scripts directory for entry points
COPY scripts/ ./scripts/

# Build arguments for version information
# These allow passing version info without requiring git history in build context
ARG VERSION=""
ARG GIT_SHA=""
ARG BUILD_DATE=""

# Generate version file using build args with fallback
# PERFORMANCE: Version is determined at build time, not runtime
# SECURITY: Git operations happen outside container, only VERSION string is passed in
# The new unified version system will use this VERSION file as priority 2
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

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

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

RUN set -eux; \
    # Conditionally install zsh for enhanced development experience
    # Only installs if DEVCONTAINER build arg is set to 1
    if [ "$DEVCONTAINER" = "1" ]; then \
        apt-get update && \
        apt-get install -y --no-install-recommends zsh && \
        chsh -s /usr/bin/zsh && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*; \
    fi; \
    # Fix ownership of all application files for non-root user
    # SECURITY: Ensures the application runs with proper permissions
    COPY --from=build --chown=nonroot:nonroot /app /app

RUN set -eux; \
    # Create application cache and temporary directories
    # These directories are used by the bot for caching and temporary files
    mkdir -p /app/.cache/tldr /app/temp; \
    # Create user cache directories (fixes permission issues for npm and other tools)
    mkdir -p /home/nonroot/.cache /home/nonroot/.npm; \
    # Ensure correct ownership for nonroot user to write into these directories
    chown -R nonroot:nonroot /app/.cache /app/temp /home/nonroot/.cache /home/nonroot/.npm; \
    chmod -R 755 /app/.cache /app/temp /home/nonroot/.cache /home/nonroot/.npm

# Install development dependencies BEFORE switching to non-root user
# DEVELOPMENT: These tools are needed for linting, testing, and development workflow
RUN uv sync --dev

# Set development environment variables
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user for all subsequent operations
# SECURITY: Follows principle of least privilege
USER nonroot

# Development container startup command
# WORKFLOW: Starts the bot in development mode with automatic database migrations
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]

# ==============================================================================
# PRODUCTION STAGE - Minimal Runtime Environment
# ==============================================================================
# Purpose: Creates a minimal, secure, and optimized image for production deployment
# Contains: Only runtime dependencies, application code, and essential files
# Security: Non-root execution, minimal attack surface, health monitoring
# Size Impact: ~440MB (73% reduction from development image)
# ==============================================================================

FROM python:3.13.7-slim@sha256:27f90d79cc85e9b7b2560063ef44fa0e9eaae7a7c3f5a9f74563065c5477cc24 AS production

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
    echo 'path-exclude /usr/share/lintian/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc

# Install ONLY runtime dependencies (minimal subset of base stage)
# SECURITY: Update all packages first, then install minimal runtime dependencies
# SIZE: Significantly smaller than build stage dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends --no-install-suggests \
    libcairo2 \
    libffi8 \
    coreutils \
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
# PYTHONPATH="/app:/app/src" : Allows imports from both app and src directories
# PYTHONOPTIMIZE=2          : Maximum Python bytecode optimization
# Other vars inherited from base stage for consistency

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app:/app/src" \
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
COPY --from=build --chown=nonroot:nonroot /app/src /app/src

COPY --from=build --chown=nonroot:nonroot /app/pyproject.toml /app/pyproject.toml
COPY --from=build --chown=nonroot:nonroot /app/VERSION /app/VERSION
COPY --from=build --chown=nonroot:nonroot /app/alembic.ini /app/alembic.ini
COPY --from=build --chown=nonroot:nonroot /app/scripts /app/scripts

# Create convenient symlinks for Python and application binaries
# USABILITY: Allows running 'python' and 'tux' commands without full paths
# COMPATIBILITY: Maintains expected command locations for scripts and debugging
RUN ln -sf /app/.venv/bin/python /usr/local/bin/python && \
    ln -sf /app/.venv/bin/tux /usr/local/bin/tux

RUN set -eux; \
    mkdir -p /app/.cache/tldr /app/temp; \
    mkdir -p /home/nonroot/.cache /home/nonroot/.npm; \
    rm -rf /home/nonroot/.npm/_cacache_; \
    chown -R nonroot:nonroot /app/.cache /app/temp /home/nonroot/.cache /home/nonroot/.npm; \
    chmod -R 755 /app/.cache /app/temp /home/nonroot/.cache /home/nonroot/.npm

# Switch to non-root user for final optimizations
USER nonroot

USER root
# Aggressive cleanup and optimization
# PERFORMANCE: Single RUN reduces layer count and enables atomic cleanup
# SIZE: Removes unnecessary files to minimize final image size
RUN set -eux; \
    # VIRTUAL ENVIRONMENT CLEANUP
    # The following operations remove unnecessary files from the Python environment
    # This can reduce the size by 30-50MB without affecting functionality
    # Remove Python bytecode files (will be regenerated as needed)
    find /app/.venv -name "*.pyc" -delete; \
    find /app/.venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true; \
    # Remove test directories from installed packages (but preserve prisma binaries)
    # These directories contain test files that are not needed in production
    for test_dir in tests testing "test*"; do \
    find /app/.venv -name "$test_dir" -type d -not -path "*/prisma*" -exec rm -rf {} + 2>/dev/null || true; \
    done; \
    # Remove documentation files from installed packages (but preserve prisma docs)
    # These files take up significant space and are not needed in production
    for doc_pattern in "*.md" "*.txt" "*.rst" "LICENSE*" "NOTICE*" "COPYING*" "CHANGELOG*" "README*" "HISTORY*" "AUTHORS*" "CONTRIBUTORS*"; do \
    find /app/.venv -name "$doc_pattern" -not -path "*/prisma*" -delete 2>/dev/null || true; \
    done; \
    # Remove large development packages that are not needed in production
    # These packages (pip, setuptools, wheel) are only needed for installing packages
    # NOTE: Preserving packages that Prisma might need
    for pkg in setuptools wheel pkg_resources; do \
    rm -rf /app/.venv/lib/python3.13/site-packages/${pkg}* 2>/dev/null || true; \
    rm -rf /app/.venv/bin/${pkg}* 2>/dev/null || true; \
    done; \
    rm -rf /app/.venv/bin/easy_install* 2>/dev/null || true; \
    # Compile Python bytecode for performance optimization
    # PERFORMANCE: Pre-compiled bytecode improves startup time
    # Note: Some compilation errors are expected and ignored
    /app/.venv/bin/python -m compileall -b -q /app/tux /app/.venv/lib/python3.13/site-packages 2>/dev/null || true

# Switch back to non-root user for runtime
USER nonroot

# Health check configuration for container orchestration
# MONITORING: Allows Docker/Kubernetes to monitor application health
# RELIABILITY: Enables automatic restart of unhealthy containers
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import tux.shared.config.env; print('Health check passed')" || exit 1

# --interval=30s    : Check health every 30 seconds
# --timeout=10s     : Allow 10 seconds for health check to complete
# --start-period=40s: Wait 40 seconds before first health check (startup time)
# --retries=3       : Mark unhealthy after 3 consecutive failures

# Application entry point and default command
# DEPLOYMENT: Configures how the container starts in production
# Use tini as init system for proper signal handling and zombie process cleanup
COPY --chmod=755 docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD []
