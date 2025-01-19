FROM python:3.12-slim AS builder

# Set the working directory
WORKDIR /app

# Install dependencies for building and runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libcairo2 \
    libffi-dev \
    libgdk-pixbuf2.0-0 \
    libpango1.0-0 \
    libpangocairo-1.0-0 \
    shared-mime-info && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Rust and Cargo
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    echo 'export PATH="/root/.cargo/bin:$PATH"' >> /etc/profile.d/cargo.sh

# Install tealdeer and update tldr cache
ENV PATH="/root/.cargo/bin:${PATH}"
RUN cargo install tealdeer && tldr -u


# Copy Poetry files and install dependencies
COPY pyproject.toml poetry.lock /app/
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Copy the remaining project files
COPY . /app

# Create a non-root user and switch to it
RUN useradd -m appuser
USER appuser

# Set PYTHONPATH environment variable to /app
ENV PYTHONPATH=/app

# Command to run the application
CMD ["sh", "-c", "ls && poetry run prisma py fetch && poetry run prisma generate && poetry run python tux/main.py"]
