# Base stage:
# - Pin the Python base image for all stages
# - Install only the common runtime dependencies and shared libraries
FROM python:3.13.2-slim AS base

LABEL org.opencontainers.image.source="https://github.com/allthingslinux/tux" \
      org.opencontainers.image.description="Tux Discord Bot" \
      org.opencontainers.image.licenses="GPL-3.0" \
      org.opencontainers.image.authors="AllThingsLinux" \
      org.opencontainers.image.vendor="AllThingsLinux"

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
    POETRY_CACHE_DIR=/tmp/poetry_cache

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

# Install development dependencies
RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    poetry install --only dev --no-root --no-directory

# Conditionally install zsh for devcontainer
RUN if [ "$DEVCONTAINER" = "1" ]; then \
        apt-get update && \
        apt-get install -y --no-install-recommends zsh && \
        chsh -s /usr/bin/zsh && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*; \
    fi

# Create cache directories with proper permissions
RUN mkdir -p /app/.cache/tldr /app/temp && \
    chown -R nonroot:nonroot /app/.cache /app/temp

# Switch to non-root user for development too
USER nonroot

# Regenerate Prisma client on start for development
CMD ["sh", "-c", "poetry run prisma generate && exec poetry run tux --dev start"]


# Production stage:
# - Minimal, secure runtime environment
# - Non-root user execution
# - Optimized for size and security
FROM base AS production

WORKDIR /app

# Set up environment for production
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Copy application code and dependencies with proper ownership
COPY --from=build --chown=nonroot:nonroot /app /app

# Create cache directories with proper permissions
RUN mkdir -p /app/.cache/tldr /app/temp && \
    chown -R nonroot:nonroot /app/.cache /app/temp

# Switch to non-root user
USER nonroot

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

ENTRYPOINT ["tux"]
CMD ["--prod", "start"]
