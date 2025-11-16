"""
🧪 Clean Test Configuration

Minimal conftest.py that imports fixtures from fixtures/ directory.
All complex fixture logic has been moved to dedicated fixture files.
"""

# Import all fixtures from fixtures directory
from tests.fixtures import *


# =============================================================================
# PYTEST HOOKS
# =============================================================================

def pytest_configure(config):
    """Configure pytest with clean settings and custom logger."""
    import sys
    from pathlib import Path

    # Add src to path (redundant with pyproject.toml pythonpath, but kept for explicit clarity)
    src_path = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_path))

    from tux.core.logging import configure_testing_logging
    configure_testing_logging()

    # Markers are defined in pyproject.toml [tool.pytest.ini_options.markers]
    # No need to duplicate here - pytest will read them from pyproject.toml
