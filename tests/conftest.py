"""Global pytest configuration and fixtures."""

import subprocess

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (may take several minutes)")
    config.addinivalue_line("markers", "docker: marks tests that require Docker to be running")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


@pytest.fixture(scope="session")
def docker_available() -> bool:
    """Check if Docker is available for testing."""
    try:
        subprocess.run(["docker", "version"], capture_output=True, text=True, timeout=10, check=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False
    else:
        return True


@pytest.fixture(autouse=True)
def skip_if_no_docker(request: pytest.FixtureRequest, docker_available: bool) -> None:
    """Skip tests that require Docker if Docker is not available."""

    # Make type-checker happy
    node = getattr(request, "node", None)
    get_marker = getattr(node, "get_closest_marker", None)

    if callable(get_marker) and get_marker("docker") and not docker_available:
        pytest.skip("Docker is not available")
