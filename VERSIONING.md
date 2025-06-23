# Versioning

This document outlines the versioning scheme, detection logic, and release process for the Tux project. Our system is designed to provide consistent and reliable versioning across development, testing, and production environments.

## Versioning Scheme

We follow the [Semantic Versioning (SemVer)](https://semver.org/) specification for our release cycle. Version numbers are formatted as `MAJOR.MINOR.PATCH`.

- **MAJOR**: Incremented for incompatible API changes or significant architectural shifts that may require manual intervention during an upgrade (e.g., major config or database schema changes).
- **MINOR**: Incremented for new, backward-compatible functionality.
- **PATCH**: Incremented for backward-compatible bug fixes.

Release candidates can be denoted with suffixes (e.g., `1.0.0-rc1`).

## Version Detection

The application version is determined dynamically at runtime. The `tux/__init__.py` module contains a robust detection mechanism that checks multiple sources in a specific order of priority. This ensures that the version is always available, regardless of the environment.

The `version` field in `pyproject.toml` is intentionally set to a static placeholder (`0.0.0`) because the true version is resolved dynamically.

### Priority Order

The version is sourced by trying the following methods in order, stopping at the first success:

1. **`TUX_VERSION` Environment Variable**:
    - **Usage**: A runtime override.
    - **Example**: `TUX_VERSION=1.2.3-custom tux --dev start`
    - **Priority**: Highest. If set, this value is always used.

2. **`VERSION` File**:
    - **Usage**: The primary versioning method for Docker images. This file is generated during the Docker build process.
    - **Location**: Project root (`/app/VERSION` inside the container).

3. **Git Tags (`git describe`)**:
    - **Usage**: The standard for development environments where the Git history is available.
    - **Format**: It produces version strings like:
        - `1.2.3`: For a commit that is tagged directly.
        - `1.2.3-10-gabc1234`: For a commit that is 10 commits ahead of the `v1.2.3` tag.
        - `1.2.3-10-gabc1234-dirty`: If there are uncommitted changes.
    - **Note**: The leading `v` from tags (e.g., `v1.2.3`) is automatically removed.

4. **Package Metadata (`importlib.metadata`)**:
    - **Usage**: For when Tux is installed as a package from PyPI or a wheel file.
    - **Mechanism**: Reads the version from the installed package's metadata.

5. **Fallback to `"dev"`**:
    - **Usage**: A final fallback if all other methods fail, ensuring the application can always start.

## Release Cycle and Git Tagging

The release process is centered around Git tags.

1. **Create a Release**: To create a new version, create and push an annotated Git tag:

    ```sh
    # Example for a patch release
    git tag -a v1.2.3 -m "Release v1.2.3"
    git push origin v1.2.3
    ```

2. **Development Version**: Between releases, any new commits will result in a development version string (e.g., `1.2.3-5-g567def8`), indicating progress since the last tag.

## Docker Image Tagging

Our Docker build process is designed to bake the version directly into the image, ensuring traceability.

- **Build Process**: The `Dockerfile` uses a build argument (`VERSION`) to create a `VERSION` file inside the image. This file becomes the source of truth for the version within the container.

- **Building an Image**: To build a versioned image, pass the `VERSION` argument, preferably derived from `git describe`:

    ```sh
    # Recommended command to build a production image
    docker build \
      --build-arg VERSION=$(git describe --tags --always --dirty | sed 's/^v//') \
      --target production \
      -t your-registry/tux:latest .
    ```

    You can also tag the image with the specific version:

    ```sh
    # Tag with the specific version for better tracking
    VERSION_TAG=$(git describe --tags --always --dirty | sed 's/^v//')
    docker build \
      --build-arg VERSION=$VERSION_TAG \
      --target production \
      -t your-registry/tux:$VERSION_TAG \
      -t your-registry/tux:latest .
    ```

This ensures that even in a detached production environment without Git, the application reports the correct version it was built from.
