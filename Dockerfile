FROM python:3.12-slim

WORKDIR /app

# Install dependencies for cairo and other utilities
RUN apt-get update && \
  apt-get install -y \
  build-essential \
  curl \
  libcairo2 \
  libffi-dev \
  libgdk-pixbuf2.0-0 \
  libpango1.0-0 \
  libpangocairo-1.0-0 \
  shared-mime-info && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*


# Install Rust and Cargo
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install tealdeer and update tldr cache
RUN cargo install tealdeer
RUN tldr -u

# Copy Poetry files and install dependencies
COPY pyproject.toml poetry.lock /app/
RUN pip install poetry && \
  poetry config virtualenvs.create false && \
  poetry install --no-interaction --no-ansi

# Copy the remaining project files
COPY . /app

# Set PYTHONPATH environment variable to /app
ENV PYTHONPATH=/app

CMD ["sh", "-c", "poetry run prisma generate && poetry run python tux/main.py"]