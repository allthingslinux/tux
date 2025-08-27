#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from loguru import logger


def get_compose_base_cmd() -> list[str]:
    """Get the base docker compose command with appropriate -f flags."""
    base = ["docker", "compose", "-f", "docker-compose.yml"]
    if os.getenv("MODE", "dev") == "dev":
        base.extend(["-f", "docker-compose.dev.yml"])
    return base


def run_command(cmd: list[str], env: dict[str, str] | None = None) -> int:
    """Run a command and return its exit code."""
    try:
        logger.info(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, env=env)
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        logger.error(f"Command not found: {cmd[0]}")
        return 1
    else:
        return 0


def run_simple_command(command: str, compose_args: list[str], log_message: str) -> int:
    """Run a simple docker compose command with logging."""
    logger.info(log_message)
    cmd = [*get_compose_base_cmd(), command, *compose_args]
    return run_command(cmd)


def main():  # noqa: PLR0912, PLR0915  # sourcery skip: low-code-quality
    """Main entry point."""
    if len(sys.argv) < 2:
        logger.error("❌ No command specified")
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "build":
        logger.info("🐳 Building Docker images...")
        cmd = [*get_compose_base_cmd(), "build"]
        if "--no-cache" in args:
            cmd.append("--no-cache")
        if "--target" in args:
            target_idx = args.index("--target")
            if target_idx + 1 < len(args):
                cmd.extend(["--target", args[target_idx + 1]])
        exit_code = run_command(cmd)

    elif command == "up":
        logger.info("🚀 Starting Docker services...")
        cmd = [*get_compose_base_cmd(), "up"]
        if "-d" in args or "--detach" in args:
            cmd.append("-d")
        if "--build" in args:
            cmd.append("--build")
        if "--watch" in args:
            cmd.append("--watch")
        exit_code = run_command(cmd)

    elif command == "down":
        logger.info("🛑 Stopping Docker services...")
        cmd = [*get_compose_base_cmd(), "down"]
        if "-v" in args or "--volumes" in args:
            cmd.append("--volumes")
        if "--remove-orphans" in args:
            cmd.append("--remove-orphans")
        exit_code = run_command(cmd)

    elif command == "logs":
        logger.info("📋 Showing Docker service logs...")
        cmd = [*get_compose_base_cmd(), "logs"]
        if "-f" in args or "--follow" in args:
            cmd.append("-f")
        if "-n" in args or "--tail" in args:
            tail_idx = args.index("-n") if "-n" in args else args.index("--tail")
            if tail_idx + 1 < len(args):
                cmd.extend(["-n", args[tail_idx + 1]])
        # Add service name if provided
        for i, arg in enumerate(args):
            if not arg.startswith("-") and i > 0:
                cmd.append(arg)
                break
        exit_code = run_command(cmd)

    elif command == "ps":
        exit_code = run_simple_command("ps", [], "📊 Listing running Docker containers...")

    elif command == "exec":
        logger.info("🔧 Executing command in container...")
        if len(args) < 1:
            logger.error("❌ Service name required for exec command")
            sys.exit(1)
        service = args[0]
        exec_args = args[1:] if len(args) > 1 else ["bash"]
        cmd = [*get_compose_base_cmd(), "exec", service, *exec_args]
        exit_code = run_command(cmd)

    elif command == "shell":
        logger.info("🐚 Opening shell in container...")
        service = args[0] if args else "tux"
        cmd = [*get_compose_base_cmd(), "exec", service, "bash"]
        exit_code = run_command(cmd)

    elif command == "restart":
        logger.info("🔄 Restarting Docker services...")
        service = args[0] if args else "tux"
        cmd = [*get_compose_base_cmd(), "restart", service]
        exit_code = run_command(cmd)

    elif command == "health":
        exit_code = run_simple_command("ps", [], "🏥 Checking container health status...")

    elif command == "test":
        logger.info("🧪 Running Docker tests...")
        # Map flags to test types and corresponding scripts
        test_type = "comprehensive"  # default
        if "--quick" in args:
            test_type = "quick"
        elif "--comprehensive" in args:
            test_type = "comprehensive"
        elif "--perf" in args:
            test_type = "perf"
        elif "--security" in args:
            test_type = "security"

        # Map test types to script names
        script_map = {
            "quick": "docker-test-quick.py",
            "perf": "docker-test-standard.py",
            "comprehensive": "docker-test-comprehensive.py",
        }

        if test_type in script_map:
            script_path = Path.cwd() / "scripts" / script_map[test_type]
            if script_path.exists():
                cmd = ["uv", "run", "python", str(script_path)]
                exit_code = run_command(cmd)
            else:
                logger.error(f"❌ Test script {script_map[test_type]} not found")
                exit_code = 1
        elif test_type == "security":
            logger.warning("⚠️  Security tests not fully implemented yet")
            exit_code = 0
        else:
            logger.error(f"❌ Unknown test type: {test_type}")
            exit_code = 1

    elif command == "cleanup":
        logger.info("🧹 Cleaning up Docker resources...")
        cleanup_script = Path.cwd() / "scripts" / "docker-cleanup.py"
        if cleanup_script.exists():
            # Parse cleanup flags
            cleanup_args: list[str] = []
            if "--volumes" in args:
                cleanup_args.append("--volumes")
            if "--force" in args:
                cleanup_args.append("--force")
            if "--dry-run" in args:
                cleanup_args.append("--dry-run")

            cmd: list[str] = ["uv", "run", "python", str(cleanup_script), *cleanup_args]
            exit_code = run_command(cmd)
        else:
            logger.error("❌ Docker cleanup script not found")
            exit_code = 1

    elif command == "config":
        exit_code = run_simple_command("config", [], "⚙️  Validating Docker Compose configuration...")

    elif command == "pull":
        exit_code = run_simple_command("pull", [], "⬇️  Pulling latest Docker images...")

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
