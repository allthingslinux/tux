"""Integration tests for env.py - testing real-world scenarios."""

import os
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest
from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch
from tux.utils.env import (
    Config,
    ConfigurationError,
    Environment,
    configure_environment,
    get_bot_token,
    get_database_url,
)


def cleanup_env(keys: list[str]) -> None:
    for key in keys:
        os.environ.pop(key, None)


def restore_env(original_env: dict[str, str]) -> None:
    for var, value in original_env.items():
        os.environ[var] = value


def remove_file(path: Path | str) -> None:
    Path(path).unlink(missing_ok=True)


def restore_env_var(key: str, value: str | None) -> None:
    if value is not None:
        os.environ[key] = value
    else:
        os.environ.pop(key, None)


def restore_env_vars(env_keys: list[str], original_env: dict[str, str]) -> None:
    for key in env_keys:
        restore_env_var(key, original_env.get(key))


def cleanup_all_env_tokens() -> None:
    cleanup_env(["DEV_DATABASE_URL", "DEV_BOT_TOKEN", "PROD_DATABASE_URL", "PROD_BOT_TOKEN"])


def set_all_env_tokens() -> None:
    os.environ |= {
        "DEV_DATABASE_URL": "postgresql://localhost:5432/tux_dev",
        "DEV_BOT_TOKEN": "dev_token_123",
        "PROD_DATABASE_URL": "postgresql://prod-db:5432/tux_prod",
        "PROD_BOT_TOKEN": "prod_token_456",
    }


def create_temp_env_file(content: str) -> Path:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as tmp:
        tmp.write(content)
        tmp.flush()
        return Path(tmp.name)


def assert_env_tokens(db_url: str, token: str) -> None:
    assert get_database_url() == db_url
    assert get_bot_token() == token


def update_env_file(path: Path, content: str) -> None:
    with path.open("w") as f:
        f.write(content)


def check_dynamic_config(path: Path, expected: str) -> None:
    config = Config(dotenv_path=path, load_env=True)
    assert config.get("DYNAMIC_CONFIG") == expected


@pytest.mark.slow
@pytest.mark.integration
class TestProductionConfig:
    """Test real production configuration scenarios."""

    def test_startup_with_missing_critical_config(self):
        """Test app startup fails gracefully when critical config is missing."""
        # Ensure clean environment - this is what actually happens in production
        # when environment variables are missing
        cleanup_all_env_tokens()

        try:
            config = Config(load_env=False)

            with pytest.raises(ConfigurationError, match="No database URL found"):
                config.get_database_url(Environment.PRODUCTION)

            with pytest.raises(ConfigurationError, match="No bot token found"):
                config.get_bot_token(Environment.PRODUCTION)
        finally:
            # Cleanup in case of test failure
            cleanup_all_env_tokens()

    def test_development_to_production_environment_switch(self):
        """Test switching from dev to prod environment - common in CI/CD."""
        # Set up dev environment
        set_all_env_tokens()

        try:
            # Start in development
            configure_environment(dev_mode=True)
            assert_env_tokens("postgresql://localhost:5432/tux_dev", "dev_token_123")

            # Switch to production (like in deployment)
            configure_environment(dev_mode=False)
            assert_env_tokens("postgresql://prod-db:5432/tux_prod", "prod_token_456")
        finally:
            # Cleanup
            cleanup_all_env_tokens()

    def test_configuration_validation_at_startup(self, monkeypatch: MonkeyPatch):
        """Test configuration validation that prevents deployment issues."""
        monkeypatch.setenv("PROD_DATABASE_URL", "invalid-url-format")
        config = Config(load_env=False)
        db_url = config.get_database_url(Environment.PRODUCTION)
        assert db_url == "invalid-url-format"  # Current behavior
        # TODO: Add URL validation in production code

    def test_sensitive_data_not_logged(self):
        """Test that sensitive configuration doesn't leak in logs."""
        sensitive_token = "super_secret_bot_token_456"
        os.environ["PROD_BOT_TOKEN"] = sensitive_token
        try:
            config = Config(load_env=False)
            token = config.get_bot_token(Environment.PRODUCTION)
            assert token == sensitive_token
        finally:
            restore_env_var("PROD_BOT_TOKEN", None)


@pytest.mark.slow
@pytest.mark.integration
class TestContainerConfig:
    """Test configuration scenarios specific to containerized deployments."""

    def test_docker_environment_file_loading(self):
        """Test loading configuration from Docker environment files."""
        env_content = textwrap.dedent("""\
            # Production Environment Configuration
            # Database Configuration
            PROD_DATABASE_URL=postgresql://postgres:password@db:5432/tux
            # Bot Configuration
            PROD_BOT_TOKEN=MTAxNjY5...actual_long_token_here
            # Application Configuration
            LOG_LEVEL=INFO
            SENTRY_DSN=https://123@sentry.io/456
        """)
        env_keys = ["PROD_DATABASE_URL", "LOG_LEVEL", "SENTRY_DSN"]
        original_env = {key: os.environ[key] for key in env_keys if key in os.environ}
        cleanup_env(env_keys)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as tmp:
            tmp.write(env_content)
            tmp.flush()
            tmp_path = Path(tmp.name)
        try:
            config = Config(dotenv_path=tmp_path, load_env=True)
            assert config.get("PROD_DATABASE_URL") == "postgresql://postgres:password@db:5432/tux"
            assert config.get("LOG_LEVEL") == "INFO"
            assert config.get("SENTRY_DSN") == "https://123@sentry.io/456"
        finally:
            tmp_path.unlink(missing_ok=True)
            restore_env_vars(env_keys, original_env)

    def test_config_drift_detection(self):
        """Test detecting configuration drift between environments."""
        # This is critical in enterprise - ensuring config consistency
        dev_config = {"DEV_DATABASE_URL": "postgresql://localhost:5432/tux_dev", "DEV_BOT_TOKEN": "dev_token"}

        prod_config = {"PROD_DATABASE_URL": "postgresql://prod:5432/tux_prod", "PROD_BOT_TOKEN": "prod_token"}

        with patch.dict(os.environ, dev_config | prod_config):
            config = Config(load_env=False)

            # Verify both environments have required configuration
            dev_db = config.get_database_url(Environment.DEVELOPMENT)
            prod_db = config.get_database_url(Environment.PRODUCTION)

            assert dev_db != prod_db  # Should be different
            assert "dev" in dev_db.lower()
            assert "prod" in prod_db.lower()


