import contextlib
import locale
import os
import socket
import time
import warnings
from pathlib import Path
from typing import Any, Protocol, cast

import pytest


# -----------------------------
# Pytest CLI options and markers
# -----------------------------

def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run tests marked as integration",
    )
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run tests marked as e2e",
    )
    parser.addoption(
        "--allow-network",
        action="store_true",
        default=False,
        help="Allow outbound network (unit tests block by default)",
    )


def pytest_configure(config: pytest.Config) -> None:
    # Set deterministic env early so header reflects correct values
    os.environ.setdefault("ENV", "test")
    os.environ.setdefault("PYTHONHASHSEED", "0")
    os.environ.setdefault("TZ", "UTC")

    with contextlib.suppress(Exception):
        time.tzset()  # type: ignore[attr-defined]

    os.environ.setdefault("LC_ALL", "C.UTF-8")
    os.environ.setdefault("LANG", "C.UTF-8")

    with contextlib.suppress(Exception):
        locale.setlocale(locale.LC_ALL, "C.UTF-8")

    # Markers
    config.addinivalue_line("markers", "unit: fast, isolated tests")
    config.addinivalue_line(
        "markers", "integration: tests involving multiple components or IO",
    )
    config.addinivalue_line(
        "markers", "e2e: full system tests simulating user journeys",
    )

    # Stricter warnings policy for early signal on deprecations/misuse
    warnings.filterwarnings("error", category=DeprecationWarning)
    warnings.filterwarnings("error", category=PendingDeprecationWarning)
    warnings.filterwarnings("error", category=ResourceWarning)

    # Do not fail the run due to pytest's own deprecation warnings
    warnings.filterwarnings("default", category=pytest.PytestDeprecationWarning)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    skip_integration = pytest.mark.skip(reason="use --run-integration to run")
    skip_e2e = pytest.mark.skip(reason="use --run-e2e to run")

    for item in items:
        if "integration" in item.keywords and not config.getoption("--run-integration"):
            item.add_marker(skip_integration)
        if "e2e" in item.keywords and not config.getoption("--run-e2e"):
            item.add_marker(skip_e2e)


# -----------------------------
# Global, deterministic environment
# -----------------------------

@pytest.fixture(scope="session", autouse=True)
def _session_defaults() -> None:  # pyright: ignore[reportUnusedFunction]
    # Redundant safety (already set in pytest_configure)
    os.environ.setdefault("ENV", "test")
    os.environ.setdefault("PYTHONHASHSEED", "0")

    os.environ.setdefault("TZ", "UTC")
    import contextlib

    with contextlib.suppress(Exception):
        time.tzset()  # type: ignore[attr-defined]

    os.environ.setdefault("LC_ALL", "C.UTF-8")
    os.environ.setdefault("LANG", "C.UTF-8")
    with contextlib.suppress(Exception):
        locale.setlocale(locale.LC_ALL, "C.UTF-8")


# -----------------------------
# Unit-test isolation helpers
# -----------------------------

class _HasMarker(Protocol):
    def get_closest_marker(self, name: str) -> Any: ...


@pytest.fixture(autouse=True)

def _isolate_unit_tests(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest, tmp_path: Path,
) -> None:  # pyright: ignore[reportUnusedFunction]
    """
    For tests marked as unit:
    - Isolate filesystem to a temp HOME/XDG* dirs
    - Block outbound network unless --allow-network is set
    """

    node = cast(_HasMarker, request.node)
    is_unit = node.get_closest_marker("unit") is not None
    if not is_unit:
        return

    # Filesystem isolation
    home = tmp_path / "home"
    xdg_cache = tmp_path / "xdg-cache"
    xdg_config = tmp_path / "xdg-config"
    xdg_data = tmp_path / "xdg-data"
    for p in (home, xdg_cache, xdg_config, xdg_data):
        p.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CACHE_HOME", str(xdg_cache))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_config))
    monkeypatch.setenv("XDG_DATA_HOME", str(xdg_data))

    # Optional network ban (default for unit)
    allow_network = request.config.getoption("--allow-network")
    if not allow_network:
        _disable_network(monkeypatch)


def _disable_network(monkeypatch: pytest.MonkeyPatch) -> None:
    class _PatchedSocket(socket.socket):  # type: ignore[misc]
        def connect(self, address):  # type: ignore[override]
            raise RuntimeError("Outbound network disabled in unit tests; use --allow-network to enable")

        def connect_ex(self, address):  # type: ignore[override]
            raise RuntimeError("Outbound network disabled in unit tests; use --allow-network to enable")

    monkeypatch.setattr(socket, "socket", _PatchedSocket)


# -----------------------------
# Helpful header
# -----------------------------

def pytest_report_header(config: pytest.Config) -> str:
    return (
        f"ENV={os.environ.get('ENV')} TZ={os.environ.get('TZ')} "
        f"locale={os.environ.get('LC_ALL') or os.environ.get('LANG')} "
        f"network={'allowed' if config.getoption('--allow-network') else 'blocked (unit)'}"
    )
