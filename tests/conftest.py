import os
import pytest

# Global test configuration and common fixtures

@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure predictable environment for tests.

    - Set minimal required env vars
    - Force non-interactive behavior
    """
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("PYTHONHASHSEED", "0")
    # Avoid accidental network calls in unit tests by default
    monkeypatch.setenv("NO_NETWORK", "1")


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "unit: fast, isolated tests")
    config.addinivalue_line("markers", "integration: tests involving multiple components or IO")
    config.addinivalue_line("markers", "e2e: full system tests simulating user journeys")
