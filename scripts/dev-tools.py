#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import and initialize the custom Tux logger
import logger_setup  # noqa: F401 # pyright: ignore[reportUnusedImport]
from loguru import logger


def run_command(cmd: list[str]) -> int:
    """Run a command and return its exit code."""
    try:
        logger.info(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        logger.error(f"Command not found: {cmd[0]}")
        return 1
    else:
        return 0


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        logger.error("❌ No command specified")
        sys.exit(1)

    command = sys.argv[1]

    if command == "lint":
        logger.info("🔍 Running linting with Ruff...")
        exit_code = run_command(["uv", "run", "ruff", "check", "."])
    elif command == "lint-fix":
        logger.info("🔧 Running linting with Ruff and applying fixes...")
        exit_code = run_command(["uv", "run", "ruff", "check", "--fix", "."])
    elif command == "format":
        logger.info("✨ Formatting code with Ruff...")
        exit_code = run_command(["uv", "run", "ruff", "format", "."])
    elif command == "type-check":
        logger.info("🔍 Checking types with basedpyright...")
        exit_code = run_command(["uv", "run", "basedpyright"])
    elif command == "pre-commit":
        logger.info("✅ Running pre-commit checks...")
        exit_code = run_command(["uv", "run", "pre-commit", "run", "--all-files"])
    else:
        logger.error(f"❌ Unknown command: {command}")
        sys.exit(1)

    if exit_code == 0:
        logger.success(f"✅ {command} completed successfully")
    else:
        logger.error(f"❌ {command} failed")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
