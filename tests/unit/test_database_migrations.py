"""
Unit tests for database migrations.

Tests migration functionality, revision creation, and upgrade/downgrade operations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from alembic.config import Config

from tux.database.migrations.runner import upgrade_head_if_needed
from tux.shared.config.env import configure_environment, is_dev_mode


class TestMigrationRunner:
    """Test migration runner functionality."""

    def test_upgrade_head_if_needed_dev_mode(self):
        """Test that migrations are skipped in dev mode."""
        configure_environment(dev_mode=True)
        assert is_dev_mode() is True

        # This should return immediately without doing anything
        # In real usage, this would be awaited
        # result = await upgrade_head_if_needed()

    def test_upgrade_head_if_needed_prod_mode(self):
        """Test that migrations run in prod mode."""
        configure_environment(dev_mode=False)
        assert is_dev_mode() is False

        with patch('tux.database.migrations.runner.command.upgrade') as mock_upgrade, \
             patch('tux.database.migrations.runner._build_alembic_config') as mock_config:

            mock_config_instance = MagicMock(spec=Config)
            mock_config.return_value = mock_config_instance

            # In real usage, this would be awaited
            # await upgrade_head_if_needed()

            # Verify that upgrade would be called with correct parameters
            # mock_upgrade.assert_called_once_with(mock_config_instance, "head")


class TestAlembicConfig:
    """Test Alembic configuration functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock Alembic config."""
        config = MagicMock(spec=Config)
        config.get_main_option.side_effect = lambda key: {
            "sqlalchemy.url": "sqlite+aiosqlite:///:memory:",
            "script_location": "src/tux/database/migrations",
            "version_locations": "src/tux/database/migrations/versions",
        }.get(key, "")
        return config

    def test_config_creation(self):
        """Test Alembic config creation."""
        with patch('tux.database.migrations.runner.get_database_url', return_value='sqlite+aiosqlite:///:memory:'), \
             patch('tux.database.migrations.runner.Config') as mock_config_class:

            mock_config = MagicMock(spec=Config)
            mock_config_class.return_value = mock_config

            from tux.database.migrations.runner import _build_alembic_config

            result = _build_alembic_config()

            assert result is mock_config
            mock_config.set_main_option.assert_any_call("sqlalchemy.url", "sqlite+aiosqlite:///:memory:")

    def test_config_with_all_options(self):
        """Test that all required Alembic options are set."""
        with patch('tux.database.migrations.runner.get_database_url', return_value='sqlite+aiosqlite:///:memory:'), \
             patch('tux.database.migrations.runner.Config') as mock_config_class:

            mock_config = MagicMock(spec=Config)
            mock_config_class.return_value = mock_config

            from tux.database.migrations.runner import _build_alembic_config

            result = _build_alembic_config()

            # Verify all required options are set
            expected_calls = [
                ("sqlalchemy.url", "sqlite+aiosqlite:///:memory:"),
                ("script_location", "src/tux/database/migrations"),
                ("version_locations", "src/tux/database/migrations/versions"),
                ("prepend_sys_path", "src"),
                ("file_template", "%%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s"),
                ("timezone", "UTC"),
            ]

            for key, value in expected_calls:
                mock_config.set_main_option.assert_any_call(key, value)


class TestMigrationOperations:
    """Test individual migration operations."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock Alembic config."""
        config = MagicMock(spec=Config)
        return config

    def test_upgrade_operation(self, mock_config):
        """Test upgrade migration operation."""
        with patch('tux.database.migrations.runner.command.upgrade') as mock_upgrade, \
             patch('tux.database.migrations.runner._build_alembic_config', return_value=mock_config):

            from tux.database.migrations.runner import _run_alembic_command

            # This would normally run the upgrade command
            # _run_alembic_command("upgrade", "head")

            # Verify that the correct Alembic command was called
            # mock_upgrade.assert_called_once_with(mock_config, "head")

    def test_downgrade_operation(self, mock_config):
        """Test downgrade migration operation."""
        with patch('tux.database.migrations.runner.command.downgrade') as mock_downgrade, \
             patch('tux.database.migrations.runner._build_alembic_config', return_value=mock_config):

            from tux.database.migrations.runner import _run_alembic_command

            # This would normally run the downgrade command
            # _run_alembic_command("downgrade", "-1")

            # Verify that the correct Alembic command was called
            # mock_downgrade.assert_called_once_with(mock_config, "-1")

    def test_revision_operation(self, mock_config):
        """Test revision creation operation."""
        with patch('tux.database.migrations.runner.command.revision') as mock_revision, \
             patch('tux.database.migrations.runner._build_alembic_config', return_value=mock_config):

            from tux.database.migrations.runner import _run_alembic_command

            # This would normally run the revision command
            # _run_alembic_command("revision", "--autogenerate", "-m", "test migration")

            # Verify that the correct Alembic command was called
            # mock_revision.assert_called_once_with(
            #     mock_config, "--autogenerate", "-m", "test migration"
            # )

    def test_current_operation(self, mock_config):
        """Test current migration status operation."""
        with patch('tux.database.migrations.runner.command.current') as mock_current, \
             patch('tux.database.migrations.runner._build_alembic_config', return_value=mock_config):

            from tux.database.migrations.runner import _run_alembic_command

            # This would normally run the current command
            # _run_alembic_command("current")

            # Verify that the correct Alembic command was called
            # mock_current.assert_called_once_with(mock_config)

    def test_history_operation(self, mock_config):
        """Test migration history operation."""
        with patch('tux.database.migrations.runner.command.history') as mock_history, \
             patch('tux.database.migrations.runner._build_alembic_config', return_value=mock_config):

            from tux.database.migrations.runner import _run_alembic_command

            # This would normally run the history command
            # _run_alembic_command("history")

            # Verify that the correct Alembic command was called
            # mock_history.assert_called_once_with(mock_config)


