# Base stage:
# - Pin the Python base image for all stages
# - Install only the common runtime dependencies
#   - git
#   - tealdeer
FROM python:3.13-slim AS base

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        tealdeer && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    tldr -u

# Tweak Python to run better in Docker
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on


# Build stage:
# - Install build tools (for packages with native dependencies)
# - Install poetry (for managing app's dependencies)
# - Install app's main dependencies
# - Install the application itself
# - Generate Prisma client
FROM base AS build

# TODO: Are these needed?
# - curl
# - libgdk-pixbuf2.0-0
# - libpango1.0-0
# - libpangocairo-1.0-0
# - shared-mime-info

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libcairo2 \
        libffi-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=2.0.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN --mount=type=cache,target=/root/.cache pip install poetry==$POETRY_VERSION

WORKDIR /app

# Copy only the metadata files to increase build cache hit rate
COPY pyproject.toml poetry.lock ./
RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    poetry install --only main --no-root --no-directory

# Now install the application itself
COPY . .
RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    --mount=type=cache,target=/root/.cache \
    poetry install --only main && \
    poetry run prisma py fetch && \
    poetry run prisma generate


# Dev stage (used by docker-compose):
# - Install extra tools for development (pre-commit, ruff, pyright, types, etc.)
# - Re-generate Prisma client on every run
FROM build AS dev

WORKDIR /app

RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    poetry install --only dev --no-root --no-directory

CMD ["sh", "-c", "ls && poetry run prisma generate && exec poetry run python tux/main.py"]


# Production stage:
# - Start with the base with the runtime dependencies already installed
# - Run the app as a nonroot user (least privileges principle)
# - Use the packaged self-sufficient application bundle
FROM base AS production

RUN adduser nonroot
USER nonroot

WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=build --chown=nonroot:nonroot /app ./

ENTRYPOINT ["python"]
CMD ["-m", "tux.main"]