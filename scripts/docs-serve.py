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


def find_mkdocs_config() -> str:
    """Find the mkdocs.yml configuration file."""
    current_dir = Path.cwd()

    # Check if we're in the docs directory
    if (current_dir / "mkdocs.yml").exists():
        return "mkdocs.yml"

    # Check if we're in the root repo with docs subdirectory
    if (current_dir / "docs" / "mkdocs.yml").exists():
        return "docs/mkdocs.yml"

    logger.error("Can't find mkdocs.yml file. Please run from the project root or docs directory.")
    return ""


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

    if command == "serve":
        logger.info("📚 Serving documentation locally...")
        if mkdocs_path := find_mkdocs_config():
            exit_code = run_command(["uv", "run", "mkdocs", "serve", "--dirty", "-f", mkdocs_path])
        else:
            exit_code = 1

    elif command == "build":
        logger.info("🏗️  Building documentation site...")
        if mkdocs_path := find_mkdocs_config():
            exit_code = run_command(["uv", "run", "mkdocs", "build", "-f", mkdocs_path])
        else:
            exit_code = 1

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
