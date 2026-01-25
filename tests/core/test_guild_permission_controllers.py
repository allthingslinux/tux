"""Guild permission controllers integration tests.

Covers PermissionRankController, PermissionAssignmentController, and
PermissionCommandController with database-backed permission rank CRUD,
role-to-rank assignments, and command permission requirements.
"""

import pytest

from tux.core.permission_system import RESTRICTED_COMMANDS, PermissionSystem
from tux.database.controllers import (
    GuildController,
    PermissionAssignmentController,
    PermissionCommandController,
    PermissionRankController,
)

TEST_GUILD_ID = 123456789012345678
TEST_ROLE_ID_1 = 987654321098765432
TEST_ROLE_ID_2 = 987654321098765433
TEST_USER_ID = 876543210987654321


class TestPermissionRankController:
    """PermissionRankController permission rank CRUD."""

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_create_permission_rank_persists_rank_with_name_and_description(
        self,
        guild_controller: GuildController,
        permission_rank_controller: PermissionRankController,
    ) -> None:
        """Creating a permission rank persists guild_id, rank, name, and description."""
        # Arrange
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)

        # Act
        rank = await permission_rank_controller.create_permission_rank(
            guild_id=TEST_GUILD_ID,
            rank=3,
            name="Moderator",
            description="Server moderator",
        )

        # Assert
        assert rank.guild_id == TEST_GUILD_ID
        assert rank.rank == 3
        assert rank.name == "Moderator"
        assert rank.description == "Server moderator"

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_get_permission_ranks_by_guild_returns_all_ranks_ordered_by_rank(
        self,
        guild_controller: GuildController,
        permission_rank_controller: PermissionRankController,
    ) -> None:
        """Retrieving ranks by guild returns all ranks ordered by rank."""
        # Arrange
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
        await permission_rank_controller.create_permission_rank(
            guild_id=TEST_GUILD_ID,
            rank=1,
            name="Member",
        )
        await permission_rank_controller.create_permission_rank(
            guild_id=TEST_GUILD_ID,
            rank=3,
            name="Moderator",
        )
        await permission_rank_controller.create_permission_rank(
            guild_id=TEST_GUILD_ID,
            rank=5,
            name="Admin",
        )

        # Act
        ranks = await permission_rank_controller.get_permission_ranks_by_guild(
            TEST_GUILD_ID,
        )

        # Assert
        assert len(ranks) == 3
        assert ranks[0].rank == 1
        assert ranks[1].rank == 3
        assert ranks[2].rank == 5

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_get_permission_rank_returns_rank_when_exists(
        self,
        guild_controller: GuildController,
        permission_rank_controller: PermissionRankController,
    ) -> None:
        """Retrieving an existing rank by guild and rank number returns it."""
        # Arrange
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
        await permission_rank_controller.create_permission_rank(
            guild_id=TEST_GUILD_ID,
            rank=3,
            name="Moderator",
        )

        # Act
        rank = await permission_rank_controller.get_permission_rank(TEST_GUILD_ID, 3)

        # Assert
        assert rank is not None
        assert rank.rank == 3
        assert rank.name == "Moderator"

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_get_permission_rank_returns_none_when_not_found(
        self,
        guild_controller: GuildController,
        permission_rank_controller: PermissionRankController,
    ) -> None:
        """Retrieving a non-existent rank returns None."""
        # Arrange
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)

        # Act
        rank = await permission_rank_controller.get_permission_rank(TEST_GUILD_ID, 99)

        # Assert
        assert rank is None

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_update_permission_rank_updates_name_and_description(
        self,
        guild_controller: GuildController,
        permission_rank_controller: PermissionRankController,
    ) -> None:
        """Updating a rank persists new name and description."""
        # Arrange
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
        await permission_rank_controller.create_permission_rank(
            guild_id=TEST_GUILD_ID,
            rank=3,
            name="Moderator",
            description="Basic moderator",
        )

        # Act
        updated = await permission_rank_controller.update_permission_rank(
            guild_id=TEST_GUILD_ID,
            rank=3,
            name="Senior Moderator",
            description="Experienced moderator",
        )

        # Assert
        assert updated is not None
        assert updated.name == "Senior Moderator"
        assert updated.description == "Experienced moderator"

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_delete_permission_rank_removes_rank_from_database(
        self,
        guild_controller: GuildController,
        permission_rank_controller: PermissionRankController,
    ) -> None:
        """Deleting a rank removes it; subsequent get returns None."""
        # Arrange
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
        await permission_rank_controller.create_permission_rank(
            guild_id=TEST_GUILD_ID,
            rank=3,
            name="Moderator",
        )

        # Act
        result = await permission_rank_controller.delete_permission_rank(
            TEST_GUILD_ID,
            3,
        )

        # Assert
        assert result is True
        rank = await permission_rank_controller.get_permission_rank(TEST_GUILD_ID, 3)
        assert rank is None


