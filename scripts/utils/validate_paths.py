#!/usr/bin/env python3

"""Validate VS Code and Python path configuration for Tux development.

This script checks:
- Python interpreter location
- PYTHONPATH configuration
- Module import paths
- Test discovery
- VS Code settings alignment
"""

# ruff: noqa: T201

import json
import subprocess
import sys
from pathlib import Path

# ANSI colors
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{RED}❌ {text}{RESET}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{YELLOW}⚠️  {text}{RESET}")


def check_python_interpreter() -> bool:
    """Check Python interpreter location."""
    print_header("Python Interpreter")
    python_exe = sys.executable
    print(f"Python executable: {python_exe}")

    # Check if it's in .venv
    if ".venv" in python_exe:
        print_success("Python interpreter is in .venv (correct for uv)")
        return True
    print_warning(f"Python interpreter is not in .venv: {python_exe}")
    return False


def check_python_path() -> bool:
    """Check Python path configuration."""
    print_header("Python Path (sys.path)")

    workspace_root = Path.cwd()
    src_path = workspace_root / "src"

    paths_found = {
        "workspace_root": False,
        "src": False,
    }

    print("Checking sys.path entries:")
    for i, path in enumerate(sys.path, 1):
        path_obj = Path(path).resolve()
        print(f"  {i}. {path_obj}")

        if path_obj == workspace_root.resolve():
            paths_found["workspace_root"] = True
            print(f"     {GREEN}← Workspace root (good){RESET}")

        if path_obj == src_path.resolve():
            paths_found["src"] = True
            print(f"     {GREEN}← src directory (required for imports){RESET}")

    print()
    all_good = True

    if paths_found["src"]:
        print_success("src/ directory is in Python path")
    else:
        print_error("src/ directory is NOT in Python path")
        print(f"   Expected: {src_path.resolve()}")
        all_good = False

    if paths_found["workspace_root"]:
        print_success("Workspace root is in Python path")
    else:
        print_warning("Workspace root is not in Python path (may be OK)")

    return all_good


def check_module_imports() -> bool:
    """Check if core modules can be imported."""
    print_header("Module Imports")

    # Ensure src/ is prioritized in path (like VS Code does)
    workspace_root = Path.cwd()
    src_path = workspace_root / "src"
    if str(src_path.resolve()) not in [str(Path(p).resolve()) for p in sys.path[:3]]:
        # Insert src/ at the beginning if not already there early
        sys.path.insert(0, str(src_path.resolve()))

    test_imports = [
        ("tux.core.logging", "Core logging module"),
        ("tux.core.bot", "Bot core"),
        ("tux.database.service", "Database service"),
    ]

    all_good = True
    for module_name, description in test_imports:
        try:
            __import__(module_name)
            print_success(f"{module_name} - {description}")
        except ImportError as e:
            print_error(f"{module_name} - {description}")
            print(f"   Error: {e}")
            all_good = False

    # Test that tux package can be imported (from src/tux/)
    try:
        import tux  # noqa: PLC0415
    except ImportError as e:
        print_error(f"tux package import failed: {e}")
        all_good = False
    else:
        tux_path = Path(tux.__file__).parent
        if "src/tux" in str(tux_path):
            print_success(f"tux package found at: {tux_path}")
        else:
            print_warning(f"tux package found at unexpected location: {tux_path}")

    return all_good


def check_vscode_settings() -> bool:
    """Check VS Code settings alignment."""
    print_header("VS Code Settings Validation")

    workspace_root = Path.cwd()
    vscode_settings = workspace_root / ".vscode" / "settings.json"

    if not vscode_settings.exists():
        print_error(".vscode/settings.json not found")
        return False

    print_success(".vscode/settings.json exists")

    # Read and check key settings
    try:
        settings = json.loads(vscode_settings.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print_error(f"Failed to parse settings.json: {e}")
        return False

    checks: list[bool] = []

    # Check PYTHONPATH in terminal env
    terminal_env = settings.get("terminal.integrated.env.linux", {})
    pythonpath = terminal_env.get("PYTHONPATH", "")
    expected_pythonpath = "${workspaceFolder}/src"

    if pythonpath == expected_pythonpath:
        print_success(f"PYTHONPATH in terminal env: {pythonpath}")
        checks.append(True)
    else:
        print_error("PYTHONPATH mismatch")
        print(f"   Found: {pythonpath}")
        print(f"   Expected: {expected_pythonpath}")
        checks.append(False)

    # Check pytest args
    pytest_args = settings.get("python.testing.pytestArgs", [])
    if pytest_args == ["tests"]:
        print_success(f"pytest args: {pytest_args}")
        checks.append(True)
    else:
        print_warning(f"pytest args: {pytest_args} (expected: ['tests'])")
        checks.append(False)

    # Check terminal CWD
    terminal_cwd = settings.get("terminal.integrated.cwd", "")
    if terminal_cwd == "${workspaceFolder}":
        print_success(f"Terminal CWD: {terminal_cwd}")
        checks.append(True)
    else:
        print_warning(f"Terminal CWD: {terminal_cwd} (expected: ${{workspaceFolder}})")
        checks.append(False)

    return all(checks)


def check_pytest_config() -> bool:
    """Check pytest configuration."""
    print_header("Pytest Configuration")

    try:
        import pytest  # noqa: PLC0415

        version = getattr(pytest, "__version__", "unknown")
        print_success(f"pytest is installed: {version}")
    except ImportError:
        print_error("pytest is not installed")
        return False

    # Try to collect tests
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "--collect-only", "-q"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ) as e:
        print_warning(f"Could not test pytest discovery: {e}")
        return False
    else:
        if result.returncode == 0 or "test session starts" in result.stdout:
            print_success("Pytest can discover tests")
            return True
        print_warning("Pytest test discovery had issues")
        print(f"   Output: {result.stdout[:200]}")
        return False


def check_uv_integration() -> bool:
    """Check uv-specific integration."""
    print_header("UV Integration")

    workspace_root = Path.cwd()
    venv_path = workspace_root / ".venv"

    if venv_path.exists():
        print_success(f".venv exists at: {venv_path}")
    else:
        print_warning(".venv does not exist (run 'uv sync' first)")
        return False

    # Check if uv.lock exists
    uv_lock = workspace_root / "uv.lock"
    if uv_lock.exists():
        print_success("uv.lock exists")
    else:
        print_warning("uv.lock does not exist")

    # Check Python interpreter in .venv
    venv_python = venv_path / "bin" / "python3"
    if venv_python.exists():
        print_success(f"Python interpreter found in .venv: {venv_python}")
        return True
    print_error("Python interpreter not found in .venv")
    return False


def main() -> int:
    """Run all validation checks."""
    print(f"\n{BOLD}{BLUE}VS Code & Python Path Validation{RESET}")
    print(f"Workspace: {Path.cwd()}\n")

    results = {
        "Python Interpreter": check_python_interpreter(),
        "Python Path": check_python_path(),
        "Module Imports": check_module_imports(),
        "VS Code Settings": check_vscode_settings(),
        "Pytest Configuration": check_pytest_config(),
        "UV Integration": check_uv_integration(),
    }

    print_header("Summary")

    all_passed = True
    for check_name, passed in results.items():
        if passed:
            print_success(f"{check_name}")
        else:
            print_error(f"{check_name}")
            all_passed = False

    print()
    if all_passed:
        print_success("All checks passed! Your configuration is correct.")
        return 0
    print_error("Some checks failed. Please review the output above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
