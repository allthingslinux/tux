# Base stage:
# - Pin the Python base image for all stages
# - Install only the common runtime dependencies and shared libraries
FROM python:3.13.2-slim AS base

LABEL org.opencontainers.image.source="https://github.com/allthingslinux/tux" \
      org.opencontainers.image.description="Tux" \
      org.opencontainers.image.licenses="GPL-3.0" \
      org.opencontainers.image.authors="All Things Linux" \
      org.opencontainers.image.vendor="All Things Linux"

# Create non-root user early for security
RUN groupadd --system --gid 1001 nonroot && \
    useradd --create-home --system --uid 1001 --gid nonroot nonroot

# Install runtime dependencies (sorted alphabetically)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        libcairo2 \
        libgdk-pixbuf2.0-0 \
        libpango1.0-0 \
        libpangocairo-1.0-0 \
        shared-mime-info \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Tweak Python to run better in Docker
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=1


# Build stage:
# - Install build tools (for packages with native dependencies)
# - Install dev headers for packages with native dependencies
# - Install poetry (for managing app's dependencies)
# - Install app's main dependencies
# - Install the application itself
# - Generate Prisma client
FROM base AS build

# Install build dependencies (sorted alphabetically)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        findutils \
        libcairo2-dev \
        libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=2.1.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    POETRY_INSTALLER_PARALLEL=true

RUN --mount=type=cache,target=/root/.cache \
    pip install poetry==$POETRY_VERSION

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    poetry install --only main --no-root --no-directory

# Copy application code
COPY . .

# Install application and generate Prisma client
RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    --mount=type=cache,target=/root/.cache \
    git init . && \
    git config user.email "docker@build.local" && \
    git config user.name "Docker Build" && \
    poetry install --only main && \
    poetry run prisma py fetch && \
    poetry run prisma generate


# Dev stage (used by docker-compose.dev.yml):
# - Install extra tools for development
# - Set up development environment
FROM build AS dev

WORKDIR /app

ARG DEVCONTAINER=0
ENV DEVCONTAINER=${DEVCONTAINER}

# Setup development environment in one optimized layer
RUN set -eux; \
    # Conditionally install zsh for devcontainer
    if [ "$DEVCONTAINER" = "1" ]; then \
        apt-get update && \
        apt-get install -y --no-install-recommends zsh && \
        chsh -s /usr/bin/zsh && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*; \
    fi; \
    # Create cache directories
    mkdir -p /app/.cache/tldr /app/temp; \
    # Fix ownership of all app files and directories in single operation
    chown -R nonroot:nonroot /app

# Switch to non-root user for development
USER nonroot

# Configure Git for non-root user and install development dependencies
# Note: Cache mount removed due to network connectivity issues with Poetry
RUN git config --global --add safe.directory /app && \
    poetry install --only dev --no-root --no-directory

# Regenerate Prisma client on start for development
CMD ["sh", "-c", "poetry run prisma generate && exec poetry run tux --dev start"]


# Production stage:
# - Minimal, secure runtime environment  
# - Non-root user execution
# - Optimized for size and security
FROM python:3.13.2-slim AS production

LABEL org.opencontainers.image.source="https://github.com/allthingslinux/tux" \
      org.opencontainers.image.description="Tux" \
      org.opencontainers.image.licenses="GPL-3.0" \
      org.opencontainers.image.authors="All Things Linux" \
      org.opencontainers.image.vendor="All Things Linux"

# Create non-root user
RUN groupadd --system --gid 1001 nonroot && \
    useradd --create-home --system --uid 1001 --gid nonroot nonroot

# Install ONLY runtime dependencies (minimal set)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libcairo2 \
        libffi8 \
        coreutils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

WORKDIR /app

# Set up environment for production
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONOPTIMIZE=2 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=1

# Copy only essential production files
COPY --from=build --chown=nonroot:nonroot /app/.venv /app/.venv
COPY --from=build --chown=nonroot:nonroot /app/tux /app/tux
COPY --from=build --chown=nonroot:nonroot /app/prisma /app/prisma
COPY --from=build --chown=nonroot:nonroot /app/config /app/config
COPY --from=build --chown=nonroot:nonroot /app/pyproject.toml /app/pyproject.toml

