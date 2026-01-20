"""Migrate prisma (pre v0.1.0) to sqlmodel (v0.1.0)."""

from __future__ import annotations

import asyncio
import io
import json
from typing import Any

import discord
from discord.ext import commands
from loguru import logger
from rich.console import Console
from rich.table import Table
from sqlalchemy import func, select, text

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.database.service import DatabaseService
from tux.shared.config import CONFIG

from .config import MigrationConfig
from .extractor import DataExtractor
from .mapper import ModelMapper
from .migrator import MIGRATION_ORDER, DatabaseMigrator
from .schema_inspector import SchemaInspector
from .schema_validator import SchemaValidator
from .validator import MigrationValidator


def truncate_error_message(error: Exception, max_length: int = 3900) -> str:
    """
    Truncate error message to avoid Discord's 4000 character limit.

    Parameters
    ----------
    error : Exception
        The exception to format.
    max_length : int, optional
        Maximum length before truncation (default: 3900).

    Returns
    -------
    str
        Truncated error message.
    """
    error_msg = str(error)
    if len(error_msg) > max_length:
        error_msg = error_msg[:max_length] + "... (truncated)"
    return error_msg


def is_bot_owner_or_sysadmin(ctx: commands.Context[Tux]) -> bool:
    """
    Check if user is bot owner or sysadmin.

    Parameters
    ----------
    ctx : commands.Context[Tux]
        Command context.

    Returns
    -------
    bool
        True if user is bot owner or sysadmin, False otherwise.
    """
    user_id = ctx.author.id
    return (
        user_id == CONFIG.USER_IDS.BOT_OWNER_ID or user_id in CONFIG.USER_IDS.SYSADMINS
    )


