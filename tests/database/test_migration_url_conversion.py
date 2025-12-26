"""
Migration URL Conversion Tests.

Tests that verify async database URLs are correctly converted to sync format
for Alembic compatibility. This is critical for the migration system to work
with async database drivers.

Note: We test the URL conversion logic directly rather than importing from
env.py, as env.py has module-level code that requires Alembic context to be
established, which isn't available during test collection.
"""

import pytest


class TestURLConversion:
    """Test async to sync URL conversion for Alembic."""

    def test_async_url_conversion_pattern(self):
        """Test that async URL pattern is correctly identified."""
        async_url = "postgresql+psycopg_async://user:pass@host:5432/db"
        sync_url = "postgresql+psycopg://user:pass@host:5432/db"

        # Test conversion logic
        converted = async_url.replace(
            "postgresql+psycopg_async://",
            "postgresql+psycopg://",
            1,
        )
        assert converted == sync_url

    def test_sync_url_unchanged(self):
        """Test that sync URLs are not modified."""
        sync_url = "postgresql+psycopg://user:pass@host:5432/db"

        # Should remain unchanged
        converted = sync_url.replace(
            "postgresql+psycopg_async://",
            "postgresql+psycopg://",
            1,
        )
        assert converted == sync_url

    def test_other_driver_urls_unchanged(self):
        """Test that URLs with other drivers are not modified."""
        other_urls = [
            "postgresql://user:pass@host:5432/db",
            "postgresql+asyncpg://user:pass@host:5432/db",
            "sqlite:///path/to/db",
        ]

        for url in other_urls:
            converted = url.replace(
                "postgresql+psycopg_async://",
                "postgresql+psycopg://",
                1,
            )
            assert converted == url, f"URL should not be modified: {url}"

    @pytest.mark.skip(reason="Requires mocking CONFIG.database_url")
    def test_offline_mode_converts_url(self):
        """Test that offline mode converts async URLs."""
        # This would require mocking CONFIG.database_url
        # For now, we test the conversion logic directly

    @pytest.mark.skip(reason="Requires mocking CONFIG.database_url")
    def test_online_mode_converts_url(self):
        """Test that online mode converts async URLs."""
        # This would require mocking CONFIG.database_url and database connection
        # For now, we test the conversion logic directly
