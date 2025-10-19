# Versioning

This document outlines the versioning scheme, detection logic, and release process for the Tux project. Our system is designed to provide consistent and reliable versioning across development, testing, and production environments.

## Versioning Scheme

We follow the [Semantic Versioning (SemVer)](https://semver.org/) specification for our release cycle. Version numbers are formatted as `MAJOR.MINOR.PATCH`.

- **MAJOR**: Incremented for incompatible API changes or significant architectural shifts that may require manual intervention during an upgrade (e.g., major config or database schema changes).
- **MINOR**: Incremented for new, backward-compatible functionality.
- **PATCH**: Incremented for backward-compatible bug fixes.

Release candidates can be denoted with suffixes (e.g., `1.0.0-rc.1`).

## Unified Version System

The Tux project uses a **unified version system** (`src/tux/shared/version.py`) that provides a single source of truth for all version-related functionality. This system is designed to be:

- **DRY (Don't Repeat Yourself)**: All version logic is centralized in one module
- **Seamless**: Works consistently across all environments (development, Docker, CI/CD)
- **Professional**: Robust error handling, caching, and type safety
- **Testable**: Clean, focused tests without complex mocking

### Key Features

- **Version Detection**: Automatic detection from multiple sources with clear priority
- **Semantic Versioning**: Full semver validation and comparison support
- **Caching**: Version is detected once and cached for performance
- **Build Information**: Comprehensive build metadata including git SHA and Python version
- **Error Handling**: Graceful fallbacks ensure the application always starts

## Version Detection

The application version is determined dynamically at runtime using the unified version system. The `tux/__init__.py` module imports from `tux.shared.version` and exposes the detected version as `__version__`.

The `version` field in `pyproject.toml` is intentionally set to a static placeholder (`0.0.0`) because the true version is resolved dynamically.

### Priority Order

The version is sourced by trying the following methods in order, stopping at the first success:

1. **`TUX_VERSION` Environment Variable**:
    - **Usage**: A runtime override for testing, deployment, or CI/CD scenarios.
    - **Example**: `TUX_VERSION=1.2.3-custom tux --dev start`
    - **Priority**: Highest. If set, this value is always used.
    - **Use Cases**:
      - Testing with specific versions
      - Production deployments with custom versioning
      - CI/CD pipelines that need to override detected versions

2. **`VERSION` File**:
    - **Usage**: The primary versioning method for Docker images and production deployments.
    - **Location**: Project root (`/app/VERSION` inside containers).
    - **Creation**: Generated during Docker build process or manually created for releases.
    - **Use Cases**:
      - Docker containers where git history may not be available
      - Release builds where exact version control is required
      - Environments where git operations are restricted

3. **Git Tags (`git describe`)**:
    - **Usage**: The standard for development environments where the Git history is available.
    - **Format**: Produces version strings like:
        - `1.2.3`: For a commit that is tagged directly.
        - `1.2.3-10-gabc1234`: For a commit that is 10 commits ahead of the `v1.2.3` tag.
        - `1.2.3-10-gabc1234-dirty`: If there are uncommitted changes (cleaned for semver compatibility).
    - **Note**: The leading `v` from tags (e.g., `v1.2.3`) is automatically removed.
    - **Use Cases**:
      - Development environments with full git history
      - Local testing and development
      - CI/CD environments with git access

4. **Fallback to `"dev"`**:
    - **Usage**: A final fallback if all other methods fail, ensuring the application can always start.
    - **Use Cases**:
      - Environments without git access
      - Missing VERSION files
      - Fallback when all detection methods fail

### Version System API

The unified version system provides several utility functions:

```python
from tux.shared.version import (
    get_version,           # Get current version
    is_semantic_version,   # Check if version is valid semver
    compare_versions,      # Compare two semantic versions
    get_version_info,      # Get detailed version components
    get_build_info,        # Get build metadata
)
```

## Release Cycle and Git Tagging

The release process is centered around Git tags and follows semantic versioning principles.

1. **Create a Release**: To create a new version, create and push an annotated Git tag:

    ```sh
    # Example for a patch release
    git tag -a v1.2.3 -m "Release v1.2.3"
    git push origin v1.2.3
    ```

2. **Development Version**: Between releases, any new commits will result in a development version string (e.g., `1.2.3-5-g567def8`), indicating progress since the last tag.

3. **Pre-release Versions**: Use proper semver pre-release identifiers:

    ```sh
    # Release candidates
    git tag -a v1.2.3-rc.1 -m "Release candidate v1.2.3-rc.1"
    
    # Beta versions
    git tag -a v1.2.3-beta.1 -m "Beta v1.2.3-beta.1"
    
    # Alpha versions
    git tag -a v1.2.3-alpha.1 -m "Alpha v1.2.3-alpha.1"
    ```

## Docker Image Tagging

Our Docker build process is designed to bake the version directly into the image, ensuring traceability and consistency with the unified version system.

### Build Process

The `Containerfile` uses build arguments to create a `VERSION` file inside the image:

```dockerfile
ARG VERSION=""
ARG GIT_SHA=""
ARG BUILD_DATE=""

# Generate version file using build args with fallback
RUN set -eux; \
    if [ -n "$VERSION" ]; then \
        echo "$VERSION" > /app/VERSION; \
    else \
        echo "dev" > /app/VERSION; \
    fi
```

### Building Versioned Images

To build a versioned image, pass the `VERSION` argument:

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

### GitHub Actions Integration

Our GitHub Actions workflows automatically handle version generation:

- **PR Builds**: Generate versions like `pr-123-abc1234`
- **Release Builds**: Use the git tag version (e.g., `1.2.3`)
- **Docker Builds**: Pass the generated version as build arguments

This ensures that even in a detached production environment without Git, the application reports the correct version it was built from.

## Testing the Version System

The version system includes comprehensive tests (`tests/unit/test_version_system.py`) that cover:

- Version detection from all sources
- Priority order validation
- Edge cases and error handling
- Semantic version validation
- Build information generation
- Integration with other components

Run the tests with:

```sh
uv run pytest tests/unit/test_version_system.py -v
```

## Troubleshooting

### Common Issues

1. **Version shows as "dev"**:
   - Check if you're in a git repository
   - Verify the VERSION file exists and contains a valid version
   - Ensure TUX_VERSION environment variable is not set to an empty value

2. **Git describe fails**:
   - Ensure you have at least one git tag
   - Check git repository integrity
   - Verify git is available in the environment

3. **Docker version mismatch**:
   - Ensure VERSION build arg is passed correctly
   - Check that the VERSION file is created in the container
   - Verify the Containerfile version generation logic

### Debugging

You can debug version detection by checking the version system directly:

```python
from tux.shared.version import VersionManager

manager = VersionManager()
print(f"Detected version: {manager.get_version()}")
print(f"Build info: {manager.get_build_info()}")
print(f"Is semantic version: {manager.is_semantic_version()}")
```

This unified version system ensures consistent, reliable versioning across all environments while maintaining the flexibility needed for different deployment scenarios.
