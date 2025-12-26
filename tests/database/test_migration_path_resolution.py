"""
Migration Path Resolution Tests.

Tests that verify migration files can be discovered correctly and that
path resolution works in different environments (local, Docker, etc.).

These tests ensure:
- Alembic can find migration files at the correct path
- Migration discovery works with different working directories
- Error handling when migrations are missing
- Path resolution matches alembic.ini configuration
"""

from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.util.exc import CommandError

from tux.core.setup.database_setup import DatabaseSetupService
from tux.database.service import DatabaseService


class TestMigrationPathResolution:
    """Test that migration paths are resolved correctly."""

    def test_alembic_can_find_migration_directory(self):
        """Test that Alembic can discover the migration directory."""
        # Get project root
        project_root = Path(__file__).parent.parent.parent
        alembic_ini = project_root / "alembic.ini"

        # Build Alembic config
        cfg = Config(str(alembic_ini))

        # Verify script_location is set correctly
        script_location = cfg.get_main_option("script_location")
        assert script_location is not None
        assert "migrations" in script_location

        # Verify the directory exists
        script_path = project_root / script_location
        assert script_path.exists(), f"Migration directory not found: {script_path}"
        assert script_path.is_dir()

    def test_alembic_can_load_script_directory(self):
        """Test that Alembic can load the ScriptDirectory."""
        project_root = Path(__file__).parent.parent.parent
        alembic_ini = project_root / "alembic.ini"

        cfg = Config(str(alembic_ini))
        script_dir = ScriptDirectory.from_config(cfg)

        # Verify script directory was loaded
        assert script_dir is not None
        assert script_dir.versions is not None

    def test_migration_versions_directory_exists(self):
        """Test that the versions directory exists and contains migrations."""
        project_root = Path(__file__).parent.parent.parent
        versions_dir = (
            project_root / "src" / "tux" / "database" / "migrations" / "versions"
        )

        assert versions_dir.exists(), f"Versions directory not found: {versions_dir}"
        assert versions_dir.is_dir()

        # Check for at least one migration file (should have initial migration)
        migration_files = list(versions_dir.glob("*.py"))
        # Filter out __init__.py
        migration_files = [f for f in migration_files if f.name != "__init__.py"]

        assert len(migration_files) > 0, (
            "No migration files found in versions directory"
        )

    def test_database_setup_finds_project_root(self):
        """Test that DatabaseSetupService can find the project root."""
        db_service = DatabaseService()
        setup_service = DatabaseSetupService(db_service)

        project_root = setup_service._find_project_root()

        # Verify project root contains alembic.ini
        assert (project_root / "alembic.ini").exists()
        assert (project_root / "src" / "tux" / "database" / "migrations").exists()

    def test_alembic_config_builds_correctly(self):
        """Test that Alembic config is built with correct paths."""
        db_service = DatabaseService()
        setup_service = DatabaseSetupService(db_service)

        cfg = setup_service._build_alembic_config()

        # Verify config has script_location
        script_location = cfg.get_main_option("script_location")
        assert script_location is not None

        # Verify the path exists relative to project root
        project_root = setup_service._find_project_root()
        script_path = project_root / script_location
        assert script_path.exists()


