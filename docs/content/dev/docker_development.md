# Docker-based Development (Optional)

This method provides a containerized environment using Docker and Docker Compose. It can be useful for ensuring consistency across different machines or isolating dependencies.

However, be aware that:

* It bypasses the built-in Python hot-reloading mechanism in favor of Docker's file synchronization (`develop: watch:`), which can sometimes be less reliable or performant depending on your OS and Docker setup.
* Running commands requires executing them *inside* the container using `docker exec`.

**Docker Setup Overview:**

* [`docker-compose.yml`](https://github.com/allthingslinux/tux/blob/main/docker-compose.yml): Defines the base configuration, primarily intended for production deployments.
* [`docker-compose.dev.yml`](https://github.com/allthingslinux/tux/blob/main/docker-compose.dev.yml): Contains overrides specifically for local development. It:
  * Uses the `dev` stage from the `Dockerfile`.
  * Enables file watching/synchronization via `develop: watch:`.
* [`Dockerfile`](https://github.com/allthingslinux/tux/blob/main/Dockerfile): A multi-stage Dockerfile defining the build process for different environments (development, production).

**Starting the Docker Environment:**

1. **Build Images (First time or after Dockerfile/dependency changes):**
    Use the `tux` CLI wrapper for Docker Compose commands.

    ```bash
    poetry run tux --dev docker build
    ```

2. **Run Services:**

    ```bash
    # Start services using development overrides
    poetry run tux --dev docker up

    # Rebuild images before starting if needed
    poetry run tux --dev docker up --build

    # Start in detached mode (background)
    poetry run tux --dev docker up -d
    ```

    This uses `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up`. The `develop: watch:` feature attempts to sync code changes from your host into the running container. The container entrypoint runs `poetry run prisma generate` followed by `poetry run tux --dev start`.

**Stopping the Docker Environment:**

```bash
# Stop and remove containers, networks, etc.
poetry run tux --dev docker down
```

**Interacting with Docker Environment:**

All interactions (running the bot, database commands, quality checks) must be executed *inside* the `app` service container.

* **View Logs:**

    ```bash
    # Follow logs
    poetry run tux --dev docker logs -f app

    # Show existing logs
    poetry run tux --dev docker logs app
    ```

* **Open a Shell inside the Container:**

    ```bash
    poetry run tux --dev docker exec app bash
    ```

    From within this shell, you can run `poetry run tux ...` commands directly.

* **Database Commands (via Docker `exec`):**

    ```bash
    # Example: Push schema changes
    poetry run tux --dev docker exec app poetry run tux --dev db push

    # Example: Create migration
    poetry run tux --dev docker exec app poetry run tux --dev db migrate --name <migration-name>
    ```

* **Linting/Formatting/Type Checking (via Docker `exec`):**

    ```bash
    poetry run tux --dev docker exec app poetry run tux dev lint
    poetry run tux --dev docker exec app poetry run tux dev format
    # etc.
    ```
