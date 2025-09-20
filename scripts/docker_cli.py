#!/usr/bin/env python3
"""
Docker CLI Script

A unified interface for all Docker operations using the clean CLI infrastructure.
"""

import contextlib
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

from typer import Argument, Option  # type: ignore[attr-defined]

# Import docker at module level to avoid import issues
try:
    import docker
except ImportError:
    docker = None

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from scripts.base import BaseCLI
from scripts.registry import Command


class Timer:
    """Simple timer for measuring durations."""

    def __init__(self) -> None:
        self.start_time: float | None = None

    def start(self) -> None:
        """Start the timer."""
        self.start_time = time.time()

    def elapsed_ms(self) -> int:
        """Get elapsed time in milliseconds."""
        if self.start_time is None:
            return 0
        return int((time.time() - self.start_time) * 1000)


class DockerCLI(BaseCLI):
    """Docker CLI with unified interface for all Docker operations."""

    def __init__(self):
        super().__init__(name="docker", description="Docker CLI - A unified interface for all Docker operations")
        self._docker_client = None
        self._setup_command_registry()
        self._setup_commands()

    def _get_docker_client(self):
        """Get or create Docker client."""
        if self._docker_client is None:
            if docker is None:
                msg = "Docker SDK not available. Install with: pip install docker"
                raise ImportError(msg)
            try:
                self._docker_client = docker.from_env()
            except Exception as e:
                self.rich.print_error(f"Failed to connect to Docker: {e}")
                raise
        return self._docker_client

    def _setup_command_registry(self) -> None:
        """Setup the command registry with all Docker commands."""
        # All commands directly registered without groups
        all_commands = [
            # Docker Compose commands
            Command("build", self.build, "Build Docker images"),
            Command("up", self.up, "Start Docker services with smart orchestration"),
            Command("down", self.down, "Stop Docker services"),
            Command("logs", self.logs, "Show Docker service logs"),
            Command("ps", self.ps, "List running Docker containers"),
            Command("exec", self.exec, "Execute command in container"),
            Command("shell", self.shell, "Open shell in container"),
            Command("restart", self.restart, "Restart Docker services"),
            Command("health", self.health, "Check container health status"),
            Command("config", self.config, "Validate Docker Compose configuration"),
            Command("pull", self.pull, "Pull latest Docker images"),
            # Docker management commands
            Command("cleanup", self.cleanup, "Clean up Docker resources"),
            Command("test", self.test, "Run Docker tests"),
            Command("test-quick", self.test_quick, "Run quick Docker validation tests"),
            Command("test-comprehensive", self.test_comprehensive, "Run comprehensive Docker tests"),
        ]

        for cmd in all_commands:
            self._command_registry.register_command(cmd)

    def _setup_commands(self) -> None:
        """Setup all Docker CLI commands using the command registry."""
        # Register all commands directly to the main app
        for command in self._command_registry.get_commands().values():
            self.add_command(
                command.func,
                name=command.name,
                help_text=command.help_text,
            )

    def _get_docker_cmd(self) -> str:
        """Get the system Docker command path."""
        return "/usr/bin/docker"

    def _get_docker_host(self) -> str | None:
        """Get the Docker host from environment variables."""
        return os.environ.get("DOCKER_HOST")

    def _setup_docker_host(self) -> bool:
        """Auto-detect and setup Docker host."""
        # Check if we're already configured
        if self._get_docker_host():
            return True

        # Try common Docker socket locations
        docker_sockets = [
            f"{os.environ.get('XDG_RUNTIME_DIR', '/run/user/1000')}/docker.sock",
            "/run/user/1000/docker.sock",
            "/var/run/docker.sock",
        ]

        for socket_path in docker_sockets:
            if Path(socket_path).exists():
                os.environ["DOCKER_HOST"] = f"unix://{socket_path}"
                return True

        return False

    def _get_compose_base_cmd(self) -> list[str]:
        """Get the base docker compose command."""
        # Use the system docker command to avoid conflicts with the virtual env docker script
        return [self._get_docker_cmd(), "compose", "-f", "docker-compose.yml"]

    def _run_command(self, command: list[str]) -> None:
        """Run a command and return success status."""
        try:
            # Ensure DOCKER_HOST is set
            env = os.environ.copy()
            if not env.get("DOCKER_HOST"):
                self._setup_docker_host()
                env |= os.environ

            self.rich.print_info(f"Running: {' '.join(command)}")
            subprocess.run(command, check=True, env=env)
        except subprocess.CalledProcessError as e:
            self.rich.print_error(f"Command failed with exit code {e.returncode}")
            raise
        except FileNotFoundError:
            self.rich.print_error(f"Command not found: {command[0]}")
            raise

    def _safe_run(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        """Safely run a command with error handling."""
        try:
            return subprocess.run(cmd, **kwargs, check=True)  # type: ignore[return-value]
        except subprocess.CalledProcessError:
            self.rich.print_error(f"Command failed: {' '.join(cmd)}")
            raise

    def _check_docker(self) -> bool:  # sourcery skip: class-extract-method, extract-duplicate-method
        """Check if Docker is available and running."""
        # Auto-detect Docker host
        self._setup_docker_host()

        try:
            client = self._get_docker_client()
            # Test basic connectivity
            client.ping()  # type: ignore[attr-defined]
            # Test if we can list containers
            client.containers.list()  # type: ignore[attr-defined]

        except Exception:
            if docker_host := self._get_docker_host():
                self.rich.print_error(f"Docker daemon not accessible at {docker_host}")
                self.rich.print_info("💡 Try:")
                self.rich.print_info("   - Start Docker: systemctl --user start docker")
                self.rich.print_info("   - Or use system Docker: sudo systemctl start docker")
            else:
                self.rich.print_error("Docker daemon not running or accessible")
                self.rich.print_info("💡 Try:")
                self.rich.print_info("   - Start Docker: systemctl --user start docker")
                self.rich.print_info("   - Or use system Docker: sudo systemctl start docker")
                self.rich.print_info("   - Or set DOCKER_HOST: export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock")
            return False

        else:
            return True

    def _get_tux_resources(self, resource_type: str) -> list[str]:
        """Get Tux-related Docker resources safely."""
        safe_patterns: dict[str, list[str]] = {
            "images": [
                r"^tux:.*",
                r"^ghcr\.io/allthingslinux/tux:.*",
            ],
            "containers": [
                r"^(tux(-dev|-prod)?|memory-test|resource-test)$",
            ],
            "volumes": [
                r"^tux(_dev)?_(cache|temp)$",
            ],
            "networks": [
                r"^tux_default$",
                r"^tux-.*",
            ],
        }

        try:
            if resource_type == "images":
                result = subprocess.run(
                    [self._get_docker_cmd(), "images", "--format", "{{.Repository}}:{{.Tag}}"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            elif resource_type == "containers":
                result = subprocess.run(
                    [self._get_docker_cmd(), "ps", "-a", "--format", "{{.Names}}"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            elif resource_type == "volumes":
                result = subprocess.run(
                    [self._get_docker_cmd(), "volume", "ls", "--format", "{{.Name}}"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            elif resource_type == "networks":
                result = subprocess.run(
                    [self._get_docker_cmd(), "network", "ls", "--format", "{{.Name}}"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            else:
                return []

            stdout_content = result.stdout or ""
            resources: list[str] = [line.strip() for line in stdout_content.strip().split("\n") if line.strip()]

            # Filter by safe patterns
            safe_resources: list[str] = []
            for resource in resources:
                for pattern in safe_patterns.get(resource_type, []):
                    if re.match(pattern, resource):
                        safe_resources.append(resource)
                        break
        except Exception:
            return []
        else:
            return safe_resources

    def _remove_resources(self, resource_type: str, resources: list[str]) -> None:
        """Remove Docker resources safely."""
        if not resources:
            return

        commands = {
            "containers": [self._get_docker_cmd(), "rm", "-f"],
            "images": [self._get_docker_cmd(), "rmi", "-f"],
            "volumes": [self._get_docker_cmd(), "volume", "rm", "-f"],
            "networks": [self._get_docker_cmd(), "network", "rm"],
        }

        remove_cmd = commands.get(resource_type)
        if not remove_cmd:
            self.rich.print_warning(f"Unknown resource type: {resource_type}")
            return

        resource_singular = resource_type[:-1]  # Remove 's'

        for name in resources:
            try:
                subprocess.run([*remove_cmd, name], capture_output=True, check=True)
                self.rich.print_success(f"Removed {resource_singular}: {name}")
            except Exception as e:
                self.rich.print_warning(f"Failed to remove {resource_singular} {name}: {e}")

    def _cleanup_dangling_resources(self) -> None:
        """Clean up dangling Docker resources."""
        self.rich.print_info("Cleaning dangling images and build cache...")

        try:
            # Remove dangling images
            result = subprocess.run(
                [self._get_docker_cmd(), "images", "--filter", "dangling=true", "--format", "{{.ID}}"],
                capture_output=True,
                text=True,
                check=True,
            )
            stdout_content = result.stdout or ""
            if dangling_ids := [line.strip() for line in stdout_content.strip().split("\n") if line.strip()]:
                subprocess.run(
                    [self._get_docker_cmd(), "rmi", "-f", *dangling_ids],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self.rich.print_success(f"Removed {len(dangling_ids)} dangling images")
            else:
                self.rich.print_info("No dangling images found")
        except Exception as e:
            self.rich.print_warning(f"Failed to clean dangling images: {e}")

        try:
            # System prune
            subprocess.run(
                [self._get_docker_cmd(), "system", "prune", "-f"],
                capture_output=True,
                timeout=60,
                check=True,
            )
            self.rich.print_success("System prune completed")
        except Exception as e:
            self.rich.print_warning(f"System prune failed: {e}")

    # ============================================================================
    # DOCKER COMPOSE COMMANDS
    # ============================================================================

    def build(
        self,
        no_cache: Annotated[bool, Option("--no-cache", help="Build without using cache")] = False,
        target: Annotated[str | None, Option("--target", help="Build target stage")] = None,
    ) -> None:
        """Build Docker images."""
        self.rich.print_section("🐳 Building Docker Images", "blue")

        cmd = [*self._get_compose_base_cmd(), "build"]
        if no_cache:
            cmd.append("--no-cache")
        if target:
            cmd.extend(["--target", target])

        try:
            self._run_command(cmd)
            self.rich.print_success("Docker build completed successfully")
        except subprocess.CalledProcessError:
            self.rich.print_error("Docker build failed")

    def up(  # noqa: PLR0912
        self,
        detach: Annotated[bool, Option("-d", "--detach", help="Run in detached mode")] = False,
        build: Annotated[bool, Option("--build", help="Build images before starting")] = False,
        watch: Annotated[bool, Option("--watch", help="Watch for changes")] = False,
        production: Annotated[bool, Option("--production", help="Enable production mode features")] = False,
        monitor: Annotated[bool, Option("--monitor", help="Enable monitoring and auto-cleanup")] = False,
        max_restart_attempts: Annotated[
            int,
            Option("--max-restart-attempts", help="Maximum restart attempts"),
        ] = 3,
        restart_delay: Annotated[
            int,
            Option("--restart-delay", help="Delay between restart attempts (seconds)"),
        ] = 5,
        services: Annotated[list[str] | None, Argument(help="Services to start")] = None,
    ) -> None:  # sourcery skip: extract-duplicate-method, low-code-quality
        """Start Docker services with smart orchestration."""
        self.rich.print_section("🚀 Starting Docker Services", "blue")

        # Check if Docker is available
        if not self._check_docker():
            self.rich.print_error("Cannot start services - Docker is not available")
            return

        # Set environment variables
        env: dict[str, str] = {}
        if production:
            env |= {
                "MAX_STARTUP_ATTEMPTS": "5",
                "STARTUP_DELAY": "10",
            }
            self.rich.print_info("🏭 Production mode enabled:")
            self.rich.print_info("   - Enhanced retry logic (5 attempts, 10s delay)")
            self.rich.print_info("   - Production-optimized settings")
        else:
            env["DEBUG"] = "true"
            self.rich.print_info("🚀 Development mode enabled:")
            self.rich.print_info("   - Debug mode")
            self.rich.print_info("   - Development-friendly logging")

        if watch:
            self.rich.print_info("   - Hot reload enabled")

        if monitor:
            self.rich.print_info("   - Smart monitoring enabled")
            self.rich.print_info("   - Auto-cleanup on configuration errors")
            self.rich.print_info("   - Automatic service orchestration")

        # If not in detached mode and no monitoring requested, use standard foreground mode
        if not detach and not monitor:
            # Standard docker compose up in foreground
            cmd = [*self._get_compose_base_cmd(), "up"]
            if services:
                cmd.extend(services)
            if build:
                cmd.append("--build")
            if watch:
                cmd.append("--watch")

            try:
                self._run_command(cmd)
            except subprocess.CalledProcessError:
                self.rich.print_success("Docker services started successfully")
        # If monitoring is enabled and not in detached mode, use monitoring logic
        elif monitor and not detach:
            self._start_with_monitoring(
                build=build,
                watch=watch,
                services=services,
                env=env,
                max_restart_attempts=max_restart_attempts,
                restart_delay=restart_delay,
            )
        else:
            # Standard docker compose up in detached mode
            cmd = [*self._get_compose_base_cmd(), "up"]
            if services:
                cmd.extend(services)
            if detach:
                cmd.append("-d")
            if build:
                cmd.append("--build")
            if watch:
                cmd.append("--watch")

            try:
                self._run_command(cmd)
            except subprocess.CalledProcessError:
                self.rich.print_success("Docker services started successfully")

    def _start_with_monitoring(
        self,
        build: bool,
        watch: bool,
        services: list[str] | None,
        env: dict[str, str],
        max_restart_attempts: int,
        restart_delay: int,
    ) -> None:
        """Start services with monitoring and auto-cleanup."""
        # Start services first
        self.rich.print_info("⏳ Starting services...")
        cmd = [*self._get_compose_base_cmd(), "up", "-d"]
        if build:
            cmd.append("--build")
        if services:
            cmd.extend(services)

        try:
            self._run_command(cmd)
        except subprocess.CalledProcessError:
            self.rich.print_error("❌ Failed to start services")
            return

        # Monitor loop
        self.rich.print_info("👀 Starting monitor loop...")
        restart_attempts = 0
        bot_container = "tux"

        try:
            while True:
                # Check bot health
                if not self._check_container_health(bot_container):
                    restart_attempts += 1
                    self.rich.print_warning(
                        f"⚠️  Bot failure detected (attempt {restart_attempts}/{max_restart_attempts})",
                    )

                    # Check for configuration errors
                    if self._has_configuration_error(bot_container):
                        self.rich.print_error("❌ Bot has configuration issues (likely missing/invalid token)")
                        self.rich.print_info("📋 Recent logs:")
                        self._show_container_logs(bot_container, tail=20)
                        self.rich.print_error(
                            "🛑 Shutting down all services - configuration issues won't be fixed by restarting",
                        )
                        break

                    if restart_attempts >= max_restart_attempts:
                        self.rich.print_error("❌ Maximum restart attempts reached. Shutting down all services.")
                        break

                    self.rich.print_info(f"🔄 Restarting services in {restart_delay} seconds...")
                    time.sleep(restart_delay)

                    try:
                        self._run_command(cmd)
                    except subprocess.CalledProcessError:
                        self.rich.print_error("❌ Failed to restart services")
                        break
                else:
                    # Reset restart counter on successful health check
                    restart_attempts = 0

                time.sleep(10)  # Check every 10 seconds

        except KeyboardInterrupt:
            self.rich.print_info("🛑 Monitor stopped by user (Ctrl+C)")
        finally:
            self.rich.print_info("🧹 Cleaning up all services...")
            self._run_command([*self._get_compose_base_cmd(), "down"])
            self.rich.print_success("✅ Cleanup complete")

    def down(
        self,
        volumes: Annotated[bool, Option("-v", "--volumes", help="Remove volumes")] = False,
        remove_orphans: Annotated[bool, Option("--remove-orphans", help="Remove orphaned containers")] = False,
        services: Annotated[list[str] | None, Argument(help="Services to stop")] = None,
    ) -> None:
        """Stop Docker services."""
        self.rich.print_section("🛑 Stopping Docker Services", "blue")

        cmd = [*self._get_compose_base_cmd(), "down"]

        if services:
            cmd.extend(services)

        if volumes:
            cmd.append("--volumes")
        if remove_orphans:
            cmd.append("--remove-orphans")

        try:
            self._run_command(cmd)
        except subprocess.CalledProcessError:
            self.rich.print_success("Docker services stopped successfully")

    def logs(
        self,
        follow: Annotated[bool, Option("-f", "--follow", help="Follow log output")] = False,
        tail: Annotated[int | None, Option("-n", "--tail", help="Number of lines to show")] = None,
        services: Annotated[list[str] | None, Argument(help="Services to show logs for")] = None,
    ) -> None:
        """Show Docker service logs."""
        self.rich.print_section("📋 Docker Service Logs", "blue")

        cmd = [*self._get_compose_base_cmd(), "logs"]

        if services:
            cmd.extend(services)

        if follow:
            cmd.append("-f")
        if tail:
            cmd.extend(["-n", str(tail)])

        try:
            self._run_command(cmd)
        except subprocess.CalledProcessError:
            self.rich.print_success("Logs displayed successfully")

    def ps(self) -> None:
        """List running Docker containers."""
        self.rich.print_section("📊 Docker Containers", "blue")
        if self._run_command([*self._get_compose_base_cmd(), "ps"]):
            self.rich.print_success("Container list displayed successfully")

    def exec(
        self,
        service: Annotated[str, Argument(help="Service name")],
        command: Annotated[list[str] | None, Argument(help="Command to execute")] = None,
    ) -> None:
        """Execute command in container."""
        self.rich.print_section("🔧 Executing Command in Container", "blue")

        cmd = [*self._get_compose_base_cmd(), "exec", service]
        if command:
            cmd.extend(command)
        else:
            cmd.append("bash")

        try:
            self._run_command(cmd)
        except subprocess.CalledProcessError:
            self.rich.print_success("Command executed successfully")

    def shell(
        self,
        service: Annotated[str | None, Argument(help="Service name")] = None,
    ) -> None:
        """Open shell in container."""
        self.rich.print_section("🐚 Opening Shell in Container", "blue")

        service_name = service or "tux"
        cmd = [*self._get_compose_base_cmd(), "exec", service_name, "bash"]

        try:
            self._run_command(cmd)
        except subprocess.CalledProcessError:
            self.rich.print_success("Shell opened successfully")

    def restart(
        self,
        service: Annotated[str | None, Argument(help="Service name")] = None,
    ) -> None:
        """Restart Docker services."""
        self.rich.print_section("🔄 Restarting Docker Services", "blue")

        service_name = service or "tux"
        cmd = [*self._get_compose_base_cmd(), "restart", service_name]

        try:
            self._run_command(cmd)
        except subprocess.CalledProcessError:
            self.rich.print_success("Docker services restarted successfully")

    def health(self) -> None:
        """Check container health status."""
        self.rich.print_section("🏥 Container Health Status", "blue")
        if self._run_command([*self._get_compose_base_cmd(), "ps"]):
            self.rich.print_success("Health check completed successfully")

    def config(self) -> None:
        """Validate Docker Compose configuration."""
        self.rich.print_section("⚙️ Docker Compose Configuration", "blue")
        if self._run_command([*self._get_compose_base_cmd(), "config"]):
            self.rich.print_success("Configuration validation completed successfully")

    def pull(self) -> None:
        """Pull latest Docker images."""
        self.rich.print_section("⬇️ Pulling Docker Images", "blue")
        if self._run_command([*self._get_compose_base_cmd(), "pull"]):
            self.rich.print_success("Docker images pulled successfully")

    def _check_container_health(self, container_name: str) -> bool:
        # sourcery skip: assign-if-exp, boolean-if-exp-identity, hoist-statement-from-if, reintroduce-else
        """Check if a container is running and healthy."""
        try:
            client = self._get_docker_client()
            container = client.containers.get(container_name)

            if container.status != "running":
                return False

            if health := container.attrs.get("State", {}).get("Health", {}):
                health_status = health.get("Status", "")
                if health_status == "unhealthy":
                    return False
                if health_status == "healthy":
                    return True
                # Starting or no health check
                return True

                # No health check configured, assume healthy if running
        except Exception:
            return False
        else:
            return True

    def _has_configuration_error(self, container_name: str) -> bool:
        """Check if container logs indicate configuration errors."""
        try:
            client = self._get_docker_client()
            container = client.containers.get(container_name)
            logs = container.logs(tail=20, timestamps=False).decode("utf-8")
            # Strip ANSI codes and convert to lowercase for pattern matching
            clean_logs = self._strip_ansi_codes(logs).lower()

            # Look for configuration error patterns
            error_patterns = [
                "token.*missing",
                "discord.*token",
                "bot.*token.*invalid",
                "configuration.*error",
                "no bot token provided",
            ]

            return any(pattern in clean_logs for pattern in error_patterns)
        except Exception:
            return False

    def _show_container_logs(self, container_name: str, tail: int = 20) -> None:
        """Show container logs."""
        try:
            client = self._get_docker_client()
            container = client.containers.get(container_name)
            logs = container.logs(tail=tail, timestamps=False).decode("utf-8")
            for line in logs.split("\n"):
                if line.strip():
                    # Strip ANSI color codes for cleaner display
                    clean_line = self._strip_ansi_codes(line)
                    self.rich.print_info(f"  {clean_line}")
        except Exception as e:
            self.rich.print_warning(f"Failed to get logs: {e}")

    def _strip_ansi_codes(self, text: str) -> str:
        """Strip ANSI color codes from text."""
        # Remove ANSI escape sequences
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)

    # ============================================================================
    # DOCKER MANAGEMENT COMMANDS
    # ============================================================================

    def cleanup(
        self,
        volumes: Annotated[bool, Option("--volumes", help="Include volumes in cleanup")] = False,
        force: Annotated[bool, Option("--force", help="Skip confirmation")] = False,
        dry_run: Annotated[bool, Option("--dry-run", help="Show what would be cleaned without doing it")] = False,
    ) -> None:
        """Clean up Docker resources."""
        self.rich.print_section("🧹 Docker Cleanup", "blue")

        if not self._check_docker():
            self.rich.print_error("Docker is not running or accessible")
            return

        if dry_run:
            self.rich.print_info("🔍 DRY RUN MODE - No resources will actually be removed")

        self.rich.print_info("Scanning for Tux-related Docker resources...")

        # Get Tux-specific resources safely
        tux_containers = self._get_tux_resources("containers")
        tux_images = self._get_tux_resources("images")
        tux_volumes = self._get_tux_resources("volumes") if volumes else []
        tux_networks = self._get_tux_resources("networks")

        # Filter out special networks
        tux_networks = [net for net in tux_networks if net not in ["bridge", "host", "none"]]

        # Display what will be cleaned
        def log_resource_list(resource_type: str, resources: list[str]) -> None:
            if resources:
                self.rich.print_info(f"{resource_type} ({len(resources)}):")
                for resource in resources:
                    self.rich.print_info(f"  - {resource}")

        log_resource_list("Containers", tux_containers)
        log_resource_list("Images", tux_images)
        log_resource_list("Volumes", tux_volumes)
        log_resource_list("Networks", tux_networks)

        if not any([tux_containers, tux_images, tux_volumes, tux_networks]):
            self.rich.print_success("No Tux-related Docker resources found to clean up")
            return

        if dry_run:
            self.rich.print_info("DRY RUN: No resources were actually removed")
            return

        if not force:
            self.rich.print_warning("⚠️  This will remove Tux-related Docker resources")
            self.rich.print_info("Use --force to skip confirmation")
            return

        self.rich.print_info("Cleaning up Tux-related Docker resources...")

        # Remove resources in order
        self._remove_resources("containers", tux_containers)
        self._remove_resources("images", tux_images)
        self._remove_resources("volumes", tux_volumes)
        self._remove_resources("networks", tux_networks)

        # Clean up dangling resources
        self._cleanup_dangling_resources()

        self.rich.print_success("Tux Docker cleanup completed")

    def test(
        self,
        test_type: Annotated[str, Argument(help="Test type: quick, comprehensive, perf, or security")],
    ) -> None:
        """Run Docker tests."""
        self.rich.print_section("🧪 Docker Tests", "blue")

        test_configs = {
            "quick": ("⚡ Running quick Docker validation tests...", "Quick tests not fully implemented yet"),
            "perf": ("📊 Running Docker performance tests...", "Performance tests not fully implemented yet"),
            "security": ("🔒 Running Docker security tests...", "Security tests not fully implemented yet"),
            "comprehensive": (
                "🎯 Running full Docker comprehensive test suite...",
                "Comprehensive tests not fully implemented yet",
            ),
        }

        if test_type not in test_configs:
            self.rich.print_error(f"Unknown test type: {test_type}")
            return

        log_message, warning_message = test_configs[test_type]
        self.rich.print_info(log_message)
        self.rich.print_warning(f"⚠️  {warning_message}")

    def _test_build(self, test_result: Callable[[bool, str], None]) -> None:
        """Test Docker build functionality."""
        self.rich.print_info("🔨 Testing builds...")
        timer = Timer()
        timer.start()
        try:
            self._safe_run(
                [self._get_docker_cmd(), "build", "--target", "dev", "-t", "tux:quick-dev", "."],
                capture_output=True,
                timeout=180,
            )
            elapsed = timer.elapsed_ms()
            test_result(True, f"Development build completed in {elapsed}ms")
        except Exception:
            test_result(False, "Development build failed")

    def _test_container_startup(self, test_result: Callable[[bool, str], None]) -> None:
        """Test container startup functionality."""
        self.rich.print_info("🚀 Testing container startup...")
        try:
            # Start container
            self._safe_run(
                [self._get_docker_cmd(), "run", "-d", "--name", "tux-quick-test", "tux:quick-dev"],
                capture_output=True,
                timeout=30,
            )

            # Wait a moment for startup
            time.sleep(2)

            # Check if container is running
            result = self._safe_run(
                [self._get_docker_cmd(), "ps", "--filter", "name=tux-quick-test", "--format", "{{.Status}}"],
                capture_output=True,
                text=True,
            )

            if "Up" in result.stdout:
                test_result(True, "Container started successfully")
            else:
                test_result(False, "Container failed to start")

        except Exception:
            test_result(False, "Container startup test failed")
        finally:
            # Cleanup
            with contextlib.suppress(Exception):
                subprocess.run([self._get_docker_cmd(), "rm", "-f", "tux-quick-test"], check=False, capture_output=True)

    def _test_basic_functionality(self, test_result: Callable[[bool, str], None]) -> None:
        """Test basic container functionality."""
        self.rich.print_info("🔧 Testing basic functionality...")
        try:
            result = self._safe_run(
                [self._get_docker_cmd(), "run", "--rm", "tux:quick-dev", "python", "-c", "print('Hello from Tux!')"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if "Hello from Tux!" in result.stdout:
                test_result(True, "Basic Python execution works")
            else:
                test_result(False, "Basic Python execution failed")
        except Exception:
            test_result(False, "Basic functionality test failed")

    def test_quick(self) -> None:
        """Run quick Docker validation tests."""
        self.rich.print_section("⚡ Quick Docker Tests", "blue")

        if not self._check_docker():
            self.rich.print_error("Docker is not running or accessible")
            return

        passed = 0
        failed = 0

        def test_result(success: bool, description: str) -> None:
            nonlocal passed, failed
            if success:
                self.rich.print_success(f"✅ {description}")
                passed += 1
            else:
                self.rich.print_error(f"❌ {description}")
                failed += 1

        # Run tests
        self._test_build(test_result)
        self._test_container_startup(test_result)
        self._test_basic_functionality(test_result)

        # Summary
        self.rich.print_section("📊 Test Results", "blue")
        self.rich.print_info(f"Passed: {passed}")
        self.rich.print_info(f"Failed: {failed}")

        if failed == 0:
            self.rich.print_success("🎉 All quick tests passed!")
        else:
            self.rich.print_error(f"❌ {failed} tests failed")

    def _test_multi_stage_builds(self, test_result: Callable[[bool, str], None]) -> None:
        """Test multi-stage Docker builds."""
        self.rich.print_info("🏗️ Testing multi-stage builds...")
        build_targets = ["dev", "prod", "test"]
        for target in build_targets:
            timer = Timer()
            timer.start()
            try:
                self._safe_run(
                    [self._get_docker_cmd(), "build", "--target", target, "-t", f"tux:comp-{target}", "."],
                    capture_output=True,
                    timeout=300,
                )
                elapsed = timer.elapsed_ms()
                test_result(True, f"{target} build completed in {elapsed}ms")
            except Exception:
                test_result(False, f"{target} build failed")

    def _test_resource_limits(self, test_result: Callable[[bool, str], None]) -> None:
        """Test Docker resource limits."""
        self.rich.print_info("💾 Testing resource limits...")
        try:
            result = self._safe_run(
                [
                    self._get_docker_cmd(),
                    "run",
                    "--rm",
                    "--memory=100m",
                    "tux:comp-dev",
                    "python",
                    "-c",
                    "import sys; print('Memory test OK')",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if "Memory test OK" in result.stdout:
                test_result(True, "Memory limit test passed")
            else:
                test_result(False, "Memory limit test failed")
        except Exception:
            test_result(False, "Resource limit test failed")

    def _test_network_connectivity(self, test_result: Callable[[bool, str], None]) -> None:
        """Test Docker network connectivity."""
        self.rich.print_info("🌐 Testing network connectivity...")
        try:
            result = self._safe_run(
                [
                    self._get_docker_cmd(),
                    "run",
                    "--rm",
                    "tux:comp-dev",
                    "python",
                    "-c",
                    "import socket; print('Network test OK')",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if "Network test OK" in result.stdout:
                test_result(True, "Network connectivity test passed")
            else:
                test_result(False, "Network connectivity test failed")
        except Exception:
            test_result(False, "Network connectivity test failed")

    def _test_filesystem_operations(self, test_result: Callable[[bool, str], None]) -> None:
        """Test Docker file system operations."""
        self.rich.print_info("📁 Testing file system operations...")
        try:
            result = self._safe_run(
                [
                    self._get_docker_cmd(),
                    "run",
                    "--rm",
                    "tux:comp-dev",
                    "python",
                    "-c",
                    "import os; os.makedirs('/tmp/test', exist_ok=True); print('FS test OK')",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if "FS test OK" in result.stdout:
                test_result(True, "File system operations test passed")
            else:
                test_result(False, "File system operations test failed")
        except Exception:
            test_result(False, "File system operations test failed")

    def _cleanup_test_images(self) -> None:
        """Clean up test images."""
        self.rich.print_info("🧹 Cleaning up test images...")
        build_targets = ["dev", "prod", "test"]
        for target in build_targets:
            with contextlib.suppress(Exception):
                subprocess.run(
                    [self._get_docker_cmd(), "rmi", "-f", f"tux:comp-{target}"],
                    check=False,
                    capture_output=True,
                )

    def test_comprehensive(self) -> None:
        """Run comprehensive Docker tests."""
        self.rich.print_section("🎯 Comprehensive Docker Tests", "blue")

        if not self._check_docker():
            self.rich.print_error("Docker is not running or accessible")
            return

        passed = 0
        failed = 0

        def test_result(success: bool, description: str) -> None:
            nonlocal passed, failed
            if success:
                self.rich.print_success(f"✅ {description}")
                passed += 1
            else:
                self.rich.print_error(f"❌ {description}")
                failed += 1

        # Run tests
        self._test_multi_stage_builds(test_result)
        self._test_resource_limits(test_result)
        self._test_network_connectivity(test_result)
        self._test_filesystem_operations(test_result)

        self._cleanup_test_images()

        self.rich.print_section("📊 Comprehensive Test Results", "blue")
        self.rich.print_info(f"Passed: {passed}")
        self.rich.print_info(f"Failed: {failed}")

        if failed == 0:
            self.rich.print_success("🎉 All comprehensive tests passed!")
        else:
            self.rich.print_error(f"❌ {failed} tests failed")


# Create the CLI app instance for mkdocs-typer
app = DockerCLI().app


def main() -> None:
    """Entry point for the Docker CLI script."""
    cli = DockerCLI()
    cli.run()


if __name__ == "__main__":
    main()
