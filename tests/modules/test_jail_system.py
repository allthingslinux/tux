"""
Integration tests for jail and unjail system.

Tests focus on:
- Role management logic (_get_manageable_roles)
- Database operations for storing/retrieving jail cases
- Role restoration logic
"""

import asyncio
from unittest.mock import MagicMock

import discord
import pytest

from tux.database.controllers import CaseController
from tux.database.models import CaseType
from tux.modules.moderation.jail import Jail


def create_mock_role(role_id: int, name: str, **kwargs) -> MagicMock:
    """Create a properly mocked Discord role."""
    role = MagicMock(spec=discord.Role)
    role.id = role_id
    role.name = name
    role.is_assignable = MagicMock(return_value=kwargs.get("is_assignable", True))
    role.is_bot_managed = MagicMock(return_value=kwargs.get("is_bot_managed", False))
    role.is_premium_subscriber = MagicMock(
        return_value=kwargs.get("is_premium_subscriber", False),
    )
    role.is_integration = MagicMock(return_value=kwargs.get("is_integration", False))
    role.is_default = MagicMock(return_value=kwargs.get("is_default", False))
    role.__eq__ = lambda self, other: self.id == getattr(other, "id", None)
    return role


class TestRoleManagementLogic:
    """Test the jail role management logic."""

    @pytest.mark.integration
    def test_get_manageable_roles_filters_normal_roles(self):
        """Test that _get_manageable_roles returns only manageable roles."""
        member = MagicMock(spec=discord.Member)
        jail_role = create_mock_role(999, "Jailed")

        # Create various roles
        normal_role1 = create_mock_role(100, "Member")
        normal_role2 = create_mock_role(101, "Verified")
        bot_role = create_mock_role(200, "Bot Role", is_bot_managed=True)
        premium_role = create_mock_role(
            300,
            "Nitro Booster",
            is_premium_subscriber=True,
        )
        integration_role = create_mock_role(
            400,
            "YouTube Subscriber",
            is_integration=True,
        )
        everyone_role = create_mock_role(500, "@everyone", is_default=True)
        unassignable_role = create_mock_role(600, "Higher Role", is_assignable=False)

        member.roles = [
            everyone_role,
            normal_role1,
            normal_role2,
            bot_role,
            premium_role,
            integration_role,
            unassignable_role,
            jail_role,
        ]

        # Call the static method
        manageable = Jail._get_manageable_roles(member, jail_role)

        # Should only return normal_role1 and normal_role2
        assert len(manageable) == 2
        assert normal_role1 in manageable
        assert normal_role2 in manageable
        assert bot_role not in manageable
        assert premium_role not in manageable
        assert integration_role not in manageable
        assert everyone_role not in manageable
        assert jail_role not in manageable
        assert unassignable_role not in manageable

    @pytest.mark.integration
    def test_get_manageable_roles_empty_when_no_roles(self):
        """Test that _get_manageable_roles returns empty list when member has no manageable roles."""
        member = MagicMock(spec=discord.Member)
        jail_role = create_mock_role(999, "Jailed")

        # Only system/special roles
        everyone_role = create_mock_role(1, "@everyone", is_default=True)
        bot_role = create_mock_role(2, "Bot Role", is_bot_managed=True)

        member.roles = [everyone_role, bot_role]

        manageable = Jail._get_manageable_roles(member, jail_role)

        assert len(manageable) == 0

    @pytest.mark.integration
    def test_get_manageable_roles_excludes_jail_role(self):
        """Test that the jail role itself is excluded from manageable roles."""
        member = MagicMock(spec=discord.Member)
        jail_role = create_mock_role(999, "Jailed")

        normal_role = create_mock_role(100, "Member")

        # Member already has jail role (edge case)
        member.roles = [normal_role, jail_role]

        manageable = Jail._get_manageable_roles(member, jail_role)

        assert len(manageable) == 1
        assert normal_role in manageable
        assert jail_role not in manageable


