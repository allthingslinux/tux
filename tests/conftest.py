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

# Explicitly register fixture modules with pytest using pytest_plugins
# This ensures pytest discovers fixtures from these modules
pytest_plugins = [
    "tests.fixtures.database_fixtures",
    "tests.fixtures.test_data_fixtures",
    "tests.fixtures.sentry_fixtures",
]

# Track if cleanup has already been called to prevent duplicate logging
_cleanup_called: bool = False


def pytest_configure(config):
    """Configure pytest with clean settings and custom logger.

    Sets up test logging and initializes the test environment.
    Test markers are defined in pyproject.toml and do not need to be
    duplicated here.

    Parameters
    ----------
    config : pytest.Config
        Pytest configuration object.
    """
    # Import here to avoid circular imports during module load
    from tux.core.logging import configure_testing_logging  # noqa: PLC0415

    configure_testing_logging()

    # Markers are defined in pyproject.toml [tool.pytest.ini_options.markers]
    # No need to duplicate here - pytest will read them from pyproject.toml


def pytest_sessionfinish(session, exitstatus):
    """Run hook after all tests finish.

    This hook runs after the entire test session completes and ensures
    any remaining pglite_manager.js processes are killed.

    When running tests in parallel with pytest-xdist, pglite processes
    may be left behind by worker processes. This cleanup ensures all
    processes are terminated at the end of the test session.

    Parameters
    ----------
    session : pytest.Session
        Pytest session object.
    exitstatus : int
        Exit status code from the test session.
    """
    cleanup_pglite_processes()


def _is_pglite_process(proc_info: dict[str, Any]) -> bool:
    """Check if a process is a pglite_manager.js Node.js process.

    Parameters
    ----------
    proc_info : dict[str, Any]
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

    cmdline = proc_info.get("cmdline")
    if not cmdline:
        return False

    cmdline_str = " ".join(str(arg) for arg in cmdline).lower()
    return "pglite_manager.js" in cmdline_str or "pglite" in cmdline_str


def _terminate_pglite_process(pid: int) -> bool:
    """Terminate a pglite process gracefully or forcefully.

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
    except psutil.NoSuchProcess:
        logger.debug(f"Process {pid} no longer exists")
        return False

    try:
        process.terminate()
        process.wait(timeout=2)
        logger.info(f"Gracefully terminated pglite process (PID: {pid})")
    except psutil.TimeoutExpired:
        logger.warning(f"Process {pid} didn't terminate, forcing kill")
        process.kill()
        process.wait(timeout=1)
        logger.info(f"Force killed pglite process (PID: {pid})")
    except psutil.NoSuchProcess:
        logger.debug(f"Process {pid} already terminated")
        return False

    return True


def cleanup_pglite_processes() -> None:
    """Kill any remaining pglite_manager.js Node.js processes.

    Searches for and terminates any Node.js processes running
    pglite_manager.js that may have been left behind from test execution,
    especially when tests are interrupted or fail.

    Uses psutil for process management. Attempts graceful termination
    (SIGTERM) before force killing (SIGKILL).

    Notes
    -----
    This function is registered as an atexit handler as a safety net,
    ensuring cleanup even if pytest doesn't exit normally. The function
    is idempotent and will only log at debug level if called multiple times
    with no processes found.
    """
    # Use module-level variable to track if cleanup was already called
    # This prevents duplicate logging when called from both pytest_sessionfinish
    # and atexit.register
    global _cleanup_called  # noqa: PLW0603

    # If cleanup was already called and we're being called again (likely from atexit),
    # do a quick silent check first
    if _cleanup_called:
        # Quick silent check - only proceed if we find something
        for proc in psutil.process_iter(attrs=["pid", "name", "cmdline", "exe"]):
            try:
                if _is_pglite_process(proc.info):
                    # Found new processes, continue with full cleanup
                    break
            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
                Exception,
            ):
                continue
        else:
            # No processes found, skip silently
            return

    _cleanup_called = True
    logger.info("Starting pglite process cleanup...")
    killed_count = 0
    found_pids: list[int] = []

    # Find all processes - use attrs parameter to get full process info
    for proc in psutil.process_iter(attrs=["pid", "name", "cmdline", "exe"]):
        proc_info: dict[str, Any] | None = None
        try:
            proc_info = proc.info

            if not _is_pglite_process(proc_info):
                continue

            pid = proc_info["pid"]
            found_pids.append(pid)
            logger.warning(
                f"Found orphaned pglite process (PID: {pid}): {' '.join(str(arg) for arg in proc_info.get('cmdline', []))}",
            )

            if _terminate_pglite_process(pid):
                killed_count += 1

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # Process may have terminated or we don't have permission
            continue
        except Exception as e:
            pid = proc_info.get("pid", "unknown") if proc_info else "unknown"
            logger.warning(f"Error checking process {pid}: {e}")
            continue

    if found_pids:
        logger.info(
            f"Found {len(found_pids)} pglite process(es), cleaned up {killed_count}",
        )
    else:
        logger.debug("No orphaned pglite processes found")


# Register cleanup to run on exit as well (safety net)
atexit.register(cleanup_pglite_processes)
