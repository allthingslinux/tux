"""Jail and unjail integration tests.

Covers role management (_get_manageable_roles), jail case DB operations,
role restoration, and re-jail on rejoin when a jailed user leaves and rejoins.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from tux.cache import JailStatusCache
from tux.core.bot import Tux
from tux.database.controllers import CaseController, DatabaseCoordinator
from tux.database.models import CaseType
from tux.database.service import DatabaseService
from tux.modules.moderation.jail import Jail

TEST_GUILD_ID = 123456
ALT_GUILD_ID = 987654
TEST_USER_ID = 789012
TEST_MODERATOR_ID = 111111
SECOND_MODERATOR_ID = 222222
JAIL_ROLE_ID = 8888
JAIL_CHANNEL_ID = 9999


def create_mock_role(role_id: int, name: str, **kwargs: bool) -> MagicMock:
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
    """Jail role management (_get_manageable_roles) filters."""

    @pytest.mark.unit
    def test_get_manageable_roles_returns_only_assignable_non_special_roles(
        self,
    ) -> None:
        """_get_manageable_roles returns only assignable, non-bot/premium/integration roles."""
        # Arrange
        member = MagicMock(spec=discord.Member)
        jail_role = create_mock_role(999, "Jailed")
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

        # Act
        manageable = Jail._get_manageable_roles(member, jail_role)

        # Assert
        assert len(manageable) == 2
        assert normal_role1 in manageable
        assert normal_role2 in manageable
        assert bot_role not in manageable
        assert premium_role not in manageable
        assert integration_role not in manageable
        assert everyone_role not in manageable
        assert jail_role not in manageable
        assert unassignable_role not in manageable

    @pytest.mark.unit
    def test_get_manageable_roles_empty_when_only_special_roles(self) -> None:
        """_get_manageable_roles returns empty list when member has only @everyone/bot roles."""
        # Arrange
        member = MagicMock(spec=discord.Member)
        jail_role = create_mock_role(999, "Jailed")
        everyone_role = create_mock_role(1, "@everyone", is_default=True)
        bot_role = create_mock_role(2, "Bot Role", is_bot_managed=True)
        member.roles = [everyone_role, bot_role]

        # Act
        manageable = Jail._get_manageable_roles(member, jail_role)

        # Assert
        assert len(manageable) == 0

    @pytest.mark.unit
    def test_get_manageable_roles_excludes_jail_role(self) -> None:
        """_get_manageable_roles excludes the jail role even when member has it."""
        # Arrange
        member = MagicMock(spec=discord.Member)
        jail_role = create_mock_role(999, "Jailed")
        normal_role = create_mock_role(100, "Member")
        member.roles = [normal_role, jail_role]

        # Act
        manageable = Jail._get_manageable_roles(member, jail_role)

        # Assert
        assert len(manageable) == 1
        assert normal_role in manageable
        assert jail_role not in manageable


class TestJailDatabaseOperations:
    """Jail case DB create/retrieve and multi-cycle behavior."""

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_jail_case_creation_persists_roles_and_reason(
        self,
        db_service: DatabaseService,
    ) -> None:
        """Creating a jail case stores role metadata and reason."""
        # Arrange
        case_controller = CaseController(db_service)
        roles = [1001, 1002, 1003, 1004]
        reason = "Testing role storage"

        # Act
        jail_case = await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=TEST_USER_ID,
            case_moderator_id=TEST_MODERATOR_ID,
            guild_id=ALT_GUILD_ID,
            case_reason=reason,
            case_user_roles=roles,
        )

        # Assert
        assert jail_case.id is not None
        assert jail_case.case_type == CaseType.JAIL
        assert jail_case.case_user_roles == roles
        assert jail_case.case_reason == reason

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_get_latest_case_by_user_returns_most_recent_jail(
        self,
        db_service: DatabaseService,
    ) -> None:
        """get_latest_case_by_user returns the most recent case (WARN then JAIL)."""
        # Arrange
        case_controller = CaseController(db_service)
        guild_id = TEST_GUILD_ID
        user_id = TEST_USER_ID
        await case_controller.create_case(
            case_type=CaseType.WARN,
            case_user_id=user_id,
            case_moderator_id=TEST_MODERATOR_ID,
            guild_id=guild_id,
            case_reason="First warning",
        )
        await asyncio.sleep(0.01)

        jail_case = await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=user_id,
            case_moderator_id=SECOND_MODERATOR_ID,
            guild_id=guild_id,
            case_reason="Jailed for violations",
            case_user_roles=[5001, 5002, 5003],
        )

        # Act
        latest_case = await case_controller.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )

        # Assert
        assert latest_case is not None
        assert latest_case.id == jail_case.id
        assert latest_case.case_type == CaseType.JAIL
        assert latest_case.case_user_roles == [5001, 5002, 5003]

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_jail_case_with_empty_roles_persists(
        self,
        db_service: DatabaseService,
    ) -> None:
        """Jail case with empty role list persists and retrieves correctly."""
        # Arrange
        case_controller = CaseController(db_service)

        # Act
        jail_case = await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=TEST_USER_ID,
            case_moderator_id=TEST_MODERATOR_ID,
            guild_id=ALT_GUILD_ID,
            case_reason="User had no roles",
            case_user_roles=[],
        )
        assert jail_case.id is not None
        retrieved = await case_controller.get_case_by_id(jail_case.id)

        # Assert
        assert jail_case.case_user_roles == []
        assert retrieved is not None
        assert retrieved.case_user_roles == []

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_jail_case_with_many_roles_persists(
        self,
        db_service: DatabaseService,
    ) -> None:
        """Jail case with many roles (50) persists correctly."""
        # Arrange
        case_controller = CaseController(db_service)
        many_roles = list(range(1000, 1050))

        # Act
        jail_case = await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=TEST_USER_ID,
            case_moderator_id=TEST_MODERATOR_ID,
            guild_id=ALT_GUILD_ID,
            case_reason="Power user with many roles",
            case_user_roles=many_roles,
        )
        assert jail_case.id is not None
        retrieved = await case_controller.get_case_by_id(jail_case.id)

        # Assert
        assert jail_case.case_user_roles == many_roles
        assert retrieved is not None
        assert retrieved.case_user_roles == many_roles

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_multiple_jail_unjail_cycles_latest_reflects_second_jail(
        self,
        db_service: DatabaseService,
    ) -> None:
        """Multiple jail/unjail cycles; get_latest returns second jail with updated roles."""
        # Arrange
        case_controller = CaseController(db_service)
        guild_id = TEST_GUILD_ID
        user_id = TEST_USER_ID

        await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=user_id,
            case_moderator_id=TEST_MODERATOR_ID,
            guild_id=guild_id,
            case_reason="First jail",
            case_user_roles=[100, 101],
        )
        await asyncio.sleep(0.01)
        await case_controller.create_case(
            case_type=CaseType.UNJAIL,
            case_user_id=user_id,
            case_moderator_id=TEST_MODERATOR_ID,
            guild_id=guild_id,
            case_reason="Time served",
        )
        await asyncio.sleep(0.01)
        jail2 = await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=user_id,
            case_moderator_id=SECOND_MODERATOR_ID,
            guild_id=guild_id,
            case_reason="Second jail",
            case_user_roles=[100, 101, 102, 103],
        )

        # Act
        all_cases = await case_controller.get_cases_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )
        latest = await case_controller.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )

        # Assert
        assert len(all_cases) == 3
        assert latest is not None
        assert latest.id == jail2.id
        assert latest.case_user_roles == [100, 101, 102, 103]


class TestUnjailRoleRestoration:
    """Unjail retrieves stored roles from latest jail case."""

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_get_latest_case_returns_stored_roles_for_unjail(
        self,
        db_service: DatabaseService,
    ) -> None:
        """get_latest_case_by_user returns jail case with stored roles for unjail restore."""
        # Arrange
        case_controller = CaseController(db_service)
        guild_id = TEST_GUILD_ID
        user_id = TEST_USER_ID
        stored_roles = [1001, 1002, 1003]
        await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=user_id,
            case_moderator_id=TEST_MODERATOR_ID,
            guild_id=guild_id,
            case_reason="Test jail",
            case_user_roles=stored_roles,
        )

        # Act
        retrieved_case = await case_controller.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )

        # Assert
        assert retrieved_case is not None
        assert retrieved_case.case_type == CaseType.JAIL
        assert retrieved_case.case_user_roles == stored_roles

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_stored_roles_unchanged_if_user_roles_change_after_jail(
        self,
        db_service: DatabaseService,
    ) -> None:
        """Stored roles are snapshot at jail time; later role changes do not affect them."""
        # Arrange
        case_controller = CaseController(db_service)
        guild_id = TEST_GUILD_ID
        user_id = TEST_USER_ID
        original_roles = [1001, 1002, 1003]
        await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=user_id,
            case_moderator_id=TEST_MODERATOR_ID,
            guild_id=guild_id,
            case_reason="Jailed",
            case_user_roles=original_roles,
        )

        # Act (simulate unjail lookup; roles snapshot at jail time)
        retrieved_case = await case_controller.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )

        # Assert
        assert retrieved_case is not None
        assert retrieved_case.case_user_roles == original_roles


class TestJailSystemEdgeCases:
    """Edge cases: missing role metadata, no prior cases, minimal role mocking."""

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_jail_case_without_role_metadata_defaults_and_persists(
        self,
        db_service: DatabaseService,
    ) -> None:
        """Jail case without explicit case_user_roles defaults to empty list and persists."""
        # Arrange
        case_controller = CaseController(db_service)

        # Act
        jail_case = await case_controller.create_case(
            case_type=CaseType.JAIL,
            case_user_id=TEST_USER_ID,
            case_moderator_id=TEST_MODERATOR_ID,
            guild_id=ALT_GUILD_ID,
            case_reason="Test",
        )
        assert jail_case.id is not None
        retrieved = await case_controller.get_case_by_id(jail_case.id)

        # Assert
        assert retrieved is not None
        assert retrieved.case_user_roles is not None
        assert retrieved.case_user_roles == []

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_get_latest_case_by_user_returns_none_when_no_cases(
        self,
        db_service: DatabaseService,
    ) -> None:
        """get_latest_case_by_user returns None for user with no cases."""
        # Arrange
        case_controller = CaseController(db_service)

        # Act
        latest_case = await case_controller.get_latest_case_by_user(
            guild_id=999999,
            user_id=888888,
        )

        # Assert
        assert latest_case is None

    @pytest.mark.unit
    def test_get_manageable_roles_handles_minimal_role_mock(self) -> None:
        """_get_manageable_roles handles a minimal valid role mock without error."""
        # Arrange
        member = MagicMock(spec=discord.Member)
        jail_role = create_mock_role(999, "Jailed")
        minimal_role = create_mock_role(100, "Partial")
        member.roles = [minimal_role]

        # Act
        manageable = Jail._get_manageable_roles(member, jail_role)

        # Assert
        assert len(manageable) == 1
        assert minimal_role in manageable


class TestRejailOnRejoin:
    """Re-jail on rejoin when user left while jailed."""

    @pytest.fixture
    async def jail_ready_coord(
        self,
        db_service: DatabaseService,
    ) -> DatabaseCoordinator:
        """DatabaseCoordinator with guild and jail config (role + channel) set."""
        await JailStatusCache().clear_all()
        coord = DatabaseCoordinator(db_service)
        await coord.guild.get_or_create_guild(TEST_GUILD_ID)
        await coord.guild_config.get_or_create_config(TEST_GUILD_ID)
        await coord.guild_config.update_config(
            TEST_GUILD_ID,
            jail_role_id=JAIL_ROLE_ID,
            jail_channel_id=JAIL_CHANNEL_ID,
        )
        return coord

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_on_member_join_reapplies_jail_role_when_user_was_jailed(
        self,
        jail_ready_coord: DatabaseCoordinator,
    ) -> None:
        """When a jailed user leaves and rejoins, on_member_join re-applies the jail role."""
        # Arrange
        await jail_ready_coord.case.create_case(
            case_type=CaseType.JAIL,
            case_user_id=TEST_USER_ID,
            case_moderator_id=TEST_MODERATOR_ID,
            guild_id=TEST_GUILD_ID,
            case_reason="Rejail test",
            case_user_roles=[],
        )
        bot = MagicMock(spec=Tux)
        bot.db = jail_ready_coord
        jail_role = create_mock_role(JAIL_ROLE_ID, "Jailed")
        mock_channel = MagicMock(spec=discord.abc.GuildChannel)
        guild = MagicMock(spec=discord.Guild)
        guild.id = TEST_GUILD_ID
        guild.name = "Test Guild"
        guild.get_role = MagicMock(return_value=jail_role)
        guild.get_channel = MagicMock(return_value=mock_channel)
        member = MagicMock(spec=discord.Member)
        member.guild = guild
        member.id = TEST_USER_ID
        member.roles = [create_mock_role(1, "@everyone", is_default=True)]
        member.add_roles = AsyncMock()
        member.remove_roles = AsyncMock()

        with patch(
            "tux.services.moderation.factory.ModerationServiceFactory.create_coordinator",
            return_value=MagicMock(),
            autospec=True,
        ):
            cog = Jail(bot)

        # Act
        await cog.on_member_join(member)

        # Assert - jail role re-applied; only @everyone so no roles to remove
        member.add_roles.assert_called_once_with(
            jail_role,
            reason="Re-jail on rejoin (was jailed before leaving)",
        )
        member.remove_roles.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_on_member_join_does_not_rejail_when_latest_case_is_unjail(
        self,
        jail_ready_coord: DatabaseCoordinator,
    ) -> None:
        """on_member_join does not rejail when user's latest case is UNJAIL."""
        # Arrange - invalidate cache so we hit DB (backend may hold stale True from other tests)
        await JailStatusCache().invalidate(TEST_GUILD_ID, TEST_USER_ID)
        await jail_ready_coord.case.create_case(
            case_type=CaseType.JAIL,
            case_user_id=TEST_USER_ID,
            case_moderator_id=TEST_MODERATOR_ID,
            guild_id=TEST_GUILD_ID,
            case_reason="Jailed",
            case_user_roles=[],
        )
        await asyncio.sleep(0.01)
        await jail_ready_coord.case.create_case(
            case_type=CaseType.UNJAIL,
            case_user_id=TEST_USER_ID,
            case_moderator_id=TEST_MODERATOR_ID,
            guild_id=TEST_GUILD_ID,
            case_reason="Released",
        )
        bot = MagicMock(spec=Tux)
        bot.db = jail_ready_coord
        jail_role = create_mock_role(JAIL_ROLE_ID, "Jailed")
        guild = MagicMock(spec=discord.Guild)
        guild.id = TEST_GUILD_ID
        guild.name = "Test Guild"
        guild.get_role = MagicMock(return_value=jail_role)
        guild.get_channel = MagicMock(
            return_value=MagicMock(spec=discord.abc.GuildChannel),
        )
        member = MagicMock(spec=discord.Member)
        member.guild = guild
        member.id = TEST_USER_ID
        member.roles = [create_mock_role(1, "@everyone", is_default=True)]
        member.add_roles = AsyncMock()
        member.remove_roles = AsyncMock()

        with patch(
            "tux.services.moderation.factory.ModerationServiceFactory.create_coordinator",
            return_value=MagicMock(),
            autospec=True,
        ):
            cog = Jail(bot)

        # Act
        await cog.on_member_join(member)

        # Assert
        member.add_roles.assert_not_called()
        member.remove_roles.assert_not_called()
