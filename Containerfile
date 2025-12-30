# ============================================================================
# STAGE 1: Common Setup (shared by base and production stages)
# ============================================================================
FROM python:3.13.8-slim@sha256:087a9f3b880e8b2c7688debb9df2a5106e060225ebd18c264d5f1d7a73399db0 AS common

# Common labels (shared across all final images)
LABEL org.opencontainers.image.source="https://github.com/allthingslinux/tux" \
        org.opencontainers.image.description="Tux - The all in one discord bot for the All Things Linux Community" \
        org.opencontainers.image.licenses="GPL-3.0" \
        org.opencontainers.image.authors="All Things Linux" \
        org.opencontainers.image.vendor="All Things Linux" \
        org.opencontainers.image.title="Tux" \
        org.opencontainers.image.documentation="https://github.com/allthingslinux/tux/blob/main/README.md"

# Common user setup (non-root user)
RUN groupadd --system --gid 1001 nonroot && \
        useradd --create-home --system --uid 1001 --gid nonroot nonroot

# Common environment variables
ENV DEBIAN_FRONTEND=noninteractive \
        DEBCONF_NONINTERACTIVE_SEEN=true

# Common dpkg configuration (reduce package size)
RUN echo 'path-exclude /usr/share/doc/*' > /etc/dpkg/dpkg.cfg.d/01_nodoc && \
        echo 'path-include /usr/share/doc/*/copyright' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
        echo 'path-exclude /usr/share/man/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
        echo 'path-exclude /usr/share/groff/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
        echo 'path-exclude /usr/share/info/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
        echo 'path-exclude /usr/share/lintian/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
        echo 'path-exclude /usr/share/linda/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc

# Common Python environment variables
ENV PYTHONUNBUFFERED=1 \
        PYTHONDONTWRITEBYTECODE=1 \
        PIP_DISABLE_PIP_VERSION_CHECK=on \
        PIP_NO_CACHE_DIR=1

# ============================================================================
# STAGE 2: Base (extends common with build dependencies)
# ============================================================================
FROM common AS base

# hadolint ignore=DL3008
RUN apt-get update && \
        apt-get upgrade -y && \
        apt-get install -y --no-install-recommends --no-install-suggests \
        git \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        shared-mime-info \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

FROM base AS build

# hadolint ignore=DL3008
RUN apt-get update && \
        apt-get upgrade -y && \
        apt-get install -y --no-install-recommends \
        build-essential \
        findutils \
        libcairo2-dev \
        libffi8 \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

RUN pip install uv==0.8.0

WORKDIR /app

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
        --mount=type=bind,source=uv.lock,target=uv.lock \
        --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
        uv sync --locked --no-install-project --no-default-groups

COPY src/tux/database/migrations/ ./src/tux/database/migrations/

# Copy source code (plugins excluded via .dockerignore)
# Plugins are drop-in extensions that should be mounted as volumes at runtime, not in image
COPY src/ ./src/
RUN cp -a src/tux ./tux
# Ensure plugins directory exists (empty) for runtime volume mounts
# .dockerignore excludes plugin files, but directory structure is needed for mounts
RUN mkdir -p ./src/tux/plugins ./tux/plugins && \
        touch ./src/tux/plugins/.gitkeep ./tux/plugins/.gitkeep

COPY README.md LICENSE pyproject.toml alembic.ini ./
COPY scripts/ ./scripts/

ARG VERSION=""
ARG GIT_SHA=""
ARG BUILD_DATE=""

RUN set -eux; \
        if [ -n "$VERSION" ]; then \
        echo "Using provided version: $VERSION"; \
        echo "$VERSION" > /app/VERSION; \
        else \
        echo "No version provided, using fallback"; \
        echo "dev" > /app/VERSION; \
        fi; \
        echo "Building version: $(cat /app/VERSION)"

# Sync the project (exclude dev/test/docs/types groups for production)
RUN --mount=type=cache,target=/root/.cache/uv \
        uv sync --locked --no-default-groups

FROM build AS dev

WORKDIR /app

ARG DEVCONTAINER=0
ENV DEVCONTAINER=${DEVCONTAINER}

# hadolint ignore=DL3008
RUN set -eux; \
        if [ "$DEVCONTAINER" = "1" ]; then \
        apt-get update && \
        apt-get install -y --no-install-recommends zsh && \
        chsh -s /usr/bin/zsh && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*; \
        fi

COPY --from=build --chown=nonroot:nonroot /app /app