class TestPermissionAssignmentController:
    """PermissionAssignmentController role-to-rank assignments."""

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_assign_permission_rank_persists_role_to_rank_mapping(
        self,
        guild_controller: GuildController,
        permission_rank_controller: PermissionRankController,
        permission_assignment_controller: PermissionAssignmentController,
    ) -> None:
        """Assigning a rank to a role persists guild_id, role_id, and permission_rank_id."""
        # Arrange
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
        rank = await permission_rank_controller.create_permission_rank(
            guild_id=TEST_GUILD_ID,
            rank=3,
            name="Moderator",
        )
        assert rank.id is not None

        # Act
        assignment = await permission_assignment_controller.assign_permission_rank(
            guild_id=TEST_GUILD_ID,
            role_id=TEST_ROLE_ID_1,
            permission_rank_id=rank.id,
        )

        # Assert
        assert assignment.guild_id == TEST_GUILD_ID
        assert assignment.role_id == TEST_ROLE_ID_1
        assert assignment.permission_rank_id == rank.id

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_get_assignments_by_guild_returns_all_role_assignments(
        self,
        guild_controller: GuildController,
        permission_rank_controller: PermissionRankController,
        permission_assignment_controller: PermissionAssignmentController,
    ) -> None:
        """Retrieving assignments by guild returns all role-to-rank mappings."""
        # Arrange
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
        rank1 = await permission_rank_controller.create_permission_rank(
            guild_id=TEST_GUILD_ID,
            rank=1,
            name="Member",
        )
        assert rank1.id is not None
        rank2 = await permission_rank_controller.create_permission_rank(
            guild_id=TEST_GUILD_ID,
            rank=3,
            name="Moderator",
        )
        assert rank2.id is not None
        await permission_assignment_controller.assign_permission_rank(
            guild_id=TEST_GUILD_ID,
            role_id=TEST_ROLE_ID_1,
            permission_rank_id=rank1.id,
        )
        await permission_assignment_controller.assign_permission_rank(
            guild_id=TEST_GUILD_ID,
            role_id=TEST_ROLE_ID_2,
            permission_rank_id=rank2.id,
        )

        # Act
        assignments = await permission_assignment_controller.get_assignments_by_guild(
            TEST_GUILD_ID,
        )

        # Assert
        assert len(assignments) == 2
        role_ids = {a.role_id for a in assignments}
        assert role_ids == {TEST_ROLE_ID_1, TEST_ROLE_ID_2}

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_get_user_permission_rank_returns_highest_rank_among_user_roles(
        self,
        guild_controller: GuildController,
        permission_rank_controller: PermissionRankController,
        permission_assignment_controller: PermissionAssignmentController,
    ) -> None:
        """User with multiple role assignments receives highest rank among them."""
        # Arrange
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
        rank1 = await permission_rank_controller.create_permission_rank(
            guild_id=TEST_GUILD_ID,
            rank=1,
            name="Member",
        )
        assert rank1.id is not None
        rank2 = await permission_rank_controller.create_permission_rank(
            guild_id=TEST_GUILD_ID,
            rank=3,
            name="Moderator",
        )
        assert rank2.id is not None
        await permission_assignment_controller.assign_permission_rank(
            guild_id=TEST_GUILD_ID,
            role_id=TEST_ROLE_ID_1,
            permission_rank_id=rank1.id,
        )
        await permission_assignment_controller.assign_permission_rank(
            guild_id=TEST_GUILD_ID,
            role_id=TEST_ROLE_ID_2,
            permission_rank_id=rank2.id,
        )

        # Act
        user_rank = await permission_assignment_controller.get_user_permission_rank(
            guild_id=TEST_GUILD_ID,
            user_id=TEST_USER_ID,
            user_roles=[TEST_ROLE_ID_1, TEST_ROLE_ID_2],
        )

        # Assert
        assert user_rank == 3

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_remove_role_assignment_removes_role_from_assignments(
        self,
        guild_controller: GuildController,
        permission_rank_controller: PermissionRankController,
        permission_assignment_controller: PermissionAssignmentController,
    ) -> None:
        """Removing a role assignment drops it; get_assignments_by_guild excludes it."""
        # Arrange
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
        rank = await permission_rank_controller.create_permission_rank(
            guild_id=TEST_GUILD_ID,
            rank=3,
            name="Moderator",
        )
        assert rank.id is not None
        await permission_assignment_controller.assign_permission_rank(
            guild_id=TEST_GUILD_ID,
            role_id=TEST_ROLE_ID_1,
            permission_rank_id=rank.id,
        )

        # Act
        result = await permission_assignment_controller.remove_role_assignment(
            guild_id=TEST_GUILD_ID,
            role_id=TEST_ROLE_ID_1,
        )

        # Assert
        assert result is True
        assignments = await permission_assignment_controller.get_assignments_by_guild(
            TEST_GUILD_ID,
        )
        role_ids = [a.role_id for a in assignments]
        assert TEST_ROLE_ID_1 not in role_ids