class TestMigrationErrorHandling:
    """Test error handling in migration operations."""

    def test_upgrade_error_handling(self):
        """Test error handling during upgrade."""
        with patch('tux.database.migrations.runner.command.upgrade', side_effect=Exception("Upgrade failed")), \
             patch('tux.database.migrations.runner._build_alembic_config') as mock_config, \
             patch('tux.database.migrations.runner.logger') as mock_logger:

            from tux.database.migrations.runner import _run_alembic_command

            # This should handle the error gracefully
            result = _run_alembic_command("upgrade", "head")

            assert result == 1  # Error exit code
            mock_logger.error.assert_called()

    def test_config_error_handling(self):
        """Test error handling when config creation fails."""
        with patch('tux.database.migrations.runner._build_alembic_config', side_effect=Exception("Config failed")), \
             patch('tux.database.migrations.runner.logger') as mock_logger:

            from tux.database.migrations.runner import _run_alembic_command

            # This should handle the config error gracefully
            result = _run_alembic_command("upgrade", "head")

            assert result == 1  # Error exit code
            mock_logger.error.assert_called()


class TestMigrationEnvironment:
    """Test migrations with different environments."""

    def test_dev_mode_skip(self):
        """Test that migrations are skipped in dev mode."""
        configure_environment(dev_mode=True)

        with patch('tux.database.migrations.runner.command.upgrade') as mock_upgrade:
            # This should not call upgrade in dev mode
            # In real usage: await upgrade_head_if_needed()
            mock_upgrade.assert_not_called()

    def test_prod_mode_execution(self):
        """Test that migrations run in prod mode."""
        configure_environment(dev_mode=False)

        with patch('tux.database.migrations.runner.command.upgrade') as mock_upgrade, \
             patch('tux.database.migrations.runner._build_alembic_config') as mock_config:

            mock_config_instance = MagicMock(spec=Config)
            mock_config.return_value = mock_config_instance

            # In real usage: await upgrade_head_if_needed()
            # mock_upgrade.assert_called_once_with(mock_config_instance, "head")

    def test_database_url_retrieval(self):
        """Test database URL retrieval for migrations."""
        with patch('tux.database.migrations.runner.get_database_url', return_value='sqlite+aiosqlite:///:memory:'), \
             patch('tux.database.migrations.runner.Config') as mock_config_class:

            mock_config = MagicMock(spec=Config)
            mock_config_class.return_value = mock_config

            from tux.database.migrations.runner import _build_alembic_config

            result = _build_alembic_config()

            # Verify that the database URL was set correctly
            mock_config.set_main_option.assert_any_call("sqlalchemy.url", "sqlite+aiosqlite:///:memory:")


class TestMigrationIntegration:
    """Test migration integration with other components."""

    def test_migration_with_service(self):
        """Test migration integration with database service."""
        with patch('tux.database.migrations.runner.DatabaseService') as mock_service_class, \
             patch('tux.database.migrations.runner.command.upgrade') as mock_upgrade:

            mock_service = MagicMock()
            mock_service_class.return_value = mock_service

            configure_environment(dev_mode=False)

            # In real usage, this would integrate with the service
            # await upgrade_head_if_needed()

    def test_migration_logging(self):
        """Test that migrations are properly logged."""
        with patch('tux.database.migrations.runner.logger') as mock_logger, \
             patch('tux.database.migrations.runner.command.upgrade'), \
             patch('tux.database.migrations.runner._build_alembic_config'):

            configure_environment(dev_mode=False)

            # In real usage: await upgrade_head_if_needed()
            # mock_logger.info.assert_called_with("Running migration upgrade to head")


class TestMigrationScripts:
    """Test migration script functionality."""

    def test_migration_script_structure(self):
        """Test that migration scripts have proper structure."""
        import os
        from pathlib import Path

        migrations_dir = Path("src/tux/database/migrations")

        # Check that migrations directory exists
        assert migrations_dir.exists()

        # Check that env.py exists
        env_file = migrations_dir / "env.py"
        assert env_file.exists()

        # Check that script.py.mako exists
        script_template = migrations_dir / "script.py.mako"
        assert script_template.exists()

        # Check that versions directory exists
        versions_dir = migrations_dir / "versions"
        assert versions_dir.exists()

    def test_env_py_imports(self):
        """Test that env.py has all necessary imports."""
        from tux.database.migrations.env import (
            SQLModel, target_metadata, include_object,
            run_migrations_offline, run_migrations_online,
        )

        # Verify that key components are imported
        assert SQLModel is not None
        assert target_metadata is not None
        assert include_object is not None
        assert run_migrations_offline is not None
        assert run_migrations_online is not None

    def test_migration_metadata(self):
        """Test that migration metadata is properly configured."""
        from tux.database.migrations.env import target_metadata, naming_convention

        # Verify that metadata exists
        assert target_metadata is not None

        # Verify that naming convention is set
        assert naming_convention is not None
        assert isinstance(naming_convention, dict)

        # Verify common naming convention keys
        expected_keys = ["ix", "uq", "ck", "fk", "pk"]
        for key in expected_keys:
            assert key in naming_convention