# Aggressive cleanup and optimization in one layer
RUN set -eux; \
    # Fix permissions
    chown -R nonroot:nonroot /app/.venv; \
    mkdir -p /app/.cache/tldr /app/temp; \
    chown -R nonroot:nonroot /app/.cache /app/temp; \
    \
    # AGGRESSIVE virtualenv cleanup
    cd /app/.venv; \
    \
    # Remove all bytecode first
    find . -name "*.pyc" -delete; \
    find . -name "*.pyo" -delete; \
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true; \
    \
    # Remove package metadata and installation files (but keep tux metadata)
    find . -name "*.egg-info" -type d ! -name "*tux*" -exec rm -rf {} + 2>/dev/null || true; \
    find . -name "*.dist-info" -type d ! -name "*tux*" -exec rm -rf {} + 2>/dev/null || true; \
    \
    # Remove test and development files
    find . -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true; \
    find . -name "test" -type d -exec rm -rf {} + 2>/dev/null || true; \
    find . -name "testing" -type d -exec rm -rf {} + 2>/dev/null || true; \
    find . -name "*test*" -type d -exec rm -rf {} + 2>/dev/null || true; \
    \
    # Remove documentation
    find . -name "docs" -type d -exec rm -rf {} + 2>/dev/null || true; \
    find . -name "doc" -type d -exec rm -rf {} + 2>/dev/null || true; \
    find . -name "examples" -type d -exec rm -rf {} + 2>/dev/null || true; \
    find . -name "samples" -type d -exec rm -rf {} + 2>/dev/null || true; \
    \
    # Remove all documentation files
    find . -name "*.md" -delete 2>/dev/null || true; \
    find . -name "*.txt" -delete 2>/dev/null || true; \
    find . -name "*.rst" -delete 2>/dev/null || true; \
    find . -name "LICENSE*" -delete 2>/dev/null || true; \
    find . -name "NOTICE*" -delete 2>/dev/null || true; \
    find . -name "COPYING*" -delete 2>/dev/null || true; \
    find . -name "CHANGELOG*" -delete 2>/dev/null || true; \
    find . -name "README*" -delete 2>/dev/null || true; \
    find . -name "HISTORY*" -delete 2>/dev/null || true; \
    find . -name "AUTHORS*" -delete 2>/dev/null || true; \
    find . -name "CONTRIBUTORS*" -delete 2>/dev/null || true; \
    \
    # Remove large packages not needed in production
    rm -rf lib/python3.13/site-packages/pip* 2>/dev/null || true; \
    rm -rf lib/python3.13/site-packages/setuptools* 2>/dev/null || true; \
    rm -rf lib/python3.13/site-packages/wheel* 2>/dev/null || true; \
    rm -rf lib/python3.13/site-packages/pkg_resources* 2>/dev/null || true; \
    \
    # Remove binaries from site-packages bin if they exist
    rm -rf bin/pip* bin/easy_install* bin/wheel* 2>/dev/null || true; \
    \
    # Remove debug symbols and static libraries
    find . -name "*.so.debug" -delete 2>/dev/null || true; \
    find . -name "*.a" -delete 2>/dev/null || true; \
    \
    # Remove locale files (if your app doesn't need i18n)
    find . -name "*.mo" -delete 2>/dev/null || true; \
    find . -name "locale" -type d -exec rm -rf {} + 2>/dev/null || true; \
    \
    # Remove source maps and other development artifacts
    find . -name "*.map" -delete 2>/dev/null || true; \
    find . -name "*.coffee" -delete 2>/dev/null || true; \
    find . -name "*.ts" -delete 2>/dev/null || true; \
    find . -name "*.scss" -delete 2>/dev/null || true; \
    find . -name "*.less" -delete 2>/dev/null || true; \
    \
    # Compile Python bytecode and remove source files for some packages  
    /app/.venv/bin/python -m compileall -b -q /app/tux /app/.venv/lib/python3.13/site-packages/ 2>/dev/null || true; \
    \
    # Strip binaries (if strip is available)
    find . -name "*.so" -exec strip --strip-unneeded {} + 2>/dev/null || true;

# Create symlink for python accessibility and ensure everything is working
RUN ln -sf /app/.venv/bin/python /usr/local/bin/python && \
    ln -sf /app/.venv/bin/tux /usr/local/bin/tux

# Switch to non-root user
USER nonroot

# Add health check that verifies the application can import core modules
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import tux.cli.core; import tux.utils.env; print('Health check passed')" || exit 1

ENTRYPOINT ["tux"]
CMD ["--prod", "start"]
