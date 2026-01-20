"""Tests for migration plugin commands."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from discord.ext import commands

from tux.core.bot import Tux
from tux.plugins.v0_1_db_migrate.plugin import (
    DatabaseMigration,
)


@pytest.mark.asyncio
@pytest.mark.unit
class TestDatabaseMigrationPlugin:
    """Test DatabaseMigration plugin."""

    @pytest.fixture
    def mock_bot(self) -> MagicMock:
        """Create mock bot."""
        bot = MagicMock(spec=Tux)
        bot.user = MagicMock()
        bot.user.id = 123456789
        return bot

    @pytest.fixture
    def plugin(self, mock_bot: MagicMock) -> DatabaseMigration:
        """Create plugin instance."""
        plug = DatabaseMigration(mock_bot)
        # Set cog on group and subcommands so Command.__call__ passes (cog, ctx, *args)
        # when invoking; otherwise cog is None and callback receives (ctx, *args) only.
        plug.migrate_group.cog = plug
        for cmd in plug.migrate_group.walk_commands():
            cmd.cog = plug
        return plug

    @pytest.fixture
    def mock_ctx(self, mock_bot: MagicMock) -> MagicMock:
        """Create mock context."""
        ctx = MagicMock(spec=commands.Context)
        ctx.bot = mock_bot
        ctx.author = MagicMock()
        ctx.author.id = 123456789  # Bot owner ID
        ctx.send = AsyncMock()
        ctx.send_help = AsyncMock()
        ctx.typing = AsyncMock()
        return ctx

    async def test_init(self, plugin: DatabaseMigration) -> None:
        """Test plugin initialization."""
        assert plugin.config is not None
        assert plugin.mapper is not None
        assert plugin.extractor is not None

    async def test_cog_check_bot_owner(
        self,
        plugin: DatabaseMigration,
        mock_ctx: MagicMock,
    ) -> None:
        """Test cog_check with bot owner."""
        with patch("tux.plugins.v0_1_db_migrate.plugin.CONFIG") as mock_config:
            mock_config.USER_IDS.BOT_OWNER_ID = 123456789
            mock_config.USER_IDS.SYSADMINS = []

            result = plugin.cog_check(mock_ctx)
            assert result is True

    async def test_cog_check_sysadmin(
        self,
        plugin: DatabaseMigration,
        mock_ctx: MagicMock,
    ) -> None:
        """Test cog_check with sysadmin."""
        mock_ctx.author.id = 999999999
        with patch("tux.plugins.v0_1_db_migrate.plugin.CONFIG") as mock_config:
            mock_config.USER_IDS.BOT_OWNER_ID = 123456789
            mock_config.USER_IDS.SYSADMINS = [999999999]

            result = plugin.cog_check(mock_ctx)
            assert result is True

    async def test_cog_check_unauthorized(
        self,
        plugin: DatabaseMigration,
        mock_ctx: MagicMock,
    ) -> None:
        """Test cog_check with unauthorized user."""
        mock_ctx.author.id = 111111111
        with patch("tux.plugins.v0_1_db_migrate.plugin.CONFIG") as mock_config:
            mock_config.USER_IDS.BOT_OWNER_ID = 123456789
            mock_config.USER_IDS.SYSADMINS = []

            result = plugin.cog_check(mock_ctx)
            assert result is False

    async def test_migrate_group_no_subcommand(
        self,
        plugin: DatabaseMigration,
        mock_ctx: MagicMock,
    ) -> None:
        """Test migrate group without subcommand."""
        mock_ctx.command = plugin.migrate_group
        await plugin.migrate_group(mock_ctx)
        mock_ctx.send_help.assert_called_once()

    async def test_migrate_audit(
        self,
        plugin: DatabaseMigration,
        mock_ctx: MagicMock,
    ) -> None:
        """Test migrate audit command."""
        with (
            patch.object(plugin, "schema_inspector", None),
            patch(
                "tux.plugins.v0_1_db_migrate.plugin.SchemaInspector",
            ) as mock_inspector_class,
            patch("asyncio.get_event_loop") as mock_loop,
        ):
            mock_inspector = MagicMock()
            mock_inspector.engine = MagicMock()
            mock_inspector.connect = MagicMock()
            mock_inspector.get_schema_report = MagicMock(
                return_value={
                    "tables": ["Guild"],
                    "relationships": [],
                },
            )
            mock_inspector.disconnect = MagicMock()
            mock_inspector_class.return_value = mock_inspector

            # Mock executor to avoid blocking
            mock_event_loop = MagicMock()
            mock_event_loop.run_in_executor = AsyncMock(
                side_effect=lambda executor, func, *args: func(*args),
            )
            mock_loop.return_value = mock_event_loop

            await plugin.migrate_audit(mock_ctx)

            mock_ctx.typing.assert_called_once()
            assert mock_ctx.send.call_count >= 2  # Embed + file

    async def test_migrate_dry_run(
        self,
        plugin: DatabaseMigration,
        mock_ctx: MagicMock,
    ) -> None:
        """Test migrate dry-run command."""
        with patch("tux.plugins.v0_1_db_migrate.plugin.CONFIG") as mock_config:
            mock_config.database_url = "sqlite:///:memory:"
            with patch(
                "tux.plugins.v0_1_db_migrate.plugin.SchemaInspector",
            ) as mock_inspector_class:
                mock_inspector = MagicMock()
                mock_inspector.engine = MagicMock()
                mock_inspector.connect = MagicMock()
                mock_inspector.disconnect = MagicMock()
                mock_inspector_class.return_value = mock_inspector

                with patch(
                    "tux.plugins.v0_1_db_migrate.plugin.DatabaseService",
                ) as mock_db_service_class:
                    mock_db_service = AsyncMock()
                    mock_db_service.connect = AsyncMock()
                    mock_db_service.disconnect = AsyncMock()
                    mock_db_service_class.return_value = mock_db_service

                    with patch(
                        "tux.plugins.v0_1_db_migrate.plugin.DatabaseMigrator",
                    ) as mock_migrator_class:
                        mock_migrator = AsyncMock()
                        mock_migrator.migrate_all = AsyncMock(
                            return_value={
                                "guild": {"success": True, "rows_migrated": 1},
                            },
                        )
                        mock_migrator_class.return_value = mock_migrator

                        await plugin.migrate_dry_run(mock_ctx, None)

                        mock_ctx.typing.assert_called_once()
                        mock_ctx.send.assert_called()

    async def test_migrate_table(
        self,
        plugin: DatabaseMigration,
        mock_ctx: MagicMock,
    ) -> None:
        """Test migrate table command."""
        with patch("tux.plugins.v0_1_db_migrate.plugin.CONFIG") as mock_config:
            mock_config.database_url = "sqlite:///:memory:"
            with patch(
                "tux.plugins.v0_1_db_migrate.plugin.SchemaInspector",
            ) as mock_inspector_class:
                mock_inspector = MagicMock()
                mock_inspector.engine = MagicMock()
                mock_inspector.connect = MagicMock()
                mock_inspector.disconnect = MagicMock()
                mock_inspector_class.return_value = mock_inspector

                with patch(
                    "tux.plugins.v0_1_db_migrate.plugin.DatabaseService",
                ) as mock_db_service_class:
                    mock_db_service = AsyncMock()
                    mock_db_service.connect = AsyncMock()
                    mock_db_service.disconnect = AsyncMock()
                    mock_db_service_class.return_value = mock_db_service

                    with patch(
                        "tux.plugins.v0_1_db_migrate.plugin.DatabaseMigrator",
                    ) as mock_migrator_class:
                        mock_migrator = AsyncMock()
                        mock_migrator.migrate_table = AsyncMock(
                            return_value={"success": True, "rows_migrated": 1},
                        )
                        mock_migrator_class.return_value = mock_migrator

                        await plugin.migrate_table(mock_ctx, "guild")

                        mock_ctx.typing.assert_called_once()
                        mock_ctx.send.assert_called()

    async def test_migrate_validate(
        self,
        plugin: DatabaseMigration,
        mock_ctx: MagicMock,
    ) -> None:
        """Test migrate validate command."""
        with patch("tux.plugins.v0_1_db_migrate.plugin.CONFIG") as mock_config:
            mock_config.database_url = "sqlite:///:memory:"
            with patch(
                "tux.plugins.v0_1_db_migrate.plugin.SchemaInspector",
            ) as mock_inspector_class:
                mock_inspector = MagicMock()
                mock_inspector.engine = MagicMock()
                mock_inspector.connect = MagicMock()
                mock_inspector.disconnect = MagicMock()
                mock_inspector_class.return_value = mock_inspector

                with patch(
                    "tux.plugins.v0_1_db_migrate.plugin.DatabaseService",
                ) as mock_db_service_class:
                    mock_db_service = AsyncMock()
                    mock_db_service.connect = AsyncMock()
                    mock_db_service.disconnect = AsyncMock()
                    mock_db_service_class.return_value = mock_db_service

                    with patch(
                        "tux.plugins.v0_1_db_migrate.plugin.MigrationValidator",
                    ) as mock_validator_class:
                        mock_validator = AsyncMock()
                        mock_validator.generate_validation_report = AsyncMock(
                            return_value={
                                "summary": {
                                    "total_tables": 1,
                                    "matching_tables": 1,
                                    "mismatched_tables": 0,
                                },
                                "row_counts": {},
                            },
                        )
                        mock_validator_class.return_value = mock_validator

                        await plugin.migrate_validate(mock_ctx)

                        mock_ctx.typing.assert_called_once()
                        mock_ctx.send.assert_called()