class TestPermissionCommandController:
    """PermissionCommandController command permission requirements."""

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_set_command_permission_persists_guild_command_and_required_rank(
        self,
        guild_controller: GuildController,
        permission_command_controller: PermissionCommandController,
    ) -> None:
        """Setting a command permission persists guild_id, command_name, and required_rank."""
        # Arrange
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)

        # Act
        cmd_perm = await permission_command_controller.set_command_permission(
            guild_id=TEST_GUILD_ID,
            command_name="ban",
            required_rank=3,
        )

        # Assert
        assert cmd_perm.guild_id == TEST_GUILD_ID
        assert cmd_perm.command_name == "ban"
        assert cmd_perm.required_rank == 3

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_get_command_permission_returns_permission_when_configured(
        self,
        guild_controller: GuildController,
        permission_command_controller: PermissionCommandController,
    ) -> None:
        """Retrieving a configured command permission returns it."""
        # Arrange
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
        await permission_command_controller.set_command_permission(
            guild_id=TEST_GUILD_ID,
            command_name="ban",
            required_rank=3,
        )

        # Act
        cmd_perm = await permission_command_controller.get_command_permission(
            guild_id=TEST_GUILD_ID,
            command_name="ban",
        )

        # Assert
        assert cmd_perm is not None
        assert cmd_perm.command_name == "ban"
        assert cmd_perm.required_rank == 3

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    async def test_get_all_command_permissions_returns_all_configured_commands(
        self,
        guild_controller: GuildController,
        permission_command_controller: PermissionCommandController,
    ) -> None:
        """Retrieving all command permissions returns every configured command for the guild."""
        # Arrange
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
        await permission_command_controller.set_command_permission(
            guild_id=TEST_GUILD_ID,
            command_name="ban",
            required_rank=3,
        )
        await permission_command_controller.set_command_permission(
            guild_id=TEST_GUILD_ID,
            command_name="kick",
            required_rank=2,
        )

        # Act
        permissions = await permission_command_controller.get_all_command_permissions(
            TEST_GUILD_ID,
        )

        # Assert
        assert len(permissions) == 2
        names = {p.command_name for p in permissions}
        assert names == {"ban", "kick"}

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    @pytest.mark.parametrize("command_name", list(RESTRICTED_COMMANDS))
    async def test_set_command_permission_raises_for_restricted_commands(
        self,
        guild_controller: GuildController,
        permission_system: PermissionSystem,
        command_name: str,
    ) -> None:
        """Restricted commands (eval, e, jsk, jishaku) cannot be assigned to permission ranks."""
        # Arrange
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)

        # Act & Assert
        with pytest.raises(ValueError, match="restricted"):
            await permission_system.set_command_permission(
                guild_id=TEST_GUILD_ID,
                command_name=command_name,
                required_rank=3,
            )

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "command_name",
        ["EVAL", "Eval", "JSK", "Jsk", "Jishaku", "JISHAKU"],
    )
    async def test_set_command_permission_blocks_restricted_case_insensitive(
        self,
        guild_controller: GuildController,
        permission_system: PermissionSystem,
        command_name: str,
    ) -> None:
        """Restricted command checks are case-insensitive."""
        # Arrange
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)

        # Act & Assert
        with pytest.raises(ValueError, match="restricted"):
            await permission_system.set_command_permission(
                guild_id=TEST_GUILD_ID,
                command_name=command_name,
                required_rank=3,
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
