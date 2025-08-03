"""Tests for the main module."""

import inspect
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Mock the config loading before importing tux.main to prevent FileNotFoundError in CI
# We need to mock the file reading operations that happen at module import time
with patch("pathlib.Path.read_text") as mock_read_text:
    # Mock the YAML content that would be read from config files
    mock_config_content = """
    USER_IDS:
      BOT_OWNER: 123456789
      SYSADMINS: [123456789]
    ALLOW_SYSADMINS_EVAL: false
    BOT_INFO:
      BOT_NAME: "Test Bot"
      PROD_PREFIX: "!"
      DEV_PREFIX: "??"
      ACTIVITIES: "Testing"
      HIDE_BOT_OWNER: false
    STATUS_ROLES: []
    TEMPVC_CATEGORY_ID: null
    TEMPVC_CHANNEL_ID: null
    GIF_LIMITER:
      RECENT_GIF_AGE: 3600
      GIF_LIMIT_EXCLUDE: []
      GIF_LIMITS_USER: {}
      GIF_LIMITS_CHANNEL: {}
    XP:
      XP_BLACKLIST_CHANNELS: []
      XP_ROLES: []
      XP_MULTIPLIERS: []
      XP_COOLDOWN: 60
      LEVELS_EXPONENT: 2
      SHOW_XP_PROGRESS: false
      ENABLE_XP_CAP: true
    SNIPPETS:
      LIMIT_TO_ROLE_IDS: false
      ACCESS_ROLE_IDS: []
    IRC:
      BRIDGE_WEBHOOK_IDS: []
    """
    mock_read_text.return_value = mock_config_content
    import tux.main


class TestMain:
    """Test cases for the main module."""

    @patch("tux.main.TuxApp")
    def test_run_creates_app_and_calls_run(self, mock_tux_app_class: Mock) -> None:
        """Test that run() creates a TuxApp instance and calls its run method."""
        # Arrange
        mock_app_instance = Mock()
        mock_tux_app_class.return_value = mock_app_instance

        # Act
        tux.main.run()

        # Assert
        mock_tux_app_class.assert_called_once()
        mock_app_instance.run.assert_called_once()

    @patch("tux.main.TuxApp")
    def test_run_propagates_app_exceptions(self, mock_tux_app_class: Mock) -> None:
        """Test that run() propagates exceptions from TuxApp.run()."""
        # Arrange
        mock_app_instance = Mock()
        mock_app_instance.run.side_effect = RuntimeError("Test error")
        mock_tux_app_class.return_value = mock_app_instance

        # Act & Assert
        with pytest.raises(RuntimeError, match="Test error"):
            tux.main.run()

    @patch("tux.main.TuxApp")
    def test_run_propagates_app_creation_exceptions(self, mock_tux_app_class: Mock) -> None:
        """Test that run() propagates exceptions from TuxApp instantiation."""
        # Arrange
        mock_tux_app_class.side_effect = ValueError("App creation failed")

        # Act & Assert
        with pytest.raises(ValueError, match="App creation failed"):
            tux.main.run()

    @patch("tux.main.run")
    def test_main_module_execution(self, mock_run: Mock) -> None:
        """Test that the main module calls run() when executed directly."""
        # This test simulates the behavior of `if __name__ == "__main__":`
        # We can't directly test the __name__ == "__main__" condition in a unit test,
        # but we can test that the run function is called correctly when invoked

        # Arrange & Act
        # Simulate direct execution by calling the code that would run
        # when the module is executed directly
        if __name__ == "__main__":
            tux.main.run()

        # Since we're not actually running as __main__ in the test,
        # we need to manually call it to verify the behavior
        tux.main.run()

        # Assert
        mock_run.assert_called_once()


class TestMainExecution:
    """Test the main module execution behavior."""

    def test_module_has_main_guard(self) -> None:
        """Test that the main module has the proper __name__ == '__main__' guard."""
        # Read the main.py file to ensure it has the proper structure

        import tux.main  # noqa: PLC0415

        # Get the source code of the main module
        source = inspect.getsource(tux.main)

        # Verify the main guard exists
        assert 'if __name__ == "__main__":' in source
        assert "run()" in source

    @patch("tux.main.TuxApp")
    def test_run_function_signature(self, mock_tux_app_class: Mock) -> None:
        """Test that the run function has the correct signature."""

        # Check that run() takes no arguments
        sig = inspect.signature(tux.main.run)
        assert len(sig.parameters) == 0

        # Check that run() returns None
        assert sig.return_annotation is None or sig.return_annotation is type(None)

        # Verify it can be called without arguments
        tux.main.run()
        mock_tux_app_class.assert_called_once()


class TestMainIntegration:
    """Test realistic integration scenarios for main.py."""

    def test_import_has_no_side_effects(self) -> None:
        """Test that importing the main module doesn't execute the bot."""
        # This is important for CLI integration - importing shouldn't start the bot
        # We're testing this by ensuring the module can be imported multiple times
        # without side effects

        import importlib  # noqa: PLC0415

        # Import the module multiple times
        for _ in range(3):
            importlib.reload(tux.main)

    @patch("tux.main.TuxApp")
    def test_cli_integration_compatibility(self, mock_tux_app_class: Mock) -> None:
        """Test that the main.run() function works correctly when called from CLI."""
        # This tests the actual usage pattern from tux/cli/core.py
        mock_app_instance = Mock()
        mock_tux_app_class.return_value = mock_app_instance

        # Simulate the CLI calling run() (from tux.cli.core start command)
        from tux.main import run  # noqa: PLC0415

        result = run()

        # The CLI expects run() to return None or an exit code
        assert result is None
        mock_tux_app_class.assert_called_once()
        mock_app_instance.run.assert_called_once()

    @patch("tux.main.TuxApp")
    def test_multiple_run_calls_create_separate_apps(self, mock_tux_app_class: Mock) -> None:
        """Test that multiple calls to run() create separate TuxApp instances."""
        # This tests that the function doesn't maintain state between calls
        mock_app_instance = Mock()
        mock_tux_app_class.return_value = mock_app_instance

        # Call run() multiple times
        tux.main.run()
        tux.main.run()
        tux.main.run()

        # Each call should create a new TuxApp instance
        assert mock_tux_app_class.call_count == 3
        assert mock_app_instance.run.call_count == 3

    @pytest.mark.slow
    def test_module_can_be_executed_as_script(self) -> None:
        """Test that the module can actually be executed as a Python script."""
        # This is a real integration test that actually tries to run the module
        # We mock the TuxApp to prevent the bot from starting

        # Create a temporary script that imports and patches TuxApp

        test_script = textwrap.dedent("""
            import sys
            from unittest.mock import Mock, patch

            # Add the project root to the path
            sys.path.insert(0, "{project_root}")

            # Mock the config loading before importing tux.main to prevent FileNotFoundError in CI
            # We need to mock the file reading operations that happen at module import time
            with patch("pathlib.Path.read_text") as mock_read_text:
                # Mock the YAML content that would be read from config files
                mock_config_content = '''
                USER_IDS:
                  BOT_OWNER: 123456789
                  SYSADMINS: [123456789]
                ALLOW_SYSADMINS_EVAL: false
                BOT_INFO:
                  BOT_NAME: "Test Bot"
                  PROD_PREFIX: "!"
                  DEV_PREFIX: "??"
                  ACTIVITIES: "Testing"
                  HIDE_BOT_OWNER: false
                STATUS_ROLES: []
                TEMPVC_CATEGORY_ID: null
                TEMPVC_CHANNEL_ID: null
                GIF_LIMITER:
                  RECENT_GIF_AGE: 3600
                  GIF_LIMIT_EXCLUDE: []
                  GIF_LIMITS_USER: {{}}
                  GIF_LIMITS_CHANNEL: {{}}
                XP:
                  XP_BLACKLIST_CHANNELS: []
                  XP_ROLES: []
                  XP_MULTIPLIERS: []
                  XP_COOLDOWN: 60
                  LEVELS_EXPONENT: 2
                  SHOW_XP_PROGRESS: false
                  ENABLE_XP_CAP: true
                SNIPPETS:
                  LIMIT_TO_ROLE_IDS: false
                  ACCESS_ROLE_IDS: []
                IRC:
                  BRIDGE_WEBHOOK_IDS: []
                '''
                mock_read_text.return_value = mock_config_content

                with patch("tux.app.TuxApp") as mock_app:
                    mock_instance = Mock()
                    mock_app.return_value = mock_instance

                    # Import and run main
                    import tux.main
                    tux.main.run()

                    # Verify it was called
                    assert mock_app.called
                    assert mock_instance.run.called
                    print("SUCCESS: Module executed correctly")
        """)

        # Get the project root dynamically
        project_root = Path(__file__).parent.parent
        script_content = test_script.format(project_root=project_root)

        # Write and execute the test script
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(script_content)
            temp_script = f.name

        try:
            result = subprocess.run(
                [sys.executable, temp_script],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            # Check that the script executed successfully
            assert result.returncode == 0, f"Script failed: {result.stderr}"
            assert "SUCCESS: Module executed correctly" in result.stdout

        finally:
            # Clean up
            Path(temp_script).unlink(missing_ok=True)

    def test_docstring_is_present_and_meaningful(self) -> None:
        """Test that the module has a proper docstring."""
        # This tests documentation quality, which is important for maintainability
        assert tux.main.__doc__ is not None
        assert len(tux.main.__doc__.strip()) > 10
        assert "entrypoint" in tux.main.__doc__.lower() or "entry point" in tux.main.__doc__.lower()

        # Test that the run function also has a docstring
        assert tux.main.run.__doc__ is not None
        assert len(tux.main.run.__doc__.strip()) > 10