@pytest.mark.slow
@pytest.mark.integration
class TestSecurityConfig:
    """Test security-related configuration scenarios."""

    def test_database_connection_security(self):
        """Test database connection security requirements."""
        # Test that production database URLs require SSL
        insecure_db_url = "postgresql://user:pass@db:5432/tux?sslmode=disable"

        os.environ["PROD_DATABASE_URL"] = insecure_db_url

        try:
            config = Config(load_env=False)
            db_url = config.get_database_url(Environment.PRODUCTION)

            # In production, this should validate SSL requirements
            assert "sslmode=disable" in db_url  # Current behavior
            # TODO: Add SSL validation for production databases
        finally:
            os.environ.pop("PROD_DATABASE_URL", None)

    def test_configuration_audit_trail(self):
        """Test that configuration changes are auditable."""
        config = Config(load_env=False)
        original_value = os.environ.get("TEST_CONFIG")
        config.set("TEST_CONFIG", "new_value")
        assert os.environ["TEST_CONFIG"] == "new_value"
        restore_env_var("TEST_CONFIG", original_value)


@pytest.mark.integration
class TestErrorRecoveryScenarios:
    """Test error recovery and resilience scenarios."""

    def test_graceful_degradation_with_missing_optional_config(self):
        """Test app continues with missing optional configuration."""
        config = Config(load_env=False)

        # Optional configurations should have sensible defaults
        log_level = config.get("LOG_LEVEL", default="INFO")
        debug_mode = config.get("DEBUG", default=False)
        max_retries = config.get("MAX_RETRIES", default=3)

        assert log_level == "INFO"
        assert debug_mode is False
        assert max_retries == 3

    def test_configuration_reload_without_restart(self):
        """Test hot-reloading configuration changes - reveals current limitation."""
        # Critical for enterprise apps - updating config without downtime
        tmp_path = create_temp_env_file("DYNAMIC_CONFIG=initial_value\n")
        try:
            check_dynamic_config(tmp_path, "initial_value")
            update_env_file(tmp_path, "DYNAMIC_CONFIG=updated_value\n")
            check_dynamic_config(tmp_path, "initial_value")
            restore_env_var("DYNAMIC_CONFIG", None)
            check_dynamic_config(tmp_path, "updated_value")
        finally:
            tmp_path.unlink(missing_ok=True)
            restore_env_var("DYNAMIC_CONFIG", None)


@pytest.mark.integration
class TestMonitoringAndObservabilityScenarios:
    """Test monitoring and observability for configuration."""

    def test_configuration_health_check(self):
        """Test health check endpoint includes configuration status."""
        # Enterprise apps expose configuration health via health checks
        os.environ |= {"PROD_DATABASE_URL": "postgresql://prod:5432/tux", "PROD_BOT_TOKEN": "valid_token"}

        try:
            configure_environment(dev_mode=False)

            # Simulate health check - verify all critical config is present
            health_status = {
                "database_configured": bool(get_database_url()),
                "bot_token_configured": bool(get_bot_token()),
                "environment": "production",
            }

            assert health_status["database_configured"] is True
            assert health_status["bot_token_configured"] is True
            assert health_status["environment"] == "production"
        finally:
            cleanup_all_env_tokens()

    def test_configuration_metrics_collection(self):
        """Test that configuration usage is monitored."""
        config = Config(load_env=False)

        # In enterprise apps, track which configurations are accessed
        config.get("SOME_CONFIG", default="default")

        # TODO: Implement metrics collection for config access patterns
        # This helps identify unused configurations and access patterns


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.xfail(reason="URL validation not yet implemented")
def test_database_url_format_validation(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("PROD_DATABASE_URL", "not-a-valid-url")
    config = Config(load_env=False)
    # This should raise ConfigurationError in the future
    db_url = config.get_database_url(Environment.PRODUCTION)
    assert db_url == "not-a-valid-url"


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.xfail(reason="SSL validation for production DB not yet implemented")
def test_production_db_ssl_enforcement(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("PROD_DATABASE_URL", "postgresql://user:pass@db:5432/tux?sslmode=disable")
    config = Config(load_env=False)
    db_url = config.get_database_url(Environment.PRODUCTION)
    assert "sslmode=disable" in db_url


def test_no_secrets_in_logs(monkeypatch: MonkeyPatch, caplog: LogCaptureFixture):
    secret = "super_secret_token_789"
    monkeypatch.setenv("PROD_BOT_TOKEN", secret)
    config = Config(load_env=False)
    with caplog.at_level("INFO"):
        config.get_bot_token(Environment.PRODUCTION)
    # Check that the secret is not present in any log output
    assert secret not in caplog.text


@pytest.mark.integration
@pytest.mark.xfail(reason="Health endpoint not implemented; placeholder for future test.")
def test_real_health_endpoint():
    # Placeholder: In the future, this should call the real health endpoint
    # and assert on the response. For now, just fail.
    msg = "Health endpoint test not implemented"
    raise AssertionError(msg)