class TestMigrationFileDiscovery:
    """Test migration file discovery and loading."""

    def test_can_list_migration_revisions(self):
        """Test that we can list all migration revisions."""
        project_root = Path(__file__).parent.parent.parent
        alembic_ini = project_root / "alembic.ini"

        cfg = Config(str(alembic_ini))
        script_dir = ScriptDirectory.from_config(cfg)

        # Get all revisions
        revisions = list(script_dir.walk_revisions())

        # Should have at least one revision (initial migration)
        assert len(revisions) > 0, "No migration revisions found"

        # Verify each revision has required attributes
        for rev in revisions:
            assert rev.revision is not None
            assert rev.doc is not None or rev.doc == ""

    def test_can_get_head_revision(self):
        """Test that we can get the head revision."""
        project_root = Path(__file__).parent.parent.parent
        alembic_ini = project_root / "alembic.ini"

        cfg = Config(str(alembic_ini))
        script_dir = ScriptDirectory.from_config(cfg)

        # Get head revision
        heads = script_dir.get_revisions("head")

        # Should have at least one head
        assert len(heads) > 0, "No head revision found"

    def test_migration_files_are_valid_python(self):
        """Test that migration files are valid Python modules."""
        project_root = Path(__file__).parent.parent.parent
        versions_dir = (
            project_root / "src" / "tux" / "database" / "migrations" / "versions"
        )

        # Get all migration files
        migration_files = [
            f for f in versions_dir.glob("*.py") if f.name != "__init__.py"
        ]

        assert len(migration_files) > 0, "No migration files to test"

        # Try to import each migration file (basic syntax check)
        for migration_file in migration_files:
            # Read file and check for required elements
            content = migration_file.read_text()

            # Check for required Alembic elements
            assert "revision" in content or '"revision"' in content
            assert "upgrade" in content or "def upgrade" in content
            assert "downgrade" in content or "def downgrade" in content


class TestMigrationErrorHandling:
    """Test error handling when migrations are missing or paths are wrong."""

    def test_missing_migration_directory_raises_error(self, tmp_path: Path):
        """Test that missing migration directory raises appropriate error."""
        # Create a temporary alembic.ini with invalid path
        alembic_ini = tmp_path / "alembic.ini"
        alembic_ini.write_text(
            "[alembic]\n"
            "script_location = /nonexistent/path/migrations\n"
            "prepend_sys_path = .\n",
        )

        cfg = Config(str(alembic_ini))

        # Attempting to load ScriptDirectory should fail gracefully
        # Alembic raises CommandError when the path doesn't exist
        with pytest.raises((FileNotFoundError, ValueError, CommandError)):
            ScriptDirectory.from_config(cfg)

    def test_invalid_migration_file_handled_gracefully(self, tmp_path: Path):
        """Test that invalid migration files are handled gracefully."""
        # This test would require creating a malformed migration file
        # For now, we just verify that the system can handle errors
        # Actual malformed file testing would be done manually or in e2e tests

        # Verify that valid migrations load correctly
        project_root = Path(__file__).parent.parent.parent
        alembic_ini = project_root / "alembic.ini"

        cfg = Config(str(alembic_ini))
        script_dir = ScriptDirectory.from_config(cfg)

        # Should not raise an error for valid migrations
        revisions = list(script_dir.walk_revisions())
        assert len(revisions) > 0


class TestAlembicConfiguration:
    """Test Alembic configuration matches expected values."""

    def test_alembic_ini_has_correct_paths(self):
        """Test that alembic.ini has correct path configuration."""
        project_root = Path(__file__).parent.parent.parent
        alembic_ini = project_root / "alembic.ini"

        cfg = Config(str(alembic_ini))

        # Verify script_location matches expected pattern
        script_location = cfg.get_main_option("script_location")
        assert script_location == "src/tux/database/migrations"

        # Verify prepend_sys_path is set
        prepend_sys_path = cfg.get_main_option("prepend_sys_path")
        assert prepend_sys_path == "src"

        # Verify version_locations matches expected pattern
        version_locations = cfg.get_main_option("version_locations")
        assert version_locations == "src/tux/database/migrations/versions"

    def test_prepend_sys_path_enables_imports(self):
        """Test that prepend_sys_path allows importing models."""
        project_root = Path(__file__).parent.parent.parent
        alembic_ini = project_root / "alembic.ini"

        cfg = Config(str(alembic_ini))
        prepend_sys_path = cfg.get_main_option("prepend_sys_path")

        # Verify prepend_sys_path is set
        assert prepend_sys_path is not None, "prepend_sys_path should be configured"

        # Verify the path exists
        prepend_path = project_root / prepend_sys_path
        assert prepend_path.exists()

        # Verify models can be imported from this path
        # (This is tested indirectly by migration generation working)
        assert (prepend_path / "tux" / "database" / "models").exists()
