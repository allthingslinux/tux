"""
🚀 Version Module Version Tests - Module Version Constant Testing.

Tests for the module-level __version__ constant.
"""

from tux import __version__
from tux.shared.version import get_version


class TestModuleVersion:
    """Test the module-level __version__ constant."""

    def test_version_is_available(self) -> None:
        """Test that __version__ is available and valid."""
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_version_is_not_placeholder(self) -> None:
        """Test that __version__ is not a placeholder value."""
        assert __version__ not in ("0.0.0", "0.0", "unknown")

    def test_version_consistency(self) -> None:
        """Test that __version__ is consistent with get_version()."""
        assert __version__ == get_version()
