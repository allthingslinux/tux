#!/usr/bin/env python3

import subprocess
import sys
import webbrowser
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from typing import TypedDict

from loguru import logger


class CommandConfig(TypedDict):
    """Type definition for command configuration."""

    description: str
    cmd: list[str]


def build_coverage_command(args: list[str]) -> list[str]:
    """Build coverage command with various options."""
    # Add coverage path
    specific = next((args[i + 1] for i, arg in enumerate(args) if arg == "--specific" and i + 1 < len(args)), None)
    cmd = ["uv", "run", "pytest", f"--cov={specific}" if specific else "--cov=tux"]

    # Add coverage report format
    if "--quick" in args:
        cmd.append("--cov-report=")
    else:
        format_val = None
        if "--format" in args:
            format_idx = args.index("--format")
            if format_idx + 1 < len(args):
                format_val = args[format_idx + 1]

        match format_val:
            case "html":
                cmd.append("--cov-report=html")
            case "xml":
                xml_file = next(
                    (args[xml_idx + 1] for xml_idx in [args.index("--xml-file")] if xml_idx + 1 < len(args)),
                    "coverage.xml",
                )
                cmd.append(f"--cov-report=xml:{xml_file}")
            case "json":
                cmd.append("--cov-report=json")
            case _:
                cmd.append("--cov-report=term-missing")

    # Add fail-under if specified
    if "--fail-under" in args:
        fail_idx = args.index("--fail-under")
        if fail_idx + 1 < len(args):
            fail_val = args[fail_idx + 1]
            cmd.extend(["--cov-fail-under", fail_val])

    # Add randomization
    cmd.extend(["--randomly-seed=last"])

    return cmd


def open_coverage_browser(args: list[str]) -> None:
    """Open coverage report in browser if requested."""
    if "--open-browser" in args and "--format" in args:
        format_idx = args.index("--format")
        if format_idx + 1 < len(args) and args[format_idx + 1] == "html":
            html_report_path = Path("htmlcov/index.html")
            if html_report_path.exists():
                logger.info("🌐 Opening HTML coverage report in browser...")
                webbrowser.open(f"file://{html_report_path.resolve()}")


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
    args = sys.argv[2:]

    # Command configurations
    commands: dict[str, CommandConfig] = {
        "run": {
            "description": "🧪 Running tests with coverage and enhanced output...",
            "cmd": ["uv", "run", "pytest", "--cov=tux", "--cov-report=term-missing", "--randomly-seed=last"],
        },
        "quick": {
            "description": "⚡ Running tests without coverage (faster)...",
            "cmd": ["uv", "run", "pytest", "--no-cov", "--randomly-seed=last"],
        },
        "plain": {
            "description": "📝 Running tests with plain output...",
            "cmd": [
                "uv",
                "run",
                "pytest",
                "-p",
                "no:sugar",
                "--cov=tux",
                "--cov-report=term-missing",
                "--randomly-seed=last",
            ],
        },
        "parallel": {
            "description": "🔄 Running tests in parallel...",
            "cmd": [
                "uv",
                "run",
                "pytest",
                "--cov=tux",
                "--cov-report=term-missing",
                "-n",
                "auto",
                "--randomly-seed=last",
            ],
        },
        "html": {
            "description": "🌐 Running tests and generating HTML report...",
            "cmd": [
                "uv",
                "run",
                "pytest",
                "--cov=tux",
                "--cov-report=html",
                "--html=reports/test_report.html",
                "--self-contained-html",
                "--randomly-seed=last",
            ],
        },
        "benchmark": {
            "description": "📊 Running benchmark tests...",
            "cmd": ["uv", "run", "pytest", "--benchmark-only", "--benchmark-sort=mean"],
        },
    }

    if command in commands:
        config = commands[command]
        logger.info(config["description"])
        exit_code = run_command(config["cmd"])
    elif command == "coverage":
        logger.info("📈 Generating comprehensive coverage reports...")
        cmd = build_coverage_command(args)
        exit_code = run_command(cmd)
        if exit_code == 0:
            open_coverage_browser(args)
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
