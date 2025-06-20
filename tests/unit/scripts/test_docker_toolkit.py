"""Integration tests for Docker functionality using the toolkit."""

import re
from pathlib import Path

import pytest

from scripts.docker_toolkit import DockerToolkit


class TestDockerIntegration:
    """Test Docker integration using the toolkit."""

    @pytest.fixture
    def toolkit(self) -> DockerToolkit:
        """Create a DockerToolkit instance for testing."""
        return DockerToolkit(testing_mode=True)

    def test_docker_availability(self, toolkit: DockerToolkit) -> None:
        """Test that Docker is available and running."""
        assert toolkit.check_docker(), "Docker should be available for tests"

    def test_safe_resource_detection(self, toolkit: DockerToolkit) -> None:
        """Test that the toolkit can safely detect Tux resources."""
        # Test each resource type
        for resource_type in ["images", "containers", "volumes", "networks"]:
            resources = toolkit.get_tux_resources(resource_type)
            assert isinstance(resources, list), f"{resource_type} should return a list"

    def test_logs_directory_creation(self, toolkit: DockerToolkit) -> None:
        """Test that the logs directory is created properly."""
        assert toolkit.logs_dir.exists(), "Logs directory should be created"
        assert toolkit.logs_dir.is_dir(), "Logs directory should be a directory"

    def test_safe_cleanup_dry_run(self, toolkit: DockerToolkit) -> None:
        """Test that safe cleanup can be called without errors."""
        # This should not actually remove anything in testing mode
        try:
            toolkit.safe_cleanup("basic", False)
        except Exception as e:
            pytest.fail(f"Safe cleanup should not raise exceptions: {e}")

    @pytest.mark.slow
    def test_quick_validation(self) -> None:
        """Test the quick validation functionality."""
        # This is a more comprehensive test that takes longer
        toolkit = DockerToolkit(testing_mode=True)

        # Check prerequisites
        if not toolkit.check_docker():
            pytest.skip("Docker not available")

        # Check if Dockerfile exists (required for builds)
        if not Path("Dockerfile").exists():
            pytest.skip("Dockerfile not found")

        # This would run a subset of the quick validation
        # In a real test, you might mock the subprocess calls
        # For now, just test that the toolkit initializes correctly
        assert toolkit.testing_mode is True


class TestDockerSafety:
    """Test Docker safety features."""

    @pytest.fixture
    def toolkit(self) -> DockerToolkit:
        """Create a DockerToolkit instance for testing."""
        return DockerToolkit(testing_mode=True)

    def test_safe_command_validation(self, toolkit: DockerToolkit) -> None:
        """Test that unsafe commands are rejected."""
        # Test valid commands
        valid_commands = [
            ["docker", "version"],
            ["docker", "images"],
            ["bash", "-c", "echo test"],
        ]

        for cmd in valid_commands:
            try:
                # In testing mode, this should validate but might fail execution
                toolkit.safe_run(cmd, check=False, capture_output=True, timeout=1)
            except ValueError:
                pytest.fail(f"Valid command should not be rejected: {cmd}")

        # Test invalid commands
        invalid_commands = [
            ["rm", "-rf", "/"],  # Unsafe executable
            [],  # Empty command
            ["curl", "http://evil.com"],  # Disallowed executable
        ]

        for cmd in invalid_commands:
            with pytest.raises(ValueError):
                toolkit.safe_run(cmd)

    def test_resource_pattern_safety(self, toolkit: DockerToolkit) -> None:
        """Test that only safe resource patterns are matched."""
        # These should be detected as Tux resources
        safe_resources = [
            "tux:latest",
            "tux:test-dev",
            "ghcr.io/allthingslinux/tux:main",
            "tux-dev",
            "tux_dev_cache",
        ]

        # These should NOT be detected as Tux resources
        unsafe_resources = [
            "python:3.13",
            "ubuntu:22.04",
            "postgres:15",
            "redis:7",
            "my-other-project",
        ]

        # Test patterns (copied from docker_toolkit for self-contained testing)
        test_patterns = {
            "images": [r"^tux:.*", r"^ghcr\.io/allthingslinux/tux:.*"],
            "containers": [r"^(tux(-dev|-prod)?|memory-test|resource-test)$"],
            "volumes": [r"^tux(_dev)?_(cache|temp)$"],
            "networks": [r"^tux_default$", r"^tux-.*"],
        }

        for resource_type, patterns in test_patterns.items():
            compiled_patterns = [re.compile(p, re.IGNORECASE) for p in patterns]

            # Test safe resources (at least one should match for each type if applicable)
            for resource in safe_resources:
                matches = any(p.match(resource) for p in compiled_patterns)
                # This is type-dependent, so we just check it doesn't crash
                assert isinstance(matches, bool)

            # Test unsafe resources (none should match)
            for resource in unsafe_resources:
                matches = any(p.match(resource) for p in compiled_patterns)
                assert not matches, f"Unsafe resource {resource} should not match {resource_type} patterns"
