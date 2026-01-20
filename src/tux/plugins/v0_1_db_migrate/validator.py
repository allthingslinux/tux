"""
Migration validator for post-migration verification.

Validates migrated data by comparing row counts, spot-checking records,
and verifying relationships and constraints.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from typing import Any, cast

from loguru import logger
from sqlalchemy import func, select, text
from sqlalchemy.engine import Engine, Result
from sqlalchemy.sql.selectable import Select

from tux.database.models import Guild, GuildConfig
from tux.database.service import DatabaseService

from .mapper import ModelMapper
from .migrator import MIGRATION_ORDER


class MigrationValidator:
    """
    Validate migrated data between old and new databases.

    Provides methods to verify data integrity, row counts,
    relationships, and constraints after migration.

    Attributes
    ----------
    mapper : ModelMapper
        Model mapper instance.
    old_engine : Engine | None
        SQLAlchemy sync engine for old database.
    db_service : DatabaseService
        Database service for new database.
    """

    def __init__(
        self,
        mapper: ModelMapper,
        old_engine: Engine | None,
        db_service: DatabaseService,
    ) -> None:
        """
        Initialize migration validator.

        Parameters
        ----------
        mapper : ModelMapper
            Model mapper instance.
        old_engine : Engine | None
            SQLAlchemy sync engine for old database.
        db_service : DatabaseService
            Database service for new database.
        """
        self.mapper = mapper
        self.old_engine = old_engine
        self.db_service = db_service

    def get_old_row_count(self, old_table_name: str) -> int:
        """
        Get row count from old database.

        Parameters
        ----------
        old_table_name : str
            Old Prisma table name.

        Returns
        -------
        int
            Number of rows in old table.
        """
        if not self.old_engine:
            logger.warning("Old engine not set, cannot get row count")
            return 0

        try:
            with self.old_engine.connect() as conn:
                result = conn.execute(
                    text(f'SELECT COUNT(*) FROM "{old_table_name}"'),
                )
                return result.scalar() or 0
        except Exception as e:
            logger.error(
                f"Failed to get row count from old table '{old_table_name}': {e}",
            )
            return 0

    async def get_new_row_count(self, new_table_name: str) -> int:
        """
        Get row count from new database.

        Parameters
        ----------
        new_table_name : str
            New SQLModel table name.

        Returns
        -------
        int
            Number of rows in new table.
        """
        try:
            model_class = self.mapper.get_model_class(new_table_name)

            async with self.db_service.session() as session:
                stmt = select(func.count()).select_from(model_class)
                result = await session.execute(stmt)
                return result.scalar() or 0
        except Exception as e:
            logger.error(
                f"Failed to get row count from new table '{new_table_name}': {e}",
            )
            return 0

    async def validate_row_counts(self) -> dict[str, dict[str, Any]]:
        """
        Validate row counts match between old and new databases.

        Returns
        -------
        dict[str, dict[str, Any]]
            Dictionary mapping table names to validation results with keys:
            - old_count: int
            - new_count: int
            - match: bool
            - difference: int
        """
        logger.info("Validating row counts")

        results: dict[str, dict[str, Any]] = {}

        for old_table_name, new_table_name in MIGRATION_ORDER:
            old_count = self.get_old_row_count(old_table_name)
            new_count = await self.get_new_row_count(new_table_name)

            match = old_count == new_count
            difference = new_count - old_count

            results[new_table_name] = {
                "old_count": old_count,
                "new_count": new_count,
                "match": match,
                "difference": difference,
            }

            if not match:
                logger.warning(
                    f"Row count mismatch for '{new_table_name}': "
                    f"old={old_count}, new={new_count}, diff={difference}",
                )
            else:
                logger.debug(
                    f"Row count match for '{new_table_name}': {old_count}",
                )

        return results

    async def validate_sample_data(
        self,
        table_name: str,
        sample_size: int = 10,
    ) -> dict[str, Any]:
        """
        Spot-check random records from migrated data.

        Parameters
        ----------
        table_name : str
            New SQLModel table name.
        sample_size : int, optional
            Number of random records to check (default: 10).

        Returns
        -------
        dict[str, Any]
            Validation result with keys:
            - samples_checked: int
            - samples_valid: int
            - samples_invalid: int
            - errors: list[str]
        """
        logger.info(f"Validating sample data for '{table_name}'")

        try:
            model_class = self.mapper.get_model_class(table_name)

            async with self.db_service.session() as session:
                # Get total count
                count_stmt = select(func.count()).select_from(model_class)
                total_count = (await session.execute(count_stmt)).scalar() or 0

                if total_count == 0:
                    logger.warning(f"No rows to validate in '{table_name}'")
                    return {
                        "samples_checked": 0,
                        "samples_valid": 0,
                        "samples_invalid": 0,
                        "errors": [],
                    }

                # Sample random records
                sample_size = min(sample_size, total_count)
                sample_indices = random.sample(range(total_count), sample_size)

                samples_valid = 0
                samples_invalid = 0
                errors: list[str] = []

                for idx in sample_indices:
                    try:
                        stmt = select(model_class).offset(idx).limit(1)
                        result = await session.execute(stmt)
                        instance = result.scalar_one_or_none()

                        if instance is None:
                            samples_invalid += 1
                            errors.append(f"Sample {idx}: record not found")
                            continue

                        # Validate instance (Pydantic validation)
                        # This will raise ValidationError if invalid
                        model_class(**instance.model_dump())

                        samples_valid += 1

                    except Exception as e:
                        samples_invalid += 1
                        errors.append(f"Sample {idx}: {e}")

                logger.info(
                    f"Sample validation for '{table_name}': "
                    f"{samples_valid}/{sample_size} valid",
                )

                return {
                    "samples_checked": sample_size,
                    "samples_valid": samples_valid,
                    "samples_invalid": samples_invalid,
                    "errors": errors,
                }

        except Exception as e:
            logger.error(f"Failed to validate sample data for '{table_name}': {e}")
            return {
                "samples_checked": 0,
                "samples_valid": 0,
                "samples_invalid": 0,
                "errors": [str(e)],
            }

    async def validate_relationships(self) -> dict[str, Any]:
        """
        Validate foreign key relationships are intact.

        Returns
        -------
        dict[str, Any]
            Validation result with keys:
            - relationships_checked: int
            - relationships_valid: int
            - relationships_invalid: int
            - errors: list[str]
        """
        logger.info("Validating foreign key relationships")

        relationships_checked = 0
        relationships_valid = 0
        relationships_invalid = 0
        errors: list[str] = []

        # Check guild relationships
        try:
            async with self.db_service.session() as session:
                # Check GuildConfig -> Guild
                stmt = select(GuildConfig).limit(100)  # Sample
                result = await session.execute(stmt)
                configs = result.unique().scalars().all()

                for config in configs:
                    relationships_checked += 1
                    # Check if guild exists
                    guild_stmt = select(Guild).where(Guild.id == config.id)  # type: ignore[arg-type]
                    guild_result = await session.execute(guild_stmt)
                    if guild_result.unique().scalar_one_or_none() is None:
                        relationships_invalid += 1
                        errors.append(f"GuildConfig {config.id}: missing guild")
                    else:
                        relationships_valid += 1

        except Exception as e:
            logger.error(f"Failed to validate relationships: {e}")
            errors.append(str(e))

        logger.info(
            f"Relationship validation: {relationships_valid}/{relationships_checked} valid",
        )

        return {
            "relationships_checked": relationships_checked,
            "relationships_valid": relationships_valid,
            "relationships_invalid": relationships_invalid,
            "errors": errors,
        }

    async def validate_constraints(self) -> dict[str, Any]:
        """
        Validate database constraints are satisfied.

        Returns
        -------
        dict[str, Any]
            Validation result with keys:
            - constraints_checked: int
            - constraints_valid: int
            - constraints_invalid: int
            - errors: list[str]
        """
        logger.info("Validating database constraints")

        constraints_checked = 0
        constraints_valid = 0
        constraints_invalid = 0
        errors: list[str] = []

        # Check unique constraints
        try:
            async with self.db_service.session() as session:
                # Check for duplicate guild IDs
                stmt = cast(
                    Select[Any],
                    (
                        select(Guild.id, func.count(Guild.id).label("count"))  # type: ignore[call-overload]
                        .group_by(Guild.id)
                        .having(func.count(Guild.id) > 1)  # type: ignore[arg-type]
                    ),
                )
                result: Result[Any] = await session.execute(stmt)
                duplicates: Sequence[Any] = result.all()

                constraints_checked += 1
                if duplicates:
                    constraints_invalid += 1
                    errors.append(
                        f"Duplicate guild IDs found: {[int(d[0]) for d in duplicates]}",
                    )
                else:
                    constraints_valid += 1

        except Exception as e:
            logger.error(f"Failed to validate constraints: {e}")
            errors.append(str(e))

        logger.info(
            f"Constraint validation: {constraints_valid}/{constraints_checked} valid",
        )

        return {
            "constraints_checked": constraints_checked,
            "constraints_valid": constraints_valid,
            "constraints_invalid": constraints_invalid,
            "errors": errors,
        }

    async def generate_validation_report(self) -> dict[str, Any]:
        """
        Generate comprehensive validation report.

        Returns
        -------
        dict[str, Any]
            Complete validation report with all validation results.
        """
        logger.info("Generating validation report")

        report = {
            "row_counts": await self.validate_row_counts(),
            "relationships": await self.validate_relationships(),
            "constraints": await self.validate_constraints(),
        }

        # Add sample validation for each table
        sample_results: dict[str, Any] = {}

        for _, new_table_name in MIGRATION_ORDER:
            sample_results[new_table_name] = await self.validate_sample_data(
                new_table_name,
            )

        report["samples"] = sample_results

        # Summary
        total_tables = len(report["row_counts"])
        matching_tables = sum(r["match"] for r in report["row_counts"].values())

        report["summary"] = {
            "total_tables": total_tables,
            "matching_tables": matching_tables,
            "mismatched_tables": total_tables - matching_tables,
        }

        logger.info(
            f"Validation report generated: {matching_tables}/{total_tables} tables match",
        )

        return report
