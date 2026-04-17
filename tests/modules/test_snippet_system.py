"""Snippet system integration tests.

Tests real-world snippet workflows: creation, permission checks,
alias resolution, editing, deletion, and snippet-ban enforcement.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from discord.ext import commands

from tux.core.bot import Tux
from tux.database.controllers import DatabaseCoordinator
from tux.database.models import CaseType, Guild
from tux.database.service import DatabaseService
from tux.modules.snippets import SnippetsBaseCog
from tux.modules.snippets.create_snippet import CreateSnippet

pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.database]

TEST_GUILD_ID = 100000
TEST_USER_ID = 200000
TEST_MOD_ID = 300000


@pytest.fixture
def mock_bot() -> Tux:
    """Return a mock Tux bot with emoji_manager stubbed."""
    bot = MagicMock(spec=Tux)
    bot.emoji_manager = MagicMock()
    bot.emoji_manager.get = lambda x: f":{x}:"
    return bot


@pytest.fixture
def mock_ctx(mock_bot: Tux) -> commands.Context[Tux]:
    """Return a mock command context in a guild with a test user."""
    ctx = MagicMock(spec=commands.Context)
    ctx.bot = mock_bot
    ctx.guild = MagicMock(spec=discord.Guild)
    ctx.guild.id = TEST_GUILD_ID
    ctx.guild.name = "Test Guild"
    ctx.guild.icon = MagicMock()
    ctx.guild.icon.url = "https://example.com/icon.png"
    ctx.author = MagicMock(spec=discord.Member)
    ctx.author.id = TEST_USER_ID
    ctx.author.name = "testuser"
    ctx.author.display_avatar = MagicMock()
    ctx.author.display_avatar.url = "https://example.com/avatar.png"
    ctx.author.roles = []
    ctx.message = MagicMock()
    ctx.message.created_at = MagicMock()
    ctx.send = AsyncMock()
    return ctx


class TestSnippetPermissionChecks:
    """Test that snippet permission logic enforces real-world access rules."""

    @pytest.fixture
    async def cog(self, mock_bot: Tux, db_service: DatabaseService) -> SnippetsBaseCog:
        """Build a snippets cog wired to the test database."""
        cog = SnippetsBaseCog(mock_bot)
        coordinator = DatabaseCoordinator(db_service)
        mock_bot.db = coordinator
        return cog

    @pytest.fixture
    async def seed_guild(self, db_service: DatabaseService) -> None:
        """Insert a minimal guild row for FK-backed operations."""
        async with db_service.session() as session:
            session.add(Guild(id=TEST_GUILD_ID, case_count=0))
            await session.commit()

    @pytest.mark.usefixtures("seed_guild")
    async def test_snippet_banned_user_cannot_create(
        self,
        cog: SnippetsBaseCog,
        mock_ctx: commands.Context[Tux],
        db_service: DatabaseService,
    ) -> None:
        """A user who has been snippet-banned should be denied snippet operations."""
        # Arrange — create a SNIPPETBAN case for the user
        await cog.db.case.create_case(
            guild_id=TEST_GUILD_ID,
            case_user_id=TEST_USER_ID,
            case_moderator_id=TEST_MOD_ID,
            case_type=CaseType.SNIPPETBAN,
            case_reason="Spam snippets",
        )

        # Act
        with patch.object(
            cog,
            "check_if_user_has_mod_override",
            new_callable=AsyncMock,
            return_value=False,
        ):
            allowed, reason = await cog.snippet_check(mock_ctx)

        # Assert
        assert allowed is False
        assert "banned" in reason.lower()

    @pytest.mark.usefixtures("seed_guild")
    async def test_snippet_unbanned_user_can_create(
        self,
        cog: SnippetsBaseCog,
        mock_ctx: commands.Context[Tux],
        db_service: DatabaseService,
    ) -> None:
        """A user who was banned then unbanned should be allowed again."""
        # Arrange — ban then unban
        await cog.db.case.create_case(
            guild_id=TEST_GUILD_ID,
            case_user_id=TEST_USER_ID,
            case_moderator_id=TEST_MOD_ID,
            case_type=CaseType.SNIPPETBAN,
            case_reason="Spam",
        )
        await cog.db.case.create_case(
            guild_id=TEST_GUILD_ID,
            case_user_id=TEST_USER_ID,
            case_moderator_id=TEST_MOD_ID,
            case_type=CaseType.SNIPPETUNBAN,
            case_reason="Appealed",
        )

        # Act
        with patch.object(
            cog,
            "check_if_user_has_mod_override",
            new_callable=AsyncMock,
            return_value=False,
        ):
            allowed, _reason = await cog.snippet_check(mock_ctx)

        # Assert
        assert allowed is True

    async def test_non_owner_cannot_edit_others_snippet(
        self,
        cog: SnippetsBaseCog,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """A regular user should not be able to edit someone else's snippet."""
        other_user_id = 999999

        with (
            patch.object(
                cog,
                "check_if_user_has_mod_override",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch.object(
                cog,
                "is_snippetbanned",
                new_callable=AsyncMock,
                return_value=False,
            ),
        ):
            allowed, reason = await cog.snippet_check(
                mock_ctx,
                snippet_locked=False,
                snippet_user_id=other_user_id,
            )

        assert allowed is False
        assert "own snippets" in reason.lower()

    async def test_mod_can_edit_others_snippet(
        self,
        cog: SnippetsBaseCog,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """A moderator should be able to edit any snippet via mod override."""
        other_user_id = 999999

        with patch.object(
            cog,
            "check_if_user_has_mod_override",
            new_callable=AsyncMock,
            return_value=True,
        ):
            allowed, reason = await cog.snippet_check(
                mock_ctx,
                snippet_locked=False,
                snippet_user_id=other_user_id,
            )

        assert allowed is True
        assert "mod override" in reason.lower()

    async def test_locked_snippet_cannot_be_edited(
        self,
        cog: SnippetsBaseCog,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """A locked snippet should not be editable by its owner."""
        with (
            patch.object(
                cog,
                "check_if_user_has_mod_override",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch.object(
                cog,
                "is_snippetbanned",
                new_callable=AsyncMock,
                return_value=False,
            ),
        ):
            allowed, reason = await cog.snippet_check(
                mock_ctx,
                snippet_locked=True,
                snippet_user_id=TEST_USER_ID,
            )

        assert allowed is False
        assert "locked" in reason.lower()

    async def test_mod_can_edit_locked_snippet(
        self,
        cog: SnippetsBaseCog,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """A moderator should bypass the lock."""
        with patch.object(
            cog,
            "check_if_user_has_mod_override",
            new_callable=AsyncMock,
            return_value=True,
        ):
            allowed, _reason = await cog.snippet_check(
                mock_ctx,
                snippet_locked=True,
                snippet_user_id=999999,
            )

        assert allowed is True


class TestSnippetCreation:
    """Test snippet creation workflows against a real database."""

    @pytest.fixture
    async def cog(self, mock_bot: Tux, db_service: DatabaseService) -> CreateSnippet:
        """Build a create-snippet cog wired to the test database."""
        cog = CreateSnippet(mock_bot)
        coordinator = DatabaseCoordinator(db_service)
        mock_bot.db = coordinator
        cog.create_snippet.cog = cog
        return cog

    @pytest.fixture
    async def seed_guild(self, db_service: DatabaseService) -> None:
        """Insert a minimal guild row for FK-backed operations."""
        async with db_service.session() as session:
            session.add(Guild(id=TEST_GUILD_ID, case_count=0))
            await session.commit()

    @pytest.mark.usefixtures("seed_guild")
    async def test_create_snippet_stores_in_database(
        self,
        cog: CreateSnippet,
        mock_ctx: commands.Context[Tux],
        db_service: DatabaseService,
    ) -> None:
        """Creating a snippet should persist it in the database with correct fields."""
        with patch.object(
            cog,
            "snippet_check",
            new_callable=AsyncMock,
            return_value=(True, "OK"),
        ):
            await cog.create_snippet(mock_ctx, "hello", content="Hello, world!")

        # Verify it's in the DB
        snippet = await cog.db.snippet.get_snippet_by_name_and_guild_id(
            "hello",
            TEST_GUILD_ID,
        )
        assert snippet is not None
        assert snippet.snippet_name == "hello"
        assert snippet.snippet_content == "Hello, world!"
        assert snippet.snippet_user_id == TEST_USER_ID
        assert snippet.guild_id == TEST_GUILD_ID

    @pytest.mark.usefixtures("seed_guild")
    async def test_create_duplicate_name_rejected(
        self,
        cog: CreateSnippet,
        mock_ctx: commands.Context[Tux],
        db_service: DatabaseService,
    ) -> None:
        """Creating a snippet with an existing name should fail."""
        with patch.object(
            cog,
            "snippet_check",
            new_callable=AsyncMock,
            return_value=(True, "OK"),
        ):
            await cog.create_snippet(mock_ctx, "dupe", content="First")
            mock_ctx.send.reset_mock()
            await cog.create_snippet(mock_ctx, "dupe", content="Second")

        # Should have sent an error
        mock_ctx.send.assert_called()  # send_snippet_error calls ctx.send
        # Verify only the first one exists
        snippet = await cog.db.snippet.get_snippet_by_name_and_guild_id(
            "dupe",
            TEST_GUILD_ID,
        )
        assert snippet is not None
        assert snippet.snippet_content == "First"

    @pytest.mark.usefixtures("seed_guild")
    async def test_create_snippet_invalid_name_rejected(
        self,
        cog: CreateSnippet,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Snippet names with special characters should be rejected."""
        with patch.object(
            cog,
            "snippet_check",
            new_callable=AsyncMock,
            return_value=(True, "OK"),
        ):
            await cog.create_snippet(mock_ctx, "bad name!", content="Content")

        # Should not exist in DB
        snippet = await cog.db.snippet.get_snippet_by_name_and_guild_id(
            "bad name!",
            TEST_GUILD_ID,
        )
        assert snippet is None

    @pytest.mark.usefixtures("seed_guild")
    async def test_create_alias_when_content_matches_existing_snippet(
        self,
        cog: CreateSnippet,
        mock_ctx: commands.Context[Tux],
        db_service: DatabaseService,
    ) -> None:
        """When content matches an existing snippet name, an alias should be created."""
        # Create the target snippet first
        await cog.db.snippet.create_snippet(
            snippet_name="original",
            snippet_content="Original content",
            snippet_user_id=TEST_USER_ID,
            guild_id=TEST_GUILD_ID,
        )

        # Create a snippet whose content is the name of the existing snippet
        with patch.object(
            cog,
            "snippet_check",
            new_callable=AsyncMock,
            return_value=(True, "OK"),
        ):
            await cog.create_snippet(mock_ctx, "shortcut", content="original")

        # Verify alias was created
        alias = await cog.db.snippet.get_snippet_by_name_and_guild_id(
            "shortcut",
            TEST_GUILD_ID,
        )
        assert alias is not None
        assert alias.alias == "original"

    @pytest.mark.usefixtures("seed_guild")
    async def test_banned_user_cannot_create_snippet(
        self,
        cog: CreateSnippet,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """A snippet-banned user's create attempt should be rejected before hitting the DB."""
        with patch.object(
            cog,
            "snippet_check",
            new_callable=AsyncMock,
            return_value=(False, "You are banned from using snippets."),
        ):
            await cog.create_snippet(mock_ctx, "sneaky", content="Banned content")

        snippet = await cog.db.snippet.get_snippet_by_name_and_guild_id(
            "sneaky",
            TEST_GUILD_ID,
        )
        assert snippet is None


class TestSnippetAliasResolution:
    """Test that alias chains resolve correctly."""

    @pytest.fixture
    async def cog(self, mock_bot: Tux, db_service: DatabaseService) -> SnippetsBaseCog:
        """Build a snippets cog wired to the test database."""
        cog = SnippetsBaseCog(mock_bot)
        coordinator = DatabaseCoordinator(db_service)
        mock_bot.db = coordinator
        return cog

    @pytest.fixture
    async def seed_guild(self, db_service: DatabaseService) -> None:
        """Insert a minimal guild row for FK-backed operations."""
        async with db_service.session() as session:
            session.add(Guild(id=TEST_GUILD_ID, case_count=0))
            await session.commit()

    @pytest.mark.usefixtures("seed_guild")
    async def test_alias_resolves_to_target(
        self,
        cog: SnippetsBaseCog,
        db_service: DatabaseService,
    ) -> None:
        """An alias snippet should resolve to its target's content."""
        await cog.db.snippet.create_snippet(
            snippet_name="target",
            snippet_content="Real content",
            snippet_user_id=TEST_USER_ID,
            guild_id=TEST_GUILD_ID,
        )
        await cog.db.snippet.create_snippet_alias(
            original_name="target",
            alias_name="shortcut",
            guild_id=TEST_GUILD_ID,
        )

        alias = await cog.db.snippet.get_snippet_by_name_and_guild_id(
            "shortcut",
            TEST_GUILD_ID,
        )
        assert alias is not None

        resolved, is_alias = await cog._resolve_alias(alias, TEST_GUILD_ID)
        assert is_alias is True
        assert resolved is not None
        assert resolved.snippet_content == "Real content"

    @pytest.mark.usefixtures("seed_guild")
    async def test_broken_alias_returns_none(
        self,
        cog: SnippetsBaseCog,
        db_service: DatabaseService,
    ) -> None:
        """An alias pointing to a deleted snippet should return None."""
        # Create target, create alias, then delete target
        await cog.db.snippet.create_snippet(
            snippet_name="will-delete",
            snippet_content="Temporary",
            snippet_user_id=TEST_USER_ID,
            guild_id=TEST_GUILD_ID,
        )
        await cog.db.snippet.create_snippet_alias(
            original_name="will-delete",
            alias_name="broken-link",
            guild_id=TEST_GUILD_ID,
        )
        target = await cog.db.snippet.get_snippet_by_name_and_guild_id(
            "will-delete",
            TEST_GUILD_ID,
        )
        assert target is not None
        assert target.id is not None
        await cog.db.snippet.delete_snippet_by_id(target.id)

        alias = await cog.db.snippet.get_snippet_by_name_and_guild_id(
            "broken-link",
            TEST_GUILD_ID,
        )
        assert alias is not None

        resolved, is_alias = await cog._resolve_alias(alias, TEST_GUILD_ID)
        assert is_alias is True
        assert resolved is None

    @pytest.mark.usefixtures("seed_guild")
    async def test_non_alias_resolves_to_self(
        self,
        cog: SnippetsBaseCog,
        db_service: DatabaseService,
    ) -> None:
        """A regular snippet should resolve to itself."""
        await cog.db.snippet.create_snippet(
            snippet_name="regular",
            snippet_content="Just content",
            snippet_user_id=TEST_USER_ID,
            guild_id=TEST_GUILD_ID,
        )

        snippet = await cog.db.snippet.get_snippet_by_name_and_guild_id(
            "regular",
            TEST_GUILD_ID,
        )
        assert snippet is not None

        resolved, is_alias = await cog._resolve_alias(snippet, TEST_GUILD_ID)
        assert is_alias is False
        assert resolved is not None
        assert resolved.snippet_content == "Just content"
