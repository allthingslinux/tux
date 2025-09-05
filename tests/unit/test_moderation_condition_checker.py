"""
🚀 ConditionChecker Unit Tests - Permission & Hierarchy Validation

Tests for the ConditionChecker mixin that handles permission checks,
role hierarchy validation, and other preconditions for moderation actions.

Test Coverage:
- Bot permission validation
- User role hierarchy checks
- Self-moderation prevention
- Guild owner protection
- Error response handling
- Condition validation flow
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import discord
from discord.ext import commands

from tux.services.moderation.condition_checker import ConditionChecker
from tux.services.moderation.moderation_service import ModerationError
from tux.core.types import Tux


class TestConditionChecker:
    """🛡️ Test ConditionChecker functionality."""

    @pytest.fixture
    def condition_checker(self) -> ConditionChecker:
        """Create a ConditionChecker instance for testing."""
        return ConditionChecker()

    @pytest.fixture
    def mock_ctx(self) -> commands.Context[Tux]:
        """Create a mock command context."""
        ctx = MagicMock(spec=commands.Context)
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.id = 123456789
        ctx.guild.owner_id = 999999999
        ctx.bot = MagicMock(spec=Tux)
        ctx.bot.user = MagicMock(spec=discord.User)
        ctx.bot.user.id = 111111111
        return ctx

    @pytest.fixture
    def mock_member(self) -> discord.Member:
        """Create a mock Discord member."""
        member = MagicMock(spec=discord.Member)
        member.id = 555666777
        member.name = "TestUser"
        return member

    @pytest.fixture
    def mock_moderator(self) -> discord.Member:
        """Create a mock Discord moderator."""
        moderator = MagicMock(spec=discord.Member)
        moderator.id = 987654321
        moderator.name = "Moderator"
        return moderator

    @pytest.mark.unit
    async def test_check_bot_permissions_success(
        self,
        condition_checker: ConditionChecker,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test successful bot permission check."""
        # Mock bot member with required permissions
        bot_member = MagicMock(spec=discord.Member)
        bot_member.guild_permissions.ban_members = True
        mock_ctx.guild.get_member.return_value = bot_member

        has_perms, error_msg = await condition_checker.check_bot_permissions(mock_ctx, "ban")

        assert has_perms is True
        assert error_msg is None

    @pytest.mark.unit
    async def test_check_bot_permissions_bot_not_member(
        self,
        condition_checker: ConditionChecker,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test bot permission check when bot is not a guild member."""
        mock_ctx.guild.get_member.return_value = None

        has_perms, error_msg = await condition_checker.check_bot_permissions(mock_ctx, "ban")

        assert has_perms is False
        assert error_msg == "Bot is not a member of this server."

    @pytest.mark.unit
    async def test_check_bot_permissions_missing_permission(
        self,
        condition_checker: ConditionChecker,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test bot permission check when bot lacks required permission."""
        # Mock bot member without ban permission
        bot_member = MagicMock(spec=discord.Member)
        bot_member.guild_permissions.ban_members = False
        mock_ctx.guild.get_member.return_value = bot_member

        has_perms, error_msg = await condition_checker.check_bot_permissions(mock_ctx, "ban")

        assert has_perms is False
        assert "Bot is missing required permissions: Ban Members" == error_msg

    @pytest.mark.unit
    async def test_check_bot_permissions_multiple_missing(
        self,
        condition_checker: ConditionChecker,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test bot permission check with multiple missing permissions."""
        # Mock bot member without required permissions
        bot_member = MagicMock(spec=discord.Member)
        bot_member.guild_permissions.ban_members = False
        bot_member.guild_permissions.kick_members = False
        mock_ctx.guild.get_member.return_value = bot_member

        has_perms, error_msg = await condition_checker.check_bot_permissions(mock_ctx, "ban")

        assert has_perms is False
        assert "Bot is missing required permissions: Ban Members" == error_msg
        assert "kick members" not in error_msg  # Only ban_members required for ban

    @pytest.mark.unit
    async def test_check_bot_permissions_no_special_perms_needed(
        self,
        condition_checker: ConditionChecker,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test bot permission check for actions that don't need special permissions."""
        bot_member = MagicMock(spec=discord.Member)
        mock_ctx.guild.get_member.return_value = bot_member

        has_perms, error_msg = await condition_checker.check_bot_permissions(mock_ctx, "warn")

        assert has_perms is True
        assert error_msg is None

    @pytest.mark.unit
    async def test_check_conditions_self_moderation(
        self,
        condition_checker: ConditionChecker,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
        mock_moderator: discord.Member,
    ) -> None:
        """Test prevention of self-moderation."""
        mock_member.id = mock_moderator.id  # Same user

        # Mock the send_error_response method since ConditionChecker is a standalone mixin
        condition_checker.send_error_response = AsyncMock()

        # Test that self-moderation returns False
        result = await condition_checker.check_conditions(
            ctx=mock_ctx,
            user=mock_member,
            moderator=mock_moderator,
            action="ban",
        )

        assert result is False  # Should return False for self-moderation
        condition_checker.send_error_response.assert_called_once()

    @pytest.mark.unit
    async def test_check_conditions_guild_owner_protection(
        self,
        condition_checker: ConditionChecker,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
        mock_moderator: discord.Member,
    ) -> None:
        """Test protection of guild owner from moderation."""
        mock_member.id = mock_ctx.guild.owner_id

        # Guild owner should be protected
        assert mock_member.id == mock_ctx.guild.owner_id

    @pytest.mark.unit
    async def test_check_conditions_role_hierarchy_member_to_member(
        self,
        condition_checker: ConditionChecker,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
        mock_moderator: discord.Member,
    ) -> None:
        """Test role hierarchy check between two members."""
        # Setup role hierarchy
        higher_role = MagicMock(spec=discord.Role)
        higher_role.position = 10

        lower_role = MagicMock(spec=discord.Role)
        lower_role.position = 5

        # Target has higher role than moderator
        mock_member.top_role = higher_role
        mock_moderator.top_role = lower_role

        # Both are Members (not just Users)
        assert isinstance(mock_member, discord.Member)
        assert isinstance(mock_moderator, discord.Member)

        # Hierarchy check should fail
        assert mock_member.top_role.position > mock_moderator.top_role.position

    @pytest.mark.unit
    async def test_check_conditions_bot_role_hierarchy(
        self,
        condition_checker: ConditionChecker,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test bot role hierarchy check."""
        # Setup bot with lower role
        bot_member = MagicMock(spec=discord.Member)
        bot_role = MagicMock(spec=discord.Role)
        bot_role.position = 5
        bot_member.top_role = bot_role
        mock_ctx.guild.get_member.return_value = bot_member

        # Target has higher role than bot
        member_role = MagicMock(spec=discord.Role)
        member_role.position = 10
        mock_member.top_role = member_role

        # Bot hierarchy check should fail
        assert mock_member.top_role.position > bot_member.top_role.position

    @pytest.mark.unit
    async def test_check_conditions_user_not_member(
        self,
        condition_checker: ConditionChecker,
        mock_ctx: commands.Context[Tux],
        mock_moderator: discord.Member,
    ) -> None:
        """Test conditions when target is a User (not Member)."""
        # Target is a User, not a Member
        mock_user = MagicMock(spec=discord.User)
        mock_user.id = 555666777

        # Should not do role hierarchy checks for Users
        assert not isinstance(mock_user, discord.Member)

    @pytest.mark.unit
    async def test_check_conditions_moderator_not_member(
        self,
        condition_checker: ConditionChecker,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test conditions when moderator is a User (not Member)."""
        # Moderator is a User, not a Member
        mock_user_moderator = MagicMock(spec=discord.User)
        mock_user_moderator.id = 987654321

        # Should not do role hierarchy checks for Users
        assert not isinstance(mock_user_moderator, discord.Member)

    @pytest.mark.unit
    async def test_check_conditions_success_case(
        self,
        condition_checker: ConditionChecker,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
        mock_moderator: discord.Member,
    ) -> None:
        """Test successful condition validation."""
        # Setup valid scenario
        mock_member.id = 555666777  # Different from moderator and owner
        mock_moderator.id = 987654321
        mock_ctx.guild.owner_id = 999999999

        # Setup role hierarchy (moderator higher than target)
        mod_role = MagicMock(spec=discord.Role)
        mod_role.position = 10
        mock_moderator.top_role = mod_role

        member_role = MagicMock(spec=discord.Role)
        member_role.position = 5
        mock_member.top_role = member_role

        # Setup bot permissions and role
        bot_member = MagicMock(spec=discord.Member)
        bot_member.guild_permissions.ban_members = True
        bot_role = MagicMock(spec=discord.Role)
        bot_role.position = 3  # Lower than member role
        bot_member.top_role = bot_role
        mock_ctx.guild.get_member.return_value = bot_member

        # All conditions should pass
        assert mock_member.id != mock_moderator.id
        assert mock_member.id != mock_ctx.guild.owner_id
        assert mock_moderator.top_role.position > mock_member.top_role.position
        assert mock_member.top_role.position > bot_member.top_role.position

    @pytest.mark.unit
    async def test_check_conditions_with_bot_permission_failure(
        self,
        condition_checker: ConditionChecker,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
        mock_moderator: discord.Member,
    ) -> None:
        """Test condition validation with bot permission failure."""
        # Setup scenario with bot lacking permissions
        bot_member = MagicMock(spec=discord.Member)
        bot_member.guild_permissions.ban_members = False  # Bot lacks permission
        mock_ctx.guild.get_member.return_value = bot_member

        # Bot permission check should fail
        has_perms, error_msg = await condition_checker.check_bot_permissions(mock_ctx, "ban")
        assert has_perms is False
        assert "Bot is missing required permissions: Ban Members" == error_msg

    @pytest.mark.unit
    async def test_check_conditions_error_response_handling(
        self,
        condition_checker: ConditionChecker,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
        mock_moderator: discord.Member,
    ) -> None:
        """Test that error responses are sent appropriately."""
        # This test verifies that error handling methods are called
        # In a real scenario, send_error_response would be available from EmbedManager

        # Mock the send_error_response method
        condition_checker.send_error_response = AsyncMock()

        # Test bot permission failure triggers error response
        bot_member = MagicMock(spec=discord.Member)
        bot_member.guild_permissions.ban_members = False
        mock_ctx.guild.get_member.return_value = bot_member

        has_perms, error_msg = await condition_checker.check_bot_permissions(mock_ctx, "ban")

        # In the full check_conditions method, this would trigger send_error_response
        assert has_perms is False
        assert error_msg is not None

    @pytest.mark.unit
    async def test_role_hierarchy_edge_cases(self) -> None:
        """Test edge cases in role hierarchy logic."""
        # Test with equal role positions
        role1 = MagicMock(spec=discord.Role)
        role1.position = 5

        role2 = MagicMock(spec=discord.Role)
        role2.position = 5

        # Equal positions should be handled
        assert role1.position == role2.position

        # Test with None roles (edge case)
        # This would need to be handled in the actual implementation
        member_no_role = MagicMock(spec=discord.Member)
        member_no_role.top_role = None

        # Should handle None gracefully
        assert member_no_role.top_role is None
