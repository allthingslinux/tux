"""Unit tests for PermissionSetupService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tux.core.setup.permission_setup import PermissionSetupService

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_setup_initializes_db_coordinator_with_cache_backend() -> None:
    """Setup gets cache backend, creates DatabaseCoordinator with it, and calls init_permission_system."""
    mock_bot = MagicMock()
    mock_bot._db_coordinator = None
    mock_db_service = MagicMock()
    mock_backend = MagicMock()
    mock_coordinator = MagicMock()
    with (
        patch(
            "tux.core.setup.permission_setup.get_cache_backend",
            return_value=mock_backend,
        ),
        patch(
            "tux.core.setup.permission_setup.DatabaseCoordinator",
            return_value=mock_coordinator,
        ) as mock_coord_cls,
        patch(
            "tux.core.setup.permission_setup.init_permission_system",
        ) as mock_init,
    ):
        service = PermissionSetupService(mock_bot, mock_db_service)
        await service.setup()
    mock_coord_cls.assert_called_once_with(
        mock_db_service,
        cache_backend=mock_backend,
    )
    assert mock_bot._db_coordinator is mock_coordinator
    mock_init.assert_called_once_with(mock_bot, mock_coordinator)