RUN set -eux; \
        mkdir -p /app/.cache/tldr /app/temp; \
        mkdir -p /home/nonroot/.cache /home/nonroot/.npm; \
        chown -R nonroot:nonroot /app/.cache /app/temp /home/nonroot/.cache /home/nonroot/.npm; \
        chmod -R 755 /app/.cache /app/temp /home/nonroot/.cache /home/nonroot/.npm

RUN uv sync --dev

ENV VIRTUAL_ENV=/app/.venv \
        PATH="/app/.venv/bin:$PATH" \
        PYTHONPATH="/app" \
        PYTHONUNBUFFERED=1 \
        PYTHONDONTWRITEBYTECODE=1 \
        TLDR_CACHE_DIR=/app/.cache/tldr

USER nonroot

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]

# ============================================================================
# STAGE 5: Production (extends common with runtime dependencies only)
# ============================================================================
FROM common AS production

# Production runtime dependencies only (no git, no build tools)
# hadolint ignore=DL3008
RUN apt-get update && \
        apt-get upgrade -y && \
        apt-get install -y --no-install-recommends --no-install-suggests \
        libcairo2 \
        libffi8 \
        coreutils \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/* \
        && rm -rf /var/cache/apt/* \
        && rm -rf /tmp/* \
        && rm -rf /var/tmp/*

WORKDIR /app

# Production-specific environment variables (extends common Python env vars)
ENV VIRTUAL_ENV=/app/.venv \
        PATH="/app/.venv/bin:$PATH" \
        PYTHONPATH="/app:/app/src" \
        PYTHONOPTIMIZE=2 \
        TLDR_CACHE_DIR=/app/.cache/tldr

COPY --from=build --chown=nonroot:nonroot /app/.venv /app/.venv
COPY --from=build --chown=nonroot:nonroot /app/tux /app/tux
COPY --from=build --chown=nonroot:nonroot /app/src /app/src
COPY --from=build --chown=nonroot:nonroot /app/pyproject.toml /app/pyproject.toml
COPY --from=build --chown=nonroot:nonroot /app/VERSION /app/VERSION
COPY --from=build --chown=nonroot:nonroot /app/alembic.ini /app/alembic.ini
COPY --from=build --chown=nonroot:nonroot /app/scripts /app/scripts

RUN ln -sf /app/.venv/bin/python /usr/local/bin/python && \
        ln -sf /app/.venv/bin/tux /usr/local/bin/tux

RUN set -eux; \
        mkdir -p /app/.cache/tldr /app/temp; \
        mkdir -p /home/nonroot/.cache /home/nonroot/.npm; \
        rm -rf /home/nonroot/.npm/_cacache_; \
        chown -R nonroot:nonroot /app/.cache /app/temp /home/nonroot/.cache /home/nonroot/.npm; \
        chmod -R 755 /app/.cache /app/temp /home/nonroot/.cache /home/nonroot/.npm

# Cleanup build artifacts and optimize image size
# Use dynamic Python version detection instead of hardcoded paths
RUN set -eux; \
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'); \
        PYTHON_LIB_PATH="/app/.venv/lib/python${PYTHON_VERSION:?}/site-packages"; \
        find /app/.venv -name "*.pyc" -delete 2>/dev/null || true; \
        find /app/.venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true; \
        for test_dir in tests testing "test*"; do \
        find /app/.venv -name "$test_dir" -type d -exec rm -rf {} + 2>/dev/null || true; \
        done; \
        for doc_pattern in "*.md" "*.txt" "*.rst" "LICENSE*" "NOTICE*" "COPYING*" "CHANGELOG*" "README*" "HISTORY*" "AUTHORS*" "CONTRIBUTORS*"; do \
        find /app/.venv -name "$doc_pattern" -delete 2>/dev/null || true; \
        done; \
        for pkg in setuptools wheel pkg_resources; do \
        rm -rf "${PYTHON_LIB_PATH:?}/${pkg}"* 2>/dev/null || true; \
        rm -rf /app/.venv/bin/${pkg}* 2>/dev/null || true; \
        done; \
        rm -rf /app/.venv/bin/easy_install* 2>/dev/null || true; \
        /app/.venv/bin/python -m compileall -b -q /app/tux "${PYTHON_LIB_PATH:?}" 2>/dev/null || true

USER nonroot

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
        CMD python -c "import tux.shared.config.settings; print('Health check passed')" || exit 1

COPY --chmod=755 docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD []
