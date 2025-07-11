"""Tests for tux.utils.env module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from tux.utils.env import (
    Config,
    ConfigurationError,
    EnvError,
    Environment,
    EnvironmentManager,
    configure_environment,
    get_bot_token,
    get_config,
    get_current_env,
    get_database_url,
    is_dev_mode,
    is_prod_mode,
    set_env_mode,
)


class TestEnvError:
    """Test the EnvError exception class."""

    def test_env_error_inheritance(self):
        """Test that EnvError inherits from Exception."""
        assert issubclass(EnvError, Exception)

    def test_env_error_instantiation(self):
        """Test creating an EnvError instance."""
        error = EnvError("test error")
        assert str(error) == "test error"


class TestConfigurationError:
    """Test the ConfigurationError exception class."""

    def test_configuration_error_inheritance(self):
        """Test that ConfigurationError inherits from EnvError."""
        assert issubclass(ConfigurationError, EnvError)

    def test_configuration_error_instantiation(self):
        """Test creating a ConfigurationError instance."""
        error = ConfigurationError("config error")
        assert str(error) == "config error"


class TestEnvironment:
    """Test the Environment enum."""

    def test_environment_values(self):
        """Test Environment enum values."""
        assert Environment.DEVELOPMENT.value == "dev"
        assert Environment.PRODUCTION.value == "prod"

    def test_is_dev_property(self):
        """Test the is_dev property."""
        assert Environment.DEVELOPMENT.is_dev is True
        assert Environment.PRODUCTION.is_dev is False

    def test_is_prod_property(self):
        """Test the is_prod property."""
        assert Environment.DEVELOPMENT.is_prod is False
        assert Environment.PRODUCTION.is_prod is True


class TestConfig:
    """Test the Config class."""

    @staticmethod
    def _clear_test_env_vars():
        """Clear test environment variables."""
        env_vars_to_clear = [
            "TEST_VAR",
            "TEST_BOOL",
            "TEST_INT",
            "DEV_DATABASE_URL",
            "PROD_DATABASE_URL",
            "DEV_BOT_TOKEN",
            "PROD_BOT_TOKEN",
        ]
        for var in env_vars_to_clear:
            os.environ.pop(var, None)

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        self._clear_test_env_vars()
        yield
        self._clear_test_env_vars()

    def test_config_init_without_dotenv(self):
        """Test Config initialization without loading dotenv."""
        config = Config(load_env=False)
        expected_root = Path(__file__).parent.parent.parent.parent
        if expected_root.parent.name == "tux":
            expected_root = expected_root.parent
        assert config.workspace_root == expected_root
        assert config.dotenv_path == config.workspace_root / ".env"

    def test_config_init_with_custom_dotenv_path(self):
        """Test Config initialization with custom dotenv path."""
        custom_path = Path("/custom/path/.env")
        config = Config(dotenv_path=custom_path, load_env=False)
        assert config.dotenv_path == custom_path

    def test_get_existing_env_var(self):
        """Test getting an existing environment variable."""
        os.environ["TEST_VAR"] = "test_value"
        config = Config(load_env=False)
        assert config.get("TEST_VAR") == "test_value"

    def test_get_non_existing_env_var_with_default(self):
        """Test getting a non-existing environment variable with default."""
        config = Config(load_env=False)
        assert config.get("NON_EXISTING_VAR", default="default_value") == "default_value"

    def test_get_non_existing_env_var_without_default(self):
        """Test getting a non-existing environment variable without default."""
        config = Config(load_env=False)
        assert config.get("NON_EXISTING_VAR") is None

    def test_get_required_env_var_missing(self):
        """Test getting a required environment variable that's missing."""
        config = Config(load_env=False)
        with pytest.raises(ConfigurationError, match="Required environment variable"):
            config.get("MISSING_REQUIRED_VAR", required=True)

    def test_get_required_env_var_existing(self):
        """Test getting a required environment variable that exists."""
        os.environ["REQUIRED_VAR"] = "required_value"
        config = Config(load_env=False)
        assert config.get("REQUIRED_VAR", required=True) == "required_value"

    @pytest.mark.parametrize("true_val", ["true", "True", "TRUE", "yes", "YES", "1", "y", "Y"])
    def test_get_bool_type_conversion_true(self, true_val: str):
        """Test boolean type conversion for true values."""
        config = Config(load_env=False)
        os.environ["TEST_BOOL"] = true_val
        assert config.get("TEST_BOOL", default=False) is True

    @pytest.mark.parametrize("false_val", ["false", "False", "FALSE", "no", "NO", "0", "n", "N"])
    def test_get_bool_type_conversion_false(self, false_val: str):
        """Test boolean type conversion for false values."""
        config = Config(load_env=False)
        os.environ["TEST_BOOL"] = false_val
        assert config.get("TEST_BOOL", default=False) is False

    def test_get_int_type_conversion(self):
        """Test integer type conversion."""
        os.environ["TEST_INT"] = "42"
        config = Config(load_env=False)
        assert config.get("TEST_INT", default=0) == 42

    def test_get_invalid_type_conversion_not_required(self):
        """Test invalid type conversion when not required."""
        os.environ["TEST_INT"] = "not_a_number"
        config = Config(load_env=False)
        assert config.get("TEST_INT", default=10) == 10

    def test_get_invalid_type_conversion_required(self):
        """Test invalid type conversion when required."""
        os.environ["TEST_INT"] = "not_a_number"
        config = Config(load_env=False)
        with pytest.raises(ConfigurationError, match="is not a valid"):
            config.get("TEST_INT", default=10, required=True)

    def test_set_env_var(self):
        """Test setting an environment variable."""
        config = Config(load_env=False)
        config.set("NEW_VAR", "new_value")
        assert os.environ["NEW_VAR"] == "new_value"

    def test_set_env_var_with_persist(self):
        """Test setting an environment variable with persistence."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as tmp:
            tmp.write("EXISTING_VAR=existing_value\n")
            tmp.flush()

            config = Config(dotenv_path=Path(tmp.name), load_env=False)

            with patch("tux.utils.env.set_key") as mock_set_key:
                config.set("NEW_VAR", "new_value", persist=True)
                mock_set_key.assert_called_once_with(Path(tmp.name), "NEW_VAR", "new_value")

            assert os.environ["NEW_VAR"] == "new_value"

            # Clean up
            Path(tmp.name).unlink(missing_ok=True)

    def test_get_database_url_dev(self):
        """Test getting database URL for development environment."""
        os.environ["DEV_DATABASE_URL"] = "dev_db_url"
        config = Config(load_env=False)
        assert config.get_database_url(Environment.DEVELOPMENT) == "dev_db_url"

    def test_get_database_url_prod(self):
        """Test getting database URL for production environment."""
        os.environ["PROD_DATABASE_URL"] = "prod_db_url"
        config = Config(load_env=False)
        assert config.get_database_url(Environment.PRODUCTION) == "prod_db_url"

    def test_get_database_url_missing(self):
        """Test getting database URL when not configured."""
        config = Config(load_env=False)
        with pytest.raises(ConfigurationError, match="No database URL found"):
            config.get_database_url(Environment.DEVELOPMENT)

    def test_get_bot_token_dev(self):
        """Test getting bot token for development environment."""
        os.environ["DEV_BOT_TOKEN"] = "dev_bot_token"
        config = Config(load_env=False)
        assert config.get_bot_token(Environment.DEVELOPMENT) == "dev_bot_token"

    def test_get_bot_token_prod(self):
        """Test getting bot token for production environment."""
        os.environ["PROD_BOT_TOKEN"] = "prod_bot_token"
        config = Config(load_env=False)
        assert config.get_bot_token(Environment.PRODUCTION) == "prod_bot_token"

    def test_get_bot_token_missing(self):
        """Test getting bot token when not configured."""
        config = Config(load_env=False)
        with pytest.raises(ConfigurationError, match="No bot token found"):
            config.get_bot_token(Environment.DEVELOPMENT)


class TestEnvironmentManager:
    """Test the EnvironmentManager class."""

    @pytest.fixture(autouse=True)
    def reset_environment_manager(self):
        """Reset EnvironmentManager singleton between tests."""
        EnvironmentManager.reset_for_testing()
        yield
        EnvironmentManager.reset_for_testing()

    def test_singleton_pattern(self):
        """Test that EnvironmentManager follows singleton pattern."""
        manager1 = EnvironmentManager()
        manager2 = EnvironmentManager()
        assert manager1 is manager2

    def test_default_environment(self):
        """Test that default environment is DEVELOPMENT."""
        manager = EnvironmentManager()
        assert manager.environment == Environment.DEVELOPMENT

    def test_set_environment(self):
        """Test setting the environment."""
        manager = EnvironmentManager()
        manager.environment = Environment.PRODUCTION
        assert manager.environment == Environment.PRODUCTION

        # Reset for other tests
        manager.environment = Environment.DEVELOPMENT

    def test_set_same_environment(self):
        """Test setting the same environment doesn't change anything."""
        manager = EnvironmentManager()
        original_env = manager.environment
        manager.environment = original_env
        assert manager.environment == original_env

    def test_configure_method(self):
        """Test the configure method."""
        manager = EnvironmentManager()
        manager.configure(Environment.PRODUCTION)
        assert manager.environment == Environment.PRODUCTION

        # Reset for other tests
        manager.configure(Environment.DEVELOPMENT)

    def test_config_property(self):
        """Test the config property returns a Config instance."""
        manager = EnvironmentManager()
        assert isinstance(manager.config, Config)


