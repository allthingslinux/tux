FROM python:3.12-slim

WORKDIR /app

# Install dependencies for cairo and other utilities
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Poetry files and install dependencies
COPY pyproject.toml poetry.lock /app/
RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy the remaining project files
COPY . /app

RUN mkdir -p /app/.cache/prisma && chmod +x /app/.cache/prisma

# Set PYTHONPATH environment variable to /app
ENV PYTHONPATH=/app

# Removing entrypoint and using CMD instead for better debugging
CMD ["sh", "-c", "ls && poetry run prisma generate && poetry run python tux/main.py"]