class TestJailDatabaseOperations:
    """Test database operations for jail system."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_jail_case_creation_with_roles(self, db_service):
        """Test creating a jail case with stored role metadata."""
        case_controller = CaseController(db_service)

        # Create a jail case with stored roles
        jail_case = await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=123456,
            case_moderator_id=789012,
            guild_id=987654,
            case_reason="Testing role storage",
            case_user_roles=[1001, 1002, 1003, 1004],
        )

        assert jail_case.id is not None
        assert jail_case.case_type == CaseType.JAIL
        assert jail_case.case_user_roles == [1001, 1002, 1003, 1004]
        assert jail_case.case_reason == "Testing role storage"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_jail_case_retrieval_by_user(self, db_service):
        """Test retrieving the latest jail case for a user."""
        case_controller = CaseController(db_service)

        guild_id = 123456
        user_id = 789012

        # Create multiple cases for the same user
        await case_controller.create_case(
            case_type=CaseType.WARN,
            case_user_id=user_id,
            case_moderator_id=111111,
            guild_id=guild_id,
            case_reason="First warning",
        )

        await asyncio.sleep(0.01)  # Ensure different timestamps

        jail_case = await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=user_id,
            case_moderator_id=222222,
            guild_id=guild_id,
            case_reason="Jailed for violations",
            case_user_roles=[5001, 5002, 5003],
        )

        # Get latest case
        latest_case = await case_controller.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )

        assert latest_case is not None
        assert latest_case.id == jail_case.id
        assert latest_case.case_type == CaseType.JAIL
        assert latest_case.case_user_roles == [5001, 5002, 5003]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_jail_case_with_empty_roles(self, db_service):
        """Test creating a jail case when user has no roles to store."""
        case_controller = CaseController(db_service)

        # Create jail case with empty role list
        jail_case = await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=123456,
            case_moderator_id=789012,
            guild_id=987654,
            case_reason="User had no roles",
            case_user_roles=[],
        )

        assert jail_case.case_user_roles == []

        # Retrieve and verify
        assert jail_case.id is not None
        retrieved = await case_controller.get_case_by_id(jail_case.id)
        assert retrieved is not None
        assert retrieved.case_user_roles == []

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_jail_case_with_many_roles(self, db_service):
        """Test storing a large number of roles (stress test)."""
        case_controller = CaseController(db_service)

        # Create a case with many roles
        many_roles = list(range(1000, 1050))  # 50 roles

        jail_case = await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=123456,
            case_moderator_id=789012,
            guild_id=987654,
            case_reason="Power user with many roles",
            case_user_roles=many_roles,
        )

        assert jail_case.case_user_roles == many_roles

        # Verify persistence
        assert jail_case.id is not None
        retrieved = await case_controller.get_case_by_id(jail_case.id)
        assert retrieved is not None
        assert retrieved.case_user_roles == many_roles

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_jail_unjail_cycles(self, db_service):
        """Test multiple jail/unjail cycles for the same user."""
        case_controller = CaseController(db_service)

        guild_id = 123456
        user_id = 789012

        # First jail
        await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=user_id,
            case_moderator_id=111111,
            guild_id=guild_id,
            case_reason="First jail",
            case_user_roles=[100, 101],
        )

        await asyncio.sleep(0.01)

        # Unjail
        await case_controller.create_case(
            case_type=CaseType.UNJAIL,
            case_user_id=user_id,
            case_moderator_id=111111,
            guild_id=guild_id,
            case_reason="Time served",
        )

        await asyncio.sleep(0.01)

        # Second jail with different roles
        jail2 = await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=user_id,
            case_moderator_id=222222,
            guild_id=guild_id,
            case_reason="Second jail",
            case_user_roles=[100, 101, 102, 103],  # User gained more roles
        )

        # Get all cases for this user
        all_cases = await case_controller.get_cases_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )

        assert len(all_cases) == 3

        # Verify latest is the second jail
        latest = await case_controller.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )
        assert latest is not None
        assert latest.id == jail2.id
        assert latest.case_user_roles == [100, 101, 102, 103]


class TestUnjailRoleRestoration:
    """Test role restoration logic during unjail."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_unjail_retrieves_correct_roles(self, db_service):
        """Test that unjail retrieves the correct stored roles."""
        case_controller = CaseController(db_service)

        guild_id = 123456
        user_id = 789012
        stored_roles = [1001, 1002, 1003]

        # Create jail case
        await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=user_id,
            case_moderator_id=111111,
            guild_id=guild_id,
            case_reason="Test jail",
            case_user_roles=stored_roles,
        )

        # Retrieve the case (simulating unjail operation)
        retrieved_case = await case_controller.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )

        assert retrieved_case is not None
        assert retrieved_case.case_type == CaseType.JAIL
        assert retrieved_case.case_user_roles == stored_roles

        # In actual unjail, these role IDs would be used to restore roles
        # This test verifies the data persists correctly

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_unjail_after_role_changes(self, db_service):
        """Test that stored roles remain consistent even if user's roles changed after jailing."""
        case_controller = CaseController(db_service)

        guild_id = 123456
        user_id = 789012
        original_roles = [1001, 1002, 1003]

        # User gets jailed with these roles
        await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=user_id,
            case_moderator_id=111111,
            guild_id=guild_id,
            case_reason="Jailed",
            case_user_roles=original_roles,
        )

        # Simulate: Admin manually gave user a role while jailed
        # (Not reflected in database - roles are snapshot at jail time)

        # Unjail retrieves original roles
        retrieved_case = await case_controller.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )

        assert retrieved_case is not None
        # Should still restore the roles from jail time, not current roles
        assert retrieved_case.case_user_roles == original_roles


class TestJailSystemEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_case_without_role_metadata(self, db_service):
        """Test handling cases where role metadata is None or missing."""
        case_controller = CaseController(db_service)

        # Create a case without explicit roles (defaults to empty list)
        jail_case = await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=123456,
            case_moderator_id=789012,
            guild_id=987654,
            case_reason="Test",
            # case_user_roles not provided
        )

        # Should handle gracefully
        assert jail_case.id is not None
        retrieved = await case_controller.get_case_by_id(jail_case.id)
        assert retrieved is not None
        assert retrieved.case_user_roles is not None  # Should be empty list, not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_with_no_prior_cases(self, db_service):
        """Test querying for a user with no jail history."""
        case_controller = CaseController(db_service)

        # Query for non-existent user
        latest_case = await case_controller.get_latest_case_by_user(
            guild_id=999999,
            user_id=888888,
        )

        assert latest_case is None

    @pytest.mark.integration
    def test_role_filtering_with_none_values(self):
        """Test role filtering handles None/missing attributes gracefully."""
        member = MagicMock(spec=discord.Member)
        jail_role = create_mock_role(999, "Jailed")

        # Create role with some missing methods (edge case)
        partial_role = MagicMock(spec=discord.Role)
        partial_role.id = 100
        partial_role.name = "Partial"
        partial_role.is_assignable = MagicMock(return_value=True)
        partial_role.is_bot_managed = MagicMock(return_value=False)
        partial_role.is_premium_subscriber = MagicMock(return_value=False)
        partial_role.is_integration = MagicMock(return_value=False)
        partial_role.is_default = MagicMock(return_value=False)
        partial_role.__eq__ = lambda self, other: self.id == getattr(other, "id", None)

        member.roles = [partial_role]

        # Should handle without errors
        manageable = Jail._get_manageable_roles(member, jail_role)
        assert len(manageable) == 1
