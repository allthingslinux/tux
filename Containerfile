FROM python:3.13.8-slim AS base

LABEL org.opencontainers.image.source="https://github.com/allthingslinux/tux" \
        org.opencontainers.image.description="Tux - The all in one discord bot for the All Things Linux Community" \
        org.opencontainers.image.licenses="GPL-3.0" \
        org.opencontainers.image.authors="All Things Linux" \
        org.opencontainers.image.vendor="All Things Linux" \
        org.opencontainers.image.title="Tux" \
        org.opencontainers.image.documentation="https://github.com/allthingslinux/tux/blob/main/README.md"

RUN groupadd --system --gid 1001 nonroot && \
        useradd --create-home --system --uid 1001 --gid nonroot nonroot

ENV DEBIAN_FRONTEND=noninteractive \
        DEBCONF_NONINTERACTIVE_SEEN=true

RUN echo 'path-exclude /usr/share/doc/*' > /etc/dpkg/dpkg.cfg.d/01_nodoc && \
        echo 'path-include /usr/share/doc/*/copyright' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
        echo 'path-exclude /usr/share/man/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
        echo 'path-exclude /usr/share/groff/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
        echo 'path-exclude /usr/share/info/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
        echo 'path-exclude /usr/share/lintian/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
        echo 'path-exclude /usr/share/linda/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc

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

ENV PYTHONUNBUFFERED=1 \
        PYTHONDONTWRITEBYTECODE=1 \
        PIP_DISABLE_PIP_VERSION_CHECK=on \
        PIP_NO_CACHE_DIR=1

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

ENV UV_VERSION=0.8.0

RUN pip install uv==$UV_VERSION

WORKDIR /app

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
        --mount=type=bind,source=uv.lock,target=uv.lock \
        --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
        uv sync --locked --no-install-project

COPY src/tux/database/migrations/ ./src/tux/database/migrations/

COPY src/ ./src/
RUN cp -a src/tux ./tux

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

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
        uv sync --locked

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
        fi; \
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
        PYTHONDONTWRITEBYTECODE=1

USER nonroot

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]

FROM python:3.13.8-slim AS production

LABEL org.opencontainers.image.source="https://github.com/allthingslinux/tux" \
        org.opencontainers.image.description="Tux - The all in one discord bot for the All Things Linux Community" \
        org.opencontainers.image.licenses="GPL-3.0" \
        org.opencontainers.image.authors="All Things Linux" \
        org.opencontainers.image.vendor="All Things Linux" \
        org.opencontainers.image.title="Tux" \
        org.opencontainers.image.documentation="https://github.com/allthingslinux/tux/blob/main/README.md"

RUN groupadd --system --gid 1001 nonroot && \
        useradd --create-home --system --uid 1001 --gid nonroot nonroot

ENV DEBIAN_FRONTEND=noninteractive \
        DEBCONF_NONINTERACTIVE_SEEN=true

RUN echo 'path-exclude /usr/share/doc/*' > /etc/dpkg/dpkg.cfg.d/01_nodoc && \
        echo 'path-include /usr/share/doc/*/copyright' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
        echo 'path-exclude /usr/share/man/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
        echo 'path-exclude /usr/share/groff/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
        echo 'path-exclude /usr/share/info/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc && \
        echo 'path-exclude /usr/share/lintian/*' >> /etc/dpkg/dpkg.cfg.d/01_nodoc

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

ENV VIRTUAL_ENV=/app/.venv \
        PATH="/app/.venv/bin:$PATH" \
        PYTHONPATH="/app:/app/src" \
        PYTHONOPTIMIZE=2 \
        PYTHONUNBUFFERED=1 \
        PYTHONDONTWRITEBYTECODE=1 \
        PIP_DISABLE_PIP_VERSION_CHECK=on \
        PIP_NO_CACHE_DIR=1

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

USER nonroot

USER root

RUN set -eux; \
        find /app/.venv -name "*.pyc" -delete; \
        find /app/.venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true; \
        for test_dir in tests testing "test*"; do \
        find /app/.venv -name "$test_dir" -type d -not -path "*/prisma*" -exec rm -rf {} + 2>/dev/null || true; \
        done; \
        for doc_pattern in "*.md" "*.txt" "*.rst" "LICENSE*" "NOTICE*" "COPYING*" "CHANGELOG*" "README*" "HISTORY*" "AUTHORS*" "CONTRIBUTORS*"; do \
        find /app/.venv -name "$doc_pattern" -not -path "*/prisma*" -delete 2>/dev/null || true; \
        done; \
        for pkg in setuptools wheel pkg_resources; do \
        rm -rf /app/.venv/lib/python3.13/site-packages/${pkg}* 2>/dev/null || true; \
        rm -rf /app/.venv/bin/${pkg}* 2>/dev/null || true; \
        done; \
        rm -rf /app/.venv/bin/easy_install* 2>/dev/null || true; \
        /app/.venv/bin/python -m compileall -b -q /app/tux /app/.venv/lib/python3.13/site-packages 2>/dev/null || true

USER nonroot

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
        CMD python -c "import tux.shared.config.env; print('Health check passed')" || exit 1

COPY --chmod=755 docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD []
