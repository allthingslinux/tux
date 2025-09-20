"""
🧪 Clean Test Configuration

Minimal conftest.py that imports fixtures from fixtures/ directory.
All complex fixture logic has been moved to dedicated fixture files.
"""

import pytest

# Import all fixtures from fixtures directory
from tests.fixtures import *


# =============================================================================
# PYTEST HOOKS
# =============================================================================

def pytest_configure(config):
    """Configure pytest with clean settings and custom logger."""
    import sys
    from pathlib import Path

    # Add src to path
    src_path = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_path))

    from tux.core.logging import configure_testing_logging
    configure_testing_logging()

    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
