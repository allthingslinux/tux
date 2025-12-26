"""
🚀 Database Timestamp Functionality Tests - SQLModel + py-pglite Unit Testing.

Tests for timestamp mixin and automatic timestamp functionality.
"""

from typing import get_type_hints

import pytest

from tests.fixtures import TEST_GUILD_ID
from tux.core.permission_system import DEFAULT_RANKS
from tux.core.permission_system import DEFAULT_RANKS as CORE_DEFAULTS
from tux.database.models.base import BaseModel, TimestampMixin
from tux.database.models.models import Guild, PermissionRank
from tux.database.service import DatabaseService
from tux.modules.config.ranks import DEFAULT_RANKS as CMD_DEFAULTS
from tux.ui.views.config.ranks import DEFAULT_RANKS as UI_DEFAULTS


class TestTimestampFunctionality:
    """🕐 Test TimestampMixin and automatic timestamp functionality."""

    @pytest.mark.unit
    def test_timestamp_mixin_fields(self) -> None:
        """Test TimestampMixin has the correct field definitions."""
        # Check that TimestampMixin defines the expected fields
        annotations = TimestampMixin.__annotations__

        assert "created_at" in annotations
        assert "updated_at" in annotations

        # Check field types
        created_at_type = str(annotations["created_at"])
        updated_at_type = str(annotations["updated_at"])

        assert "datetime" in created_at_type.lower()
        assert "datetime" in updated_at_type.lower()
        assert "None" in created_at_type  # Optional type

    @pytest.mark.unit
    def test_base_model_inherits_timestamps(self) -> None:
        """Test BaseModel properly inherits timestamp fields from TimestampMixin."""
        # BaseModel should inherit from TimestampMixin
        assert issubclass(BaseModel, TimestampMixin)

        # Check that BaseModel has the timestamp fields via MRO
        # The fields are defined in TimestampMixin, so they should be accessible
        # through the class hierarchy
        assert hasattr(BaseModel, "created_at")
        assert hasattr(BaseModel, "updated_at")

        # Check that the field annotations are accessible
        # Since SQLModel uses Mapped types, we check the model fields
        # get_type_hints is already imported from typing at module level
        hints = get_type_hints(BaseModel)
        assert "created_at" in hints
        assert "updated_at" in hints

    @pytest.mark.unit
    def test_permission_rank_has_timestamps(self) -> None:
        """Test PermissionRank model inherits timestamp fields."""
        # PermissionRank should inherit from BaseModel
        assert issubclass(PermissionRank, BaseModel)
        assert issubclass(PermissionRank, TimestampMixin)

        # Test instance creation
        rank = PermissionRank(
            guild_id=TEST_GUILD_ID,
            rank=0,
            name="Test Rank",
            description="Test description",
        )

        # Fields should exist on the instance
        assert hasattr(rank, "created_at")
        assert hasattr(rank, "updated_at")

        # Initially None (database-managed)
        assert rank.created_at is None
        assert rank.updated_at is None

        # Fields should be in __dict__ after model_post_init
        assert "created_at" in rank.__dict__
        assert "updated_at" in rank.__dict__

    @pytest.mark.unit
    def test_timestamp_dict_compatibility(self) -> None:
        """Test timestamp fields are accessible in model __dict__."""
        rank = PermissionRank(
            guild_id=TEST_GUILD_ID,
            rank=0,
            name="Test Rank",
            description="Test description",
        )

        # Timestamp fields should be in __dict__ for SQLAlchemy compatibility
        assert "created_at" in rank.__dict__
        assert "updated_at" in rank.__dict__

        # Values should be None initially
        assert rank.__dict__["created_at"] is None
        assert rank.__dict__["updated_at"] is None

    @pytest.mark.unit
    def test_timestamp_serialization(self) -> None:
        """Test timestamp fields are included in to_dict() serialization."""
        rank = PermissionRank(
            guild_id=TEST_GUILD_ID,
            rank=0,
            name="Test Rank",
            description="Test description",
        )

        data = rank.to_dict()

        # Timestamp fields should be in serialized data
        assert "created_at" in data
        assert "updated_at" in data

        # Initially None, so should be None in dict
        assert data["created_at"] is None
        assert data["updated_at"] is None

    @pytest.mark.unit
    async def test_timestamp_database_operations(
        self,
        db_service: DatabaseService,
    ) -> None:
        """Test timestamp fields work correctly with database operations."""
        async with db_service.session() as session:
            # Create guild first (foreign key requirement)
            guild = Guild(id=TEST_GUILD_ID, case_count=0)
            session.add(guild)
            await session.commit()

            # Create permission rank
            rank = PermissionRank(
                guild_id=TEST_GUILD_ID,
                rank=5,
                name="Test Admin",
                description="Test administrator rank",
            )
            session.add(rank)
            await session.commit()
            await session.refresh(rank)

            # After database refresh, timestamps should still be in __dict__
            assert "created_at" in rank.__dict__
            assert "updated_at" in rank.__dict__

            # to_dict should include timestamps
            data = rank.to_dict()
            assert "created_at" in data
            assert "updated_at" in data

    @pytest.mark.unit
    def test_default_ranks_single_source_of_truth(self) -> None:
        """Test that DEFAULT_RANKS is the single source of truth."""
        # All should reference the same object
        assert CORE_DEFAULTS is UI_DEFAULTS
        assert UI_DEFAULTS is CMD_DEFAULTS

        # Should have exactly 8 ranks (0-7)
        assert len(DEFAULT_RANKS) == 8
        assert set(DEFAULT_RANKS.keys()) == {0, 1, 2, 3, 4, 5, 6, 7}

        # Check specific rank data
        assert DEFAULT_RANKS[0]["name"] == "Member"
        assert DEFAULT_RANKS[7]["name"] == "Server Owner"

        # All ranks should have name and description
        for rank_data in DEFAULT_RANKS.values():
            assert "name" in rank_data
            assert "description" in rank_data
            assert isinstance(rank_data["name"], str)
            assert isinstance(rank_data["description"], str)

    @pytest.mark.unit
    def test_timestamp_mixin_no_application_defaults(self) -> None:
        """Test that TimestampMixin doesn't set application-level defaults."""
        # Create instance without any data
        rank = PermissionRank.__new__(PermissionRank)

        # Before initialization, fields might not exist
        # After proper initialization, they should be None (not set by application)
        rank.__init__(
            guild_id=TEST_GUILD_ID,
            rank=0,
            name="Test Rank",
            description="Test description",
        )

        # Timestamps should be None, not datetime objects (database-managed)
        assert rank.created_at is None
        assert rank.updated_at is None

        # But they should be in __dict__ for compatibility
        assert "created_at" in rank.__dict__
        assert "updated_at" in rank.__dict__
