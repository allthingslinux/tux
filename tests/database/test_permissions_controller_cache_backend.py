"""Unit tests for permission controllers with cache backend (Valkey/in-memory)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tux.database.controllers.permissions import PermissionRankController
from tux.database.models.models import PermissionRank

pytestmark = pytest.mark.unit

TEST_GUILD_ID = 123456789


@pytest.fixture
def mock_backend() -> MagicMock:
    """Async cache backend mock."""
    backend = MagicMock()
    backend.get = AsyncMock(return_value=None)
    backend.set = AsyncMock()
    backend.delete = AsyncMock()
    return backend


@pytest.fixture
def mock_db() -> MagicMock:
    """Database service mock (no real DB)."""
    return MagicMock()


@pytest.mark.asyncio
async def test_get_permission_ranks_by_guild_returns_cached_from_backend(
    mock_backend: MagicMock,
    mock_db: MagicMock,
) -> None:
    """When backend has cached list, get_permission_ranks_by_guild returns it without DB."""
    now = datetime.now(UTC).isoformat()
    cached = [
        {
            "id": 1,
            "guild_id": TEST_GUILD_ID,
            "rank": 1,
            "name": "Member",
            "description": None,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": 2,
            "guild_id": TEST_GUILD_ID,
            "rank": 3,
            "name": "Mod",
            "description": "Moderator",
            "created_at": now,
            "updated_at": now,
        },
    ]
    mock_backend.get = AsyncMock(return_value=cached)
    controller = PermissionRankController(db=mock_db, cache_backend=mock_backend)
    result = await controller.get_permission_ranks_by_guild(TEST_GUILD_ID)
    assert len(result) == 2
    assert result[0].rank == 1
    assert result[0].name == "Member"
    assert result[1].rank == 3
    assert result[1].name == "Mod"
    mock_backend.get.assert_called_once()
    mock_db.session.assert_not_called()


@pytest.mark.asyncio
async def test_get_permission_ranks_by_guild_misses_backend_then_sets(
    mock_backend: MagicMock,
    mock_db: MagicMock,
) -> None:
    """When backend returns None, controller fetches (mocked) and caches via backend."""
    mock_backend.get = AsyncMock(return_value=None)
    controller = PermissionRankController(db=mock_db, cache_backend=mock_backend)
    with patch.object(
        controller,
        "find_all",
        new_callable=AsyncMock,
        return_value=[],
    ):
        result = await controller.get_permission_ranks_by_guild(TEST_GUILD_ID)
    assert result == []
    mock_backend.set.assert_called_once()


@pytest.mark.asyncio
async def test_create_permission_rank_invalidates_backend(
    mock_backend: MagicMock,
    mock_db: MagicMock,
) -> None:
    """create_permission_rank invalidates backend cache keys on success."""
    rank = PermissionRank(
        id=1,
        guild_id=TEST_GUILD_ID,
        rank=2,
        name="Mod",
        description="Moderator",
    )
    controller = PermissionRankController(db=mock_db, cache_backend=mock_backend)
    with patch.object(
        controller,
        "create",
        new_callable=AsyncMock,
        return_value=rank,
    ):
        await controller.create_permission_rank(
            guild_id=TEST_GUILD_ID,
            rank=2,
            name="Mod",
            description="Moderator",
        )
    assert mock_backend.delete.called
    call_args_list = mock_backend.delete.call_args_list
    keys_deleted = [c[0][0] for c in call_args_list if c[0]]
    assert any("permission_ranks" in k for k in keys_deleted)
