"""Tests for new migration plugin commands (check-pk, check-duplicates, validate-schema)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from discord.ext import commands

from tux.core.bot import Tux
from tux.plugins.v0_1_db_migrate.plugin import DatabaseMigration, truncate_error_message


@pytest.mark.asyncio
@pytest.mark.unit
class TestNewMigrationCommands:
    """Test new migration diagnostic commands."""

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

    async def test_migrate_check_pk_success(
        self,
        plugin: DatabaseMigration,
        mock_ctx: MagicMock,
    ) -> None:
        """Test migrate check-pk command success."""
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
            mock_inspector.disconnect = MagicMock()
            mock_inspector.inspect_primary_key_constraint = MagicMock(
                return_value={
                    "constraint_name": "AFKModel_pkey",
                    "columns": ["member_id"],
                    "is_composite": False,
                    "column_count": 1,
                },
            )
            mock_inspector.inspect_columns = MagicMock(
                return_value=[
                    {
                        "name": "member_id",
                        "type": "BIGINT",
                        "nullable": False,
                        "primary_key": True,
                    },
                ],
            )
            mock_inspector_class.return_value = mock_inspector

            # Mock executor
            mock_event_loop = MagicMock()
            mock_event_loop.run_in_executor = AsyncMock(
                side_effect=lambda executor, func, *args: func(*args),
            )
            mock_loop.return_value = mock_event_loop

            await plugin.migrate_check_pk(mock_ctx, "AFKModel")

            mock_ctx.typing.assert_called_once()
            assert mock_ctx.send.call_count >= 1
            # Check that embed was sent
            call_args = mock_ctx.send.call_args_list[0]
            assert "embed" in call_args.kwargs

    async def test_migrate_check_pk_with_composite(
        self,
        plugin: DatabaseMigration,
        mock_ctx: MagicMock,
    ) -> None:
        """Test migrate check-pk with composite PK."""
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
            mock_inspector.disconnect = MagicMock()
            mock_inspector.inspect_primary_key_constraint = MagicMock(
                return_value={
                    "constraint_name": "Levels_pkey",
                    "columns": ["member_id", "guild_id"],
                    "is_composite": True,
                    "column_count": 2,
                },
            )
            mock_inspector.inspect_columns = MagicMock(
                return_value=[
                    {
                        "name": "member_id",
                        "type": "BIGINT",
                        "nullable": False,
                        "primary_key": True,
                    },
                    {
                        "name": "guild_id",
                        "type": "BIGINT",
                        "nullable": False,
                        "primary_key": True,
                    },
                ],
            )
            mock_inspector_class.return_value = mock_inspector

            mock_event_loop = MagicMock()
            mock_event_loop.run_in_executor = AsyncMock(
                side_effect=lambda executor, func, *args: func(*args),
            )
            mock_loop.return_value = mock_event_loop

            await plugin.migrate_check_pk(mock_ctx, "Levels")

            mock_ctx.typing.assert_called_once()
            assert mock_ctx.send.call_count >= 1

    async def test_migrate_check_pk_error(
        self,
        plugin: DatabaseMigration,
        mock_ctx: MagicMock,
    ) -> None:
        """Test migrate check-pk command error handling."""
        with (
            patch.object(plugin, "schema_inspector", None),
            patch(
                "tux.plugins.v0_1_db_migrate.plugin.SchemaInspector",
            ) as mock_inspector_class,
        ):
            mock_inspector = MagicMock()
            mock_inspector.connect = MagicMock(
                side_effect=Exception("Connection failed"),
            )
            mock_inspector.disconnect = MagicMock()
            mock_inspector_class.return_value = mock_inspector

            await plugin.migrate_check_pk(mock_ctx, "AFKModel")

            mock_ctx.typing.assert_called_once()
            # Should send error message
            assert any(
                "❌" in str(call) or "failed" in str(call).lower()
                for call in mock_ctx.send.call_args_list
            )

    async def test_migrate_check_duplicates_no_duplicates(
        self,
        plugin: DatabaseMigration,
        mock_ctx: MagicMock,
    ) -> None:
        """Test migrate check-duplicates with no duplicates."""
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
            mock_inspector.disconnect = MagicMock()
            mock_inspector_class.return_value = mock_inspector

            # Mock executor
            mock_event_loop = MagicMock()
            mock_event_loop.run_in_executor = AsyncMock(
                side_effect=lambda executor, func, *args: func(*args),
            )
            mock_loop.return_value = mock_event_loop

            # Patch the query_duplicates function
            with patch.object(
                plugin,
                "migrate_check_duplicates",
                wraps=plugin.migrate_check_duplicates,
            ):
                await plugin.migrate_check_duplicates(mock_ctx, "AFKModel")

            mock_ctx.typing.assert_called_once()
            assert mock_ctx.send.call_count >= 1

    async def test_migrate_check_duplicates_with_duplicates(
        self,
        plugin: DatabaseMigration,
        mock_ctx: MagicMock,
    ) -> None:
        """Test migrate check-duplicates with duplicates found."""
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
            mock_inspector.disconnect = MagicMock()
            mock_inspector_class.return_value = mock_inspector

            # Mock executor
            mock_event_loop = MagicMock()
            mock_event_loop.run_in_executor = AsyncMock(
                side_effect=lambda executor, func, *args: func(*args),
            )
            mock_loop.return_value = mock_event_loop

            await plugin.migrate_check_duplicates(mock_ctx, "AFKModel")

            mock_ctx.typing.assert_called_once()
            assert mock_ctx.send.call_count >= 1
            # Check that warning was included
            call_args = mock_ctx.send.call_args_list[0]
            embed = call_args.kwargs.get("embed")
            if embed:
                assert "⚠️" in str(embed.fields) or "Duplicate" in str(embed.fields)

    async def test_migrate_validate_schema_valid(
        self,
        plugin: DatabaseMigration,
        mock_ctx: MagicMock,
    ) -> None:
        """Test migrate validate-schema with valid schema."""
        with (
            patch.object(plugin, "schema_inspector", None),
            patch(
                "tux.plugins.v0_1_db_migrate.plugin.SchemaInspector",
            ) as mock_inspector_class,
            patch("asyncio.get_event_loop") as mock_loop,
            patch(
                "tux.plugins.v0_1_db_migrate.plugin.SchemaValidator",
            ) as mock_validator_class,
        ):
            mock_inspector = MagicMock()
            mock_inspector.engine = MagicMock()
            mock_inspector.connect = MagicMock()
            mock_inspector.disconnect = MagicMock()
            mock_inspector.get_schema_report = MagicMock(
                return_value={
                    "tables": ["Guild", "AFKModel"],
                    "table_details": {
                        "Guild": [],
                        "AFKModel": [],
                    },
                    "relationships": [],
                },
            )
            mock_inspector_class.return_value = mock_inspector

            mock_validator = MagicMock()
            mock_validator.validate_schema_report = MagicMock(
                return_value={
                    "valid": True,
                    "issues": [],
                    "warnings": [],
                    "summary": {
                        "total_tables": 2,
                        "errors": 0,
                        "warnings": 0,
                    },
                },
            )
            mock_validator_class.return_value = mock_validator

            mock_event_loop = MagicMock()
            mock_event_loop.run_in_executor = AsyncMock(
                side_effect=lambda executor, func, *args: func(*args),
            )
            mock_loop.return_value = mock_event_loop

            await plugin.migrate_validate_schema(mock_ctx)

            mock_ctx.typing.assert_called_once()
            assert mock_ctx.send.call_count >= 2  # Embed + file

    async def test_migrate_validate_schema_with_errors(
        self,
        plugin: DatabaseMigration,
        mock_ctx: MagicMock,
    ) -> None:
        """Test migrate validate-schema with validation errors."""
        with (
            patch.object(plugin, "schema_inspector", None),
            patch(
                "tux.plugins.v0_1_db_migrate.plugin.SchemaInspector",
            ) as mock_inspector_class,
            patch("asyncio.get_event_loop") as mock_loop,
            patch(
                "tux.plugins.v0_1_db_migrate.plugin.SchemaValidator",
            ) as mock_validator_class,
        ):
            mock_inspector = MagicMock()
            mock_inspector.engine = MagicMock()
            mock_inspector.connect = MagicMock()
            mock_inspector.disconnect = MagicMock()
            mock_inspector.get_schema_report = MagicMock(
                return_value={
                    "tables": ["AFKModel"],
                    "table_details": {"AFKModel": []},
                    "relationships": [],
                },
            )
            mock_inspector_class.return_value = mock_inspector

            mock_validator = MagicMock()
            mock_validator.validate_schema_report = MagicMock(
                return_value={
                    "valid": False,
                    "issues": [
                        {
                            "type": "primary_key_mismatch",
                            "table": "AFKModel",
                            "severity": "error",
                            "message": "PK mismatch",
                        },
                    ],
                    "warnings": [],
                    "summary": {
                        "total_tables": 1,
                        "errors": 1,
                        "warnings": 0,
                    },
                },
            )
            mock_validator_class.return_value = mock_validator

            mock_event_loop = MagicMock()
            mock_event_loop.run_in_executor = AsyncMock(
                side_effect=lambda executor, func, *args: func(*args),
            )
            mock_loop.return_value = mock_event_loop

            await plugin.migrate_validate_schema(mock_ctx)

            mock_ctx.typing.assert_called_once()
            assert mock_ctx.send.call_count >= 2
            # Check that error was shown
            call_args = mock_ctx.send.call_args_list[0]
            embed = call_args.kwargs.get("embed")
            if embed:
                assert "❌" in str(embed.title) or "error" in str(embed.fields).lower()

    async def test_truncate_error_message(
        self,
        plugin: DatabaseMigration,
    ) -> None:
        """Test error message truncation helper."""
        # Short error message
        short_error = Exception("Short error")
        result = truncate_error_message(short_error)
        assert result == "Short error"

        # Long error message
        long_error = Exception("x" * 5000)
        result = truncate_error_message(long_error)
        assert len(result) <= 3900
        assert "... (truncated)" in result

    async def test_migrate_audit_with_executor(
        self,
        plugin: DatabaseMigration,
        mock_ctx: MagicMock,
    ) -> None:
        """Test migrate audit uses executor to avoid blocking."""
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
            mock_inspector.disconnect = MagicMock()
            mock_inspector.get_schema_report = MagicMock(
                return_value={
                    "tables": ["Guild"],
                    "relationships": [],
                },
            )
            mock_inspector_class.return_value = mock_inspector

            mock_event_loop = MagicMock()
            executor_called = False

            async def mock_run_in_executor(executor, func, *args):
                nonlocal executor_called
                executor_called = True
                return func(*args)

            mock_event_loop.run_in_executor = AsyncMock(
                side_effect=mock_run_in_executor,
            )
            mock_loop.return_value = mock_event_loop

            await plugin.migrate_audit(mock_ctx)

            # Verify executor was used
            assert executor_called is True
            mock_ctx.typing.assert_called_once()
            assert mock_ctx.send.call_count >= 2  # Embed + file