class TestPublicAPI:
    """Test the public API functions."""

    @staticmethod
    def _clear_test_env_vars():
        """Clear test environment variables."""
        for var in ["DEV_DATABASE_URL", "PROD_DATABASE_URL", "DEV_BOT_TOKEN", "PROD_BOT_TOKEN"]:
            if var in os.environ:
                del os.environ[var]

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Reset environment and clear test variables before and after each test."""
        self._clear_test_env_vars()
        configure_environment(dev_mode=True)
        yield
        self._clear_test_env_vars()
        configure_environment(dev_mode=True)

    def test_is_dev_mode(self):
        """Test is_dev_mode function."""
        configure_environment(dev_mode=True)
        assert is_dev_mode() is True

        configure_environment(dev_mode=False)
        assert is_dev_mode() is False

    def test_is_prod_mode(self):
        """Test is_prod_mode function."""
        configure_environment(dev_mode=True)
        assert is_prod_mode() is False

        configure_environment(dev_mode=False)
        assert is_prod_mode() is True

    def test_get_current_env(self):
        """Test get_current_env function."""
        configure_environment(dev_mode=True)
        assert get_current_env() == "dev"

        configure_environment(dev_mode=False)
        assert get_current_env() == "prod"

    def test_set_env_mode(self):
        """Test set_env_mode function."""
        set_env_mode(dev_mode=True)
        assert is_dev_mode() is True

        set_env_mode(dev_mode=False)
        assert is_prod_mode() is True

    def test_configure_environment(self):
        """Test configure_environment function."""
        configure_environment(dev_mode=True)
        assert is_dev_mode() is True

        configure_environment(dev_mode=False)
        assert is_prod_mode() is True

    def test_get_config(self):
        """Test get_config function."""
        config = get_config()
        assert isinstance(config, Config)

    @patch.dict(os.environ, {"DEV_DATABASE_URL": "dev_db_url"})
    def test_get_database_url(self):
        """Test get_database_url function."""
        configure_environment(dev_mode=True)
        assert get_database_url() == "dev_db_url"

    def test_get_database_url_missing(self):
        """Test get_database_url function when URL is missing."""
        configure_environment(dev_mode=True)
        with pytest.raises(ConfigurationError):
            get_database_url()

    @patch.dict(os.environ, {"DEV_BOT_TOKEN": "dev_bot_token"})
    def test_get_bot_token(self):
        """Test get_bot_token function."""
        configure_environment(dev_mode=True)
        assert get_bot_token() == "dev_bot_token"

    def test_get_bot_token_missing(self):
        """Test get_bot_token function when token is missing."""
        configure_environment(dev_mode=True)
        with pytest.raises(ConfigurationError):
            get_bot_token()


class TestDotenvIntegration:
    """Test dotenv file integration."""

    def test_config_loads_dotenv_file(self):
        """Test that Config loads environment variables from .env file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as tmp:
            tmp.write("TEST_ENV_VAR=test_value\n")
            tmp.write("ANOTHER_VAR=another_value\n")
            tmp.flush()

            # Create config that loads from the temp file
            config = Config(dotenv_path=Path(tmp.name), load_env=True)

            # Check that variables were loaded
            assert config.get("TEST_ENV_VAR") == "test_value"
            assert config.get("ANOTHER_VAR") == "another_value"

            # Clean up
            Path(tmp.name).unlink(missing_ok=True)

    def test_config_skips_nonexistent_dotenv_file(self):
        """Test that Config doesn't fail when .env file doesn't exist."""
        nonexistent_path = Path("/nonexistent/path/.env")
        # This should not raise an exception
        config = Config(dotenv_path=nonexistent_path, load_env=True)
        assert config.dotenv_path == nonexistent_path
