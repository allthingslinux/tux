# Base stage:
# - Pin the Python base image for all stages
# - Install only the common runtime dependencies and shared libraries
FROM python:3.13.2-slim AS base

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  git \
  libcairo2 \
  libgdk-pixbuf2.0-0 \
  libpango1.0-0 \
  libpangocairo-1.0-0 \
  shared-mime-info \
  ffmpeg && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Tweak Python to run better in Docker
ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=on


# Build stage:
# - Install build tools (for packages with native dependencies)
# - Install dev headers for packages with native dependencies
# - Install poetry (for managing app's dependencies)
# - Install app's main dependencies
# - Install the application itself
# - Generate Prisma client AND copy binaries
FROM base AS build

# Install build dependencies (excluding Node.js)
RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  build-essential \
  libcairo2-dev \
  libffi-dev \
  findutils \
  && apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Node.js installation removed - prisma-client-py handles its own

ENV POETRY_VERSION=2.1.1 \
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=1 \
  POETRY_VIRTUALENVS_IN_PROJECT=1 \
  POETRY_CACHE_DIR=/tmp/poetry_cache

RUN --mount=type=cache,target=/root/.cache pip install poetry==$POETRY_VERSION

WORKDIR /app

COPY . .
RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
  poetry install --only main --no-root --no-directory

RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
  --mount=type=cache,target=/root/.cache \
  poetry install --only main && \
  poetry run prisma py fetch && \
  poetry run prisma generate && \
  # --- Start: Copy Prisma Binaries ---
  # Find the actual query engine binary path
  PRISMA_QUERY_ENGINE_PATH=$(find /root/.cache/prisma-python/binaries -name query-engine-* -type f | head -n 1) && \
  # Find the actual schema engine binary path (might be needed too)
  PRISMA_SCHEMA_ENGINE_PATH=$(find /root/.cache/prisma-python/binaries -name schema-engine-* -type f | head -n 1) && \
  # Create a directory within /app to store them
  mkdir -p /app/prisma_binaries && \
  # Copy and make executable
  if [ -f "$PRISMA_QUERY_ENGINE_PATH" ]; then cp $PRISMA_QUERY_ENGINE_PATH /app/prisma_binaries/query-engine && chmod +x /app/prisma_binaries/query-engine; else echo "Warning: Query engine not found"; fi && \
  if [ -f "$PRISMA_SCHEMA_ENGINE_PATH" ]; then cp $PRISMA_SCHEMA_ENGINE_PATH /app/prisma_binaries/schema-engine && chmod +x /app/prisma_binaries/schema-engine; else echo "Warning: Schema engine not found"; fi
# --- End: Copy Prisma Binaries ---


# Dev stage (used by docker-compose.dev.yml):
# - Install extra tools for development (pre-commit, ruff, pyright, types, etc.)
# - Re-generate Prisma client on every run (CMD handles this)

FROM build AS dev

WORKDIR /app

RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
  poetry install --only dev --no-root --no-directory

# Ensure Prisma client is regenerated on start, then run bot via CLI with --dev flag
CMD ["sh", "-c", "poetry run prisma generate && exec poetry run tux --dev start"]


# Production stage:
# - Start with the base with the runtime dependencies already installed
# - Run the app as a nonroot user (least privileges principle)
# - Use the packaged self-sufficient application bundle
FROM base AS production

# Create a non-root user and group using standard tools for Debian base
RUN groupadd --system nonroot && \
  useradd --create-home --system --gid nonroot nonroot

WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv \
  PATH="/app/.venv/bin:$PATH" \
  # --- Start: Point Prisma client to the copied binaries ---
  PRISMA_QUERY_ENGINE_BINARY="/app/prisma_binaries/query-engine" \
  PRISMA_SCHEMA_ENGINE_BINARY="/app/prisma_binaries/schema-engine"
# --- End: Point Prisma client ---

# Copy the application code, venv, and the prepared prisma_binaries dir
# Ensure ownership is set to nonroot
COPY --from=build --chown=nonroot:nonroot /app /app

# Create TLDR cache directory with proper permissions for the nonroot user
RUN mkdir -p /app/.cache/tldr && \
  chown -R nonroot:nonroot /app/.cache

# Switch to the non-root user
USER nonroot

ENTRYPOINT ["tux"]
CMD ["--prod", "start"]