class DatabaseMigration(BaseCog):
    """Database migration plugin for migrating from Prisma to SQLModel."""

    def __init__(self, bot: Tux) -> None:
        """
        Initialize the database migration plugin.

        Parameters
        ----------
        bot : Tux
            The bot instance.
        """
        super().__init__(bot)
        self.console = Console()
        self.config = MigrationConfig()
        self.mapper = ModelMapper()
        self.extractor = DataExtractor(self.config, self.mapper)
        self.schema_inspector: SchemaInspector | None = None
        self.migrator: DatabaseMigrator | None = None
        self.validator: MigrationValidator | None = None

    def cog_check(self, ctx: commands.Context[Any]) -> bool:
        """
        Check if user can use migration commands.

        Parameters
        ----------
        ctx : commands.Context[Any]
            Command context.

        Returns
        -------
        bool
            True if user is bot owner or sysadmin, False otherwise.
        """
        return is_bot_owner_or_sysadmin(ctx)

    @commands.group(name="migrate", invoke_without_command=True)
    async def migrate_group(self, ctx: commands.Context[Tux]) -> None:
        """
        Database migration commands.

        Use subcommands to audit, migrate, and validate data.
        """
        await ctx.send_help(ctx.command)

    @migrate_group.command(name="audit")
    async def migrate_audit(self, ctx: commands.Context[Tux]) -> None:
        """Inspect old database schema.

        Generates a comprehensive schema report showing tables, columns,
        relationships, and indexes from the old Prisma database.
        """
        """
        Inspect old database schema.

        Generates a comprehensive schema report showing tables, columns,
        relationships, and indexes from the old Prisma database.
        """
        await ctx.typing()

        try:
            # Initialize schema inspector
            self.schema_inspector = SchemaInspector(self.config)
            self.schema_inspector.connect()

            # Generate schema report
            report = self.schema_inspector.get_schema_report()

            # Format report as embed
            embed = discord.Embed(
                title="Database Schema Audit",
                description="Schema inspection of old Prisma database",
                color=discord.Color.blue(),
            )

            # Add table information
            tables = report["tables"]
            embed.add_field(
                name="Tables Found",
                value=f"{len(tables)} tables",
                inline=False,
            )

            # Add table list
            table_list = "\n".join(f"• {table}" for table in tables[:20])
            if len(tables) > 20:
                table_list += f"\n... and {len(tables) - 20} more"

            embed.add_field(
                name="Table Names",
                value=table_list or "No tables found",
                inline=False,
            )

            # Add relationships
            relationships = report["relationships"]
            embed.add_field(
                name="Relationships",
                value=f"{len(relationships)} foreign key relationships",
                inline=False,
            )

            await ctx.send(embed=embed)

            # Send detailed report as file if requested
            report_json = json.dumps(report, indent=2, default=str)
            report_bytes = report_json.encode("utf-8")
            report_file = discord.File(
                filename="schema_report.json",
                fp=io.BytesIO(report_bytes),
            )
            await ctx.send("Detailed schema report:", file=report_file)

            logger.info("Schema audit completed")

        except Exception as e:
            logger.error(f"Schema audit failed: {e}")
            error_msg = truncate_error_message(e)
            await ctx.send(f"❌ Schema audit failed: {error_msg}")

        finally:
            if self.schema_inspector:
                self.schema_inspector.disconnect()

    @migrate_group.command(name="check-pk")
    async def migrate_check_pk(  # noqa: PLR0915
        self,
        ctx: commands.Context[Tux],
        table_name: str = "AFKModel",
    ) -> None:
        """
        Check primary key constraint for a specific table.

        Parameters
        ----------
        table_name : str, optional
            Table name to check (default: AFKModel).
        """
        await ctx.typing()

        try:
            # Initialize schema inspector
            self.schema_inspector = SchemaInspector(self.config)
            self.schema_inspector.connect()

            # Get PK constraint details in executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            pk_info = await loop.run_in_executor(
                None,
                self.schema_inspector.inspect_primary_key_constraint,
                table_name,
            )

            # Get column details in executor to avoid blocking event loop
            columns = await loop.run_in_executor(
                None,
                self.schema_inspector.inspect_columns,
                table_name,
            )
            pk_columns_detail = [
                {
                    "name": col["name"],
                    "type": col["type"],
                    "nullable": col["nullable"],
                    "is_pk": col["primary_key"],
                }
                for col in columns
                if col["primary_key"]
            ]

            # Format results
            embed = discord.Embed(
                title=f"Primary Key Analysis: {table_name}",
                description="Detailed primary key constraint inspection",
                color=discord.Color.blue(),
            )

            embed.add_field(
                name="Constraint Name",
                value=pk_info["constraint_name"],
                inline=True,
            )
            embed.add_field(
                name="Column Count",
                value=str(pk_info["column_count"]),
                inline=True,
            )
            embed.add_field(
                name="Is Composite",
                value="✅ Yes" if pk_info["is_composite"] else "❌ No",
                inline=True,
            )

            # Add PK columns
            pk_cols_list = ", ".join(pk_info["columns"])
            embed.add_field(
                name="Primary Key Columns",
                value=f"`{pk_cols_list}`" if pk_cols_list else "None",
                inline=False,
            )

            # Add detailed column info
            if pk_columns_detail:
                detail_text = "\n".join(
                    f"• **{col['name']}**: {col['type']} "
                    f"({'nullable' if col['nullable'] else 'NOT NULL'})"
                    for col in pk_columns_detail
                )
                embed.add_field(
                    name="Column Details",
                    value=detail_text,
                    inline=False,
                )

            # Check against expected
            expected_pks: dict[str, list[str]] = {
                "AFKModel": ["member_id", "guild_id"],
                "Levels": ["member_id", "guild_id"],
            }

            if table_name in expected_pks:
                expected = set(expected_pks[table_name])
                actual = set(pk_info["columns"])
                if expected != actual:
                    embed.color = discord.Color.red()
                    embed.add_field(
                        name="⚠️ Mismatch Detected",
                        value=(
                            f"**Expected**: `{', '.join(expected)}`\n"
                            f"**Actual**: `{', '.join(actual)}`"
                        ),
                        inline=False,
                    )
                else:
                    embed.color = discord.Color.green()
                    embed.add_field(
                        name="✅ Match",
                        value="Primary key matches expected configuration",
                        inline=False,
                    )

            await ctx.send(embed=embed)

            # Also query PostgreSQL information_schema directly for verification
            # Run in executor to avoid blocking event loop
            engine = self.schema_inspector.engine
            if engine:

                def query_pk_info() -> tuple[Any, ...] | None:
                    with engine.connect() as conn:
                        pk_sql = text(
                            """
                            SELECT
                                tc.constraint_name,
                                string_agg(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) as columns,
                                COUNT(kcu.column_name) as column_count
                            FROM information_schema.table_constraints tc
                            JOIN information_schema.key_column_usage kcu
                                ON tc.constraint_name = kcu.constraint_name
                                AND tc.table_schema = kcu.table_schema
                            WHERE tc.constraint_type = 'PRIMARY KEY'
                                AND tc.table_name = :table_name
                                AND tc.table_schema = 'public'
                            GROUP BY tc.constraint_name
                            """,
                        )
                        result = conn.execute(pk_sql, {"table_name": table_name})
                        row = result.fetchone()
                        return tuple(row) if row else None

                pk_row = await loop.run_in_executor(None, query_pk_info)

                if pk_row:
                    # Access row by index (Row objects support indexing)
                    constraint_name = pk_row[0] if len(pk_row) > 0 else "N/A"
                    columns = pk_row[1] if len(pk_row) > 1 else "N/A"
                    column_count = pk_row[2] if len(pk_row) > 2 else "N/A"
                    embed.add_field(
                        name="PostgreSQL Information Schema",
                        value=(
                            f"**Constraint**: `{constraint_name}`\n"
                            f"**Columns**: `{columns}`\n"
                            f"**Count**: {column_count}"
                        ),
                        inline=False,
                    )

            await ctx.send(embed=embed)

            logger.info(f"PK check completed for '{table_name}'")

        except Exception as e:
            logger.error(f"PK check failed: {e}")
            error_msg = truncate_error_message(e)
            await ctx.send(f"❌ PK check failed: {error_msg}")

        finally:
            if self.schema_inspector:
                self.schema_inspector.disconnect()

    @migrate_group.command(name="check-duplicates")
    async def migrate_check_duplicates(
        self,
        ctx: commands.Context[Tux],
        table_name: str = "AFKModel",
    ) -> None:
        """
        Check for duplicate member_id values across guilds in AFKModel.

        This helps identify potential data issues if the old schema
        only has member_id as PK instead of composite (member_id, guild_id).

        Parameters
        ----------
        table_name : str, optional
            Table name to check (default: AFKModel).
        """
        await ctx.typing()

        try:
            # Initialize schema inspector
            self.schema_inspector = SchemaInspector(self.config)
            self.schema_inspector.connect()

            if not self.schema_inspector.engine:
                await ctx.send("❌ Not connected to database")
                return

            # Query for duplicates in executor to avoid blocking event loop
            engine = self.schema_inspector.engine

            def query_duplicates() -> tuple[list[tuple[Any, ...]], int, int]:
                with engine.connect() as conn:
                    # Check for duplicate member_id values
                    duplicate_query = text(
                        f"""
                        SELECT member_id, COUNT(*) as count,
                               array_agg(DISTINCT guild_id) as guild_ids
                        FROM "{table_name}"
                        GROUP BY member_id
                        HAVING COUNT(*) > 1
                        ORDER BY count DESC
                        LIMIT 20
                        """,
                    )
                    result = conn.execute(duplicate_query)
                    # Convert Row objects to tuples
                    duplicates = [tuple(row) for row in result.fetchall()]

                    # Get total row count
                    count_query = text(f'SELECT COUNT(*) FROM "{table_name}"')
                    total_count = conn.execute(count_query).scalar() or 0

                    # Get unique member_id count
                    unique_query = text(
                        f'SELECT COUNT(DISTINCT member_id) FROM "{table_name}"',
                    )
                    unique_count = conn.execute(unique_query).scalar() or 0

                    return duplicates, total_count, unique_count

            loop = asyncio.get_event_loop()
            duplicates, total_count, unique_count = await loop.run_in_executor(
                None,
                query_duplicates,
            )

            # Format results
            embed = discord.Embed(
                title=f"Duplicate Check: {table_name}",
                description="Checking for duplicate member_id values",
                color=discord.Color.green() if not duplicates else discord.Color.red(),
            )

            embed.add_field(
                name="Total Rows",
                value=str(total_count),
                inline=True,
            )
            embed.add_field(
                name="Unique member_id",
                value=str(unique_count),
                inline=True,
            )
            embed.add_field(
                name="Duplicates Found",
                value=str(len(duplicates)),
                inline=True,
            )

            if duplicates:
                duplicate_text = "\n".join(
                    f"• `member_id={row[0]}`: {row[1]} rows in guilds {row[2]}"
                    for row in duplicates[:10]
                )
                if len(duplicates) > 10:
                    duplicate_text += f"\n... and {len(duplicates) - 10} more"
                embed.add_field(
                    name="⚠️ Duplicate member_id Values",
                    value=duplicate_text,
                    inline=False,
                )
                embed.add_field(
                    name="⚠️ Impact",
                    value=(
                        "If old schema has only member_id as PK, migration will fail. "
                        "These duplicates need to be resolved before migration."
                    ),
                    inline=False,
                )
            else:
                embed.add_field(
                    name="✅ No Duplicates",
                    value="All member_id values are unique across guilds.",
                    inline=False,
                )

            await ctx.send(embed=embed)

            logger.info(f"Duplicate check completed for '{table_name}'")

        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            error_msg = truncate_error_message(e)
            await ctx.send(f"❌ Duplicate check failed: {error_msg}")

        finally:
            if self.schema_inspector:
                self.schema_inspector.disconnect()

    @migrate_group.command(name="validate-schema")
    async def migrate_validate_schema(self, ctx: commands.Context[Tux]) -> None:
        """
        Validate old database schema for migration compatibility.

        Checks the schema report against expected mappings to identify
        potential issues before migration execution.
        """
        await ctx.typing()

        try:
            # Initialize schema inspector
            self.schema_inspector = SchemaInspector(self.config)
            self.schema_inspector.connect()

            # Generate schema report in executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            report = await loop.run_in_executor(
                None,
                self.schema_inspector.get_schema_report,
            )

            # Validate schema (this is CPU-bound, fast, so no executor needed)
            schema_validator = SchemaValidator(self.mapper)
            validation_result = schema_validator.validate_schema_report(report)

            # Format results
            summary = validation_result["summary"]
            embed = discord.Embed(
                title="Schema Validation Report",
                description="Pre-migration schema compatibility check",
                color=discord.Color.green()
                if validation_result["valid"]
                else discord.Color.red(),
            )

            embed.add_field(
                name="Status",
                value="✅ Valid" if validation_result["valid"] else "❌ Issues Found",
                inline=True,
            )
            embed.add_field(
                name="Tables",
                value=str(summary["total_tables"]),
                inline=True,
            )
            embed.add_field(
                name="Errors",
                value=str(summary["errors"]),
                inline=True,
            )
            embed.add_field(
                name="Warnings",
                value=str(summary["warnings"]),
                inline=True,
            )

            # Add critical issues
            errors = [
                i for i in validation_result["issues"] if i["severity"] == "error"
            ]
            if errors:
                error_text = "\n".join(
                    f"• **{e['table']}**: {e['message']}" for e in errors[:5]
                )
                if len(errors) > 5:
                    error_text += f"\n... and {len(errors) - 5} more errors"
                embed.add_field(
                    name="Critical Issues",
                    value=error_text,
                    inline=False,
                )

            # Add warnings
            warnings = validation_result["warnings"] + [
                i for i in validation_result["issues"] if i["severity"] == "warning"
            ]
            if warnings:
                warning_text = "\n".join(
                    f"• **{w['table']}**: {w['message']}" for w in warnings[:5]
                )
                if len(warnings) > 5:
                    warning_text += f"\n... and {len(warnings) - 5} more warnings"
                embed.add_field(
                    name="Warnings",
                    value=warning_text,
                    inline=False,
                )

            await ctx.send(embed=embed)

            # Send detailed report as file
            report_json = json.dumps(validation_result, indent=2, default=str)
            report_bytes = report_json.encode("utf-8")
            report_file = discord.File(
                filename="schema_validation_report.json",
                fp=io.BytesIO(report_bytes),
            )
            await ctx.send("Detailed validation report:", file=report_file)

            logger.info("Schema validation completed")

        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            error_msg = truncate_error_message(e)
            await ctx.send(f"❌ Schema validation failed: {error_msg}")

        finally:
            if self.schema_inspector:
                self.schema_inspector.disconnect()

    @migrate_group.command(name="map")
    async def migrate_map(self, ctx: commands.Context[Tux]) -> None:
        """
        Display model mapping configuration.

        Shows how old Prisma models map to new SQLModel models,
        including field name conversions and type transformations.
        """
        await ctx.typing()

        try:
            # Create mapping table
            table = Table(title="Model Mapping Configuration")
            table.add_column("Old Table", style="cyan")
            table.add_column("New Table", style="green")
            table.add_column("Fields", style="yellow")

            for old_table, new_table in MIGRATION_ORDER:
                field_mapping = self.mapper.field_mappings.get(old_table, {})
                field_count = len(field_mapping)
                table.add_row(old_table, new_table, str(field_count))

            # Send as code block (Rich tables don't work well in Discord)
            mapping_text = "```\n"
            mapping_text += "Model Mapping Configuration\n"
            mapping_text += "=" * 50 + "\n\n"

            for old_table, new_table in MIGRATION_ORDER:
                mapping_text += f"{old_table} -> {new_table}\n"
                field_mapping = self.mapper.field_mappings.get(old_table, {})
                for old_field, new_field in list(field_mapping.items())[:5]:
                    mapping_text += f"  {old_field} -> {new_field}\n"
                if len(field_mapping) > 5:
                    mapping_text += f"  ... and {len(field_mapping) - 5} more fields\n"
                mapping_text += "\n"

            mapping_text += "```"

            await ctx.send(mapping_text)

            logger.info("Model mapping displayed")

        except Exception as e:
            logger.error(f"Failed to display mapping: {e}")
            error_msg = truncate_error_message(e)
            await ctx.send(f"❌ Failed to display mapping: {error_msg}")

    @migrate_group.command(name="dry-run")
    async def migrate_dry_run(
        self,
        ctx: commands.Context[Tux],
        table_name: str | None = None,
    ) -> None:
        """
        Test migration without committing changes.

        Parameters
        ----------
        table_name : str | None, optional
            Table name to test. If None, tests all tables.
        """
        await ctx.typing()

        db_service: DatabaseService | None = None
        try:
            # Enable dry-run mode
            self.config.dry_run = True

            # Initialize components
            self.schema_inspector = SchemaInspector(self.config)
            self.schema_inspector.connect()
            assert self.schema_inspector.engine is not None
            self.extractor.set_engine(self.schema_inspector.engine)

            db_service = DatabaseService()
            await db_service.connect(CONFIG.database_url)

            self.migrator = DatabaseMigrator(
                self.config,
                self.mapper,
                self.extractor,
                db_service,
            )

            # Run migration
            result = await self._run_migration(table_name)

            # Format results
            message = self._format_migration_results(result)
            await ctx.send(message)

            logger.info("Dry-run migration completed")

        except Exception as e:
            logger.error(f"Dry-run migration failed: {e}")
            error_msg = truncate_error_message(e)
            await ctx.send(f"❌ Dry-run failed: {error_msg}")

        finally:
            self.config.dry_run = False
            if self.schema_inspector:
                self.schema_inspector.disconnect()
            if db_service:
                await db_service.disconnect()

    @migrate_group.command(name="table")
    async def migrate_table(
        self,
        ctx: commands.Context[Tux],
        table_name: str,
    ) -> None:
        """
        Migrate a single table.

        Parameters
        ----------
        table_name : str
            New SQLModel table name to migrate.
        """
        await ctx.typing()

        db_service: DatabaseService | None = None
        try:
            # Find old table name
            old_table: str | None = None
            for old, new in MIGRATION_ORDER:
                if new == table_name:
                    old_table = old
                    break

            if not old_table:
                await ctx.send(f"❌ Unknown table: {table_name}")
                return

            # Initialize components
            self.schema_inspector = SchemaInspector(self.config)
            self.schema_inspector.connect()
            assert self.schema_inspector.engine is not None
            self.extractor.set_engine(self.schema_inspector.engine)

            db_service = DatabaseService()
            await db_service.connect(CONFIG.database_url)

            self.migrator = DatabaseMigrator(
                self.config,
                self.mapper,
                self.extractor,
                db_service,
            )

            # Run migration
            result = await self.migrator.migrate_table(old_table, table_name)

            if result["success"]:
                await ctx.send(
                    f"✅ Migration complete: {table_name} "
                    f"({result['rows_migrated']} migrated, {result['rows_failed']} failed)",
                )
            else:
                error_msg = truncate_error_message(Exception(result["error"]))
                await ctx.send(f"❌ Migration failed: {error_msg}")

            logger.info(f"Table migration completed: {table_name}")

        except Exception as e:
            logger.error(f"Table migration failed: {e}")
            error_msg = truncate_error_message(e)
            await ctx.send(f"❌ Migration failed: {error_msg}")

        finally:
            if self.schema_inspector:
                self.schema_inspector.disconnect()
            if db_service:
                await db_service.disconnect()

    @migrate_group.command(name="all")
    async def migrate_all(self, ctx: commands.Context[Tux]) -> None:
        """
        Migrate all tables in dependency order.

        ⚠️ **WARNING**: This will migrate all data from the old database.
        Make sure you have backups and have tested with dry-run first!
        """
        await ctx.typing()

        # Confirmation
        confirm_msg = await ctx.send(
            "⚠️ **WARNING**: This will migrate ALL data from the old database.\n"
            "React with ✅ to confirm, or ❌ to cancel.",
        )

        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")

        def check(reaction: discord.Reaction, user: discord.Member) -> bool:
            return (
                user.id == ctx.author.id
                and str(reaction.emoji) in ("✅", "❌")
                and reaction.message.id == confirm_msg.id
            )

        try:
            reaction, _ = await ctx.bot.wait_for(
                "reaction_add",
                timeout=60.0,
                check=check,
            )

            if str(reaction.emoji) != "✅":
                await ctx.send("❌ Migration cancelled.")
                return

        except TimeoutError:
            await ctx.send("❌ Migration cancelled (timeout).")
            return

        await ctx.typing()

        db_service: DatabaseService | None = None
        try:
            # Initialize components
            self.schema_inspector = SchemaInspector(self.config)
            self.schema_inspector.connect()
            assert self.schema_inspector.engine is not None
            self.extractor.set_engine(self.schema_inspector.engine)

            db_service = DatabaseService()
            await db_service.connect(CONFIG.database_url)

            self.migrator = DatabaseMigrator(
                self.config,
                self.mapper,
                self.extractor,
                db_service,
            )

            # Run migration
            results = await self.migrator.migrate_all()

            # Format results
            total_migrated = sum(r.get("rows_migrated", 0) for r in results.values())
            total_failed = sum(r.get("rows_failed", 0) for r in results.values())
            successful = sum(1 for r in results.values() if r.get("success"))

            embed = discord.Embed(
                title="Migration Complete",
                description=f"{successful}/{len(results)} tables migrated successfully",
                color=discord.Color.green()
                if successful == len(results)
                else discord.Color.orange(),
            )

            embed.add_field(
                name="Rows Migrated",
                value=str(total_migrated),
                inline=True,
            )
            embed.add_field(name="Rows Failed", value=str(total_failed), inline=True)

            # Add table results
            table_results = "\n".join(
                f"• {table}: {r['rows_migrated']} migrated"
                for table, r in list(results.items())[:10]
            )
            if len(results) > 10:
                table_results += f"\n... and {len(results) - 10} more tables"

            embed.add_field(name="Table Results", value=table_results, inline=False)

            await ctx.send(embed=embed)

            logger.info("Full migration completed")

        except Exception as e:
            logger.error(f"Full migration failed: {e}")
            await ctx.send(f"❌ Migration failed: {e}")

        finally:
            if self.schema_inspector:
                self.schema_inspector.disconnect()
            if db_service:
                await db_service.disconnect()

    @migrate_group.command(name="validate")
    async def migrate_validate(self, ctx: commands.Context[Tux]) -> None:
        """
        Validate migrated data.

        Compares row counts, spot-checks records, and verifies
        relationships and constraints between old and new databases.
        """
        await ctx.typing()

        db_service: DatabaseService | None = None
        try:
            # Initialize components
            self.schema_inspector = SchemaInspector(self.config)
            self.schema_inspector.connect()

            db_service = DatabaseService()
            await db_service.connect(CONFIG.database_url)

            self.validator = MigrationValidator(
                self.mapper,
                self.schema_inspector.engine,
                db_service,
            )

            # Generate validation report
            report = await self.validator.generate_validation_report()

            # Format results
            summary = report["summary"]
            embed = discord.Embed(
                title="Validation Report",
                description="Post-migration data validation",
                color=discord.Color.green()
                if summary["mismatched_tables"] == 0
                else discord.Color.orange(),
            )

            embed.add_field(
                name="Tables Matching",
                value=f"{summary['matching_tables']}/{summary['total_tables']}",
                inline=True,
            )
            embed.add_field(
                name="Tables Mismatched",
                value=str(summary["mismatched_tables"]),
                inline=True,
            )

            # Add row count details
            row_counts = report["row_counts"]
            mismatches = [
                (table, r["old_count"], r["new_count"], r["difference"])
                for table, r in row_counts.items()
                if not r["match"]
            ]

            if mismatches:
                mismatch_text = "\n".join(
                    f"• {table}: {old} -> {new} (diff: {diff})"
                    for table, old, new, diff in mismatches[:10]
                )
                if len(mismatches) > 10:
                    mismatch_text += f"\n... and {len(mismatches) - 10} more"
                embed.add_field(name="Mismatches", value=mismatch_text, inline=False)

            await ctx.send(embed=embed)

            # Send detailed report as file
            report_json = json.dumps(report, indent=2, default=str)
            report_bytes = report_json.encode("utf-8")
            report_file = discord.File(
                filename="validation_report.json",
                fp=io.BytesIO(report_bytes),
            )
            await ctx.send("Detailed validation report:", file=report_file)

            logger.info("Validation completed")

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            error_msg = truncate_error_message(e)
            await ctx.send(f"❌ Validation failed: {error_msg}")

        finally:
            if self.schema_inspector:
                self.schema_inspector.disconnect()
            if db_service:
                await db_service.disconnect()

    @migrate_group.command(name="status")
    async def migrate_status(self, ctx: commands.Context[Tux]) -> None:
        """
        Show migration status and progress.

        Displays information about which tables have been migrated
        and their row counts.
        """
        await ctx.typing()

        db_service: DatabaseService | None = None
        try:
            db_service = DatabaseService()
            await db_service.connect(CONFIG.database_url)

            # Check row counts for each table
            status_text = "```\nMigration Status\n"
            status_text += "=" * 50 + "\n\n"

            for _old_table, new_table in MIGRATION_ORDER:
                try:
                    model_class = self.mapper.get_model_class(new_table)

                    async with db_service.session() as session:
                        stmt = select(func.count()).select_from(model_class)
                        result = await session.execute(stmt)
                        count = result.scalar() or 0

                    status_text += f"{new_table:30} {count:>10} rows\n"
                except Exception as e:
                    status_text += f"{new_table:30} ERROR: {e}\n"

            status_text += "```"

            await ctx.send(status_text)

            logger.info("Migration status displayed")

        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            error_msg = truncate_error_message(e)
            await ctx.send(f"❌ Failed to get status: {error_msg}")

        finally:
            if db_service:
                await db_service.disconnect()

    async def _run_migration(self, table_name: str | None) -> dict[str, Any]:
        """Run migration for specified table or all tables."""
        if self.migrator is None:
            msg = "Migrator not initialized"
            raise RuntimeError(msg)

        if table_name:
            # Find old table name
            old_table = None
            for old, new in MIGRATION_ORDER:
                if new == table_name:
                    old_table = old
                    break

            if not old_table:
                msg = f"Unknown table: {table_name}"
                raise ValueError(msg)

            return await self.migrator.migrate_table(old_table, table_name)

        return await self.migrator.migrate_all()

    def _format_migration_results(self, result: dict[str, Any]) -> str:
        """Format migration results into a message."""
        if "success" in result:
            # Single table result
            if result["success"]:
                return (
                    f"✅ Dry-run completed: {result['rows_migrated']} rows would be migrated, "
                    f"{result['rows_failed']} would fail"
                )
            return f"❌ Dry-run failed: {result['error']}"

        # Multiple table results
        total_migrated = sum(r.get("rows_migrated", 0) for r in result.values())
        total_failed = sum(r.get("rows_failed", 0) for r in result.values())
        successful = sum(1 for r in result.values() if r.get("success"))

        return (
            f"✅ Dry-run completed: {successful}/{len(result)} tables successful, "
            f"{total_migrated} rows would be migrated, {total_failed} would fail"
        )


async def setup(bot: Tux) -> None:
    """Set up the database migration plugin."""
    await bot.add_cog(DatabaseMigration(bot))
