# Install Poetry
install-poetry:
    curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
install:
    poetry install && poetry run pre-commit install && poetry run prisma generate

# Prisma-related commands
generate-prisma:
    poetry run prisma generate

migrate-prisma:
    poetry run prisma migrate dev

# Run the bot
run:
    poetry run python tux/main.py

# Lint the code using ruff
lint:
    poetry run ruff check .

# Fix linting issues
lint-fix:
    poetry run ruff --fix .

# Type-check the code using pyright
check-types:
    poetry run pyright

# Environment setup
setup-env:
    @echo "Setting up environment..."
    just install-poetry
    just install
    just lint-fix
    just generate-prisma
    # just prisma-migrate

start-docker:
    docker compose up --build -d

stop-docker:
    docker compose down
