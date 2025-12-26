"""Test configuration for pytest."""

import atexit
import sys
from pathlib import Path
from typing import Any

import psutil
from loguru import logger

# Add src to path early for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Register fixture modules with pytest
pytest_plugins = [
    "tests.fixtures.database_fixtures",
    "tests.fixtures.data_fixtures",
    "tests.fixtures.sentry_fixtures",
]


def pytest_configure(config):
    """Configure pytest for testing.

    Sets up test environment and logging. Test markers are defined
    in pyproject.toml and do not need to be duplicated here.

    Parameters
    ----------
    config : pytest.Config
        Pytest configuration object.
    """
    # Import here to avoid circular imports during module load
    from tux.core.logging import configure_testing_logging  # noqa: PLC0415

    configure_testing_logging()


def pytest_sessionfinish(session, exitstatus):
    """Run hook after all tests finish.

    Ensures cleanup of any remaining pglite processes.

    Parameters
    ----------
    session : pytest.Session
        Pytest session object.
    exitstatus : int
        Exit status code from the test session.
    """
    cleanup_pglite_processes()


def _is_pglite_process(proc_info: dict[str, Any]) -> bool:
    """Check if a process is a pglite Node.js process.

    Parameters
    ----------
    proc_info : dict
        Process information dictionary from psutil.

    Returns
    -------
    bool
        True if the process is a pglite Node.js process.
    """
    proc_name = proc_info.get("name", "").lower()
    if proc_name not in ("node", "nodejs"):
        exe = proc_info.get("exe", "")
        if exe and "node" not in exe.lower():
            return False

    cmdline = proc_info.get("cmdline", [])
    if not cmdline:
        return False

    cmdline_str = " ".join(str(arg) for arg in cmdline).lower()
    return "pglite_manager.js" in cmdline_str


def _terminate_pglite_process(pid: int) -> bool:
    """Terminate a pglite process gracefully, then forcefully if needed.

    Parameters
    ----------
    pid : int
        Process ID to terminate.

    Returns
    -------
    bool
        True if the process was successfully terminated.
    """
    try:
        process = psutil.Process(pid)
        process.terminate()
        process.wait(timeout=2.0)
    except psutil.TimeoutExpired:
        # Process exists but didn't terminate in time, kill it
        process = psutil.Process(pid)  # Re-fetch in case original was lost
        process.kill()
        process.wait(timeout=1.0)
        return True
    except psutil.NoSuchProcess:
        return False
    else:
        return True


def cleanup_pglite_processes() -> None:
    """Clean up any orphaned pglite processes.

    Searches for and terminates Node.js processes running pglite_manager.js
    that may have been left behind from test execution.
    """
    killed_count = 0

    for proc in psutil.process_iter(attrs=["pid", "name", "cmdline", "exe"]):
        try:
            proc_info = proc.info
            if _is_pglite_process(proc_info) and _terminate_pglite_process(
                proc_info["pid"],
            ):
                killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    if killed_count > 0:
        logger.info(f"Cleaned up {killed_count} pglite process(es)")


# Register cleanup to run on exit
atexit.register(cleanup_pglite_processes)


# Test utility functions (inspired by organizex patterns)
def create_mock_guild(**overrides: Any) -> dict[str, Any]:
    """Create mock Discord guild data for testing."""
    default_data = {
        "id": 123456789012345678,
        "name": "Test Guild",
        "member_count": 100,
        "owner_id": 987654321098765432,
    }
    default_data.update(overrides)
    return default_data


def create_mock_user(**overrides: Any) -> dict[str, Any]:
    """Create mock Discord user data for testing."""
    default_data = {
        "id": 987654321098765432,
        "name": "testuser",
        "discriminator": "1234",
        "display_name": "Test User",
        "bot": False,
        "mention": "<@987654321098765432>",
    }
    default_data.update(overrides)
    return default_data


def create_mock_channel(**overrides: Any) -> dict[str, Any]:
    """Create mock Discord channel data for testing."""
    default_data = {
        "id": 876543210987654321,
        "name": "test-channel",
        "mention": "<#876543210987654321>",
        "type": "text",
    }
    default_data.update(overrides)
    return default_data


def create_mock_interaction(**overrides: Any) -> dict[str, Any]:
    """Create mock Discord interaction data for testing."""
    default_data = {
        "user": create_mock_user(),
        "guild": create_mock_guild(),
        "guild_id": 123456789012345678,
        "channel": create_mock_channel(),
        "channel_id": 876543210987654321,
        "command": {"qualified_name": "test_command"},
    }
    default_data.update(overrides)
    return default_data
