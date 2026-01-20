"""
Data extractor for old Prisma database.

Extracts data from old database in batches, transforms it using
the model mapper, and validates against SQLModel schemas.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from loguru import logger
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .config import MigrationConfig
from .mapper import ModelMapper


class DataExtractor:
    """
    Extract and transform data from old Prisma database.

    Provides batch extraction with transformation and validation
    for migrating data to new SQLModel database.

    Attributes
    ----------
    config : MigrationConfig
        Migration configuration.
    mapper : ModelMapper
        Model mapper for field transformations.
    engine : Engine | None
        SQLAlchemy sync engine for old database.
    """

    def __init__(self, config: MigrationConfig, mapper: ModelMapper) -> None:
        """
        Initialize data extractor.

        Parameters
        ----------
        config : MigrationConfig
            Migration configuration.
        mapper : ModelMapper
            Model mapper instance.
        """
        self.config = config
        self.mapper = mapper
        self.engine: Engine | None = None

    def set_engine(self, engine: Engine) -> None:
        """
        Set the database engine for extraction.

        Parameters
        ----------
        engine : Engine
            SQLAlchemy sync engine for old database.
        """
        self.engine = engine

    def get_row_count(self, old_table_name: str) -> int:
        """
        Get total row count for a table.

        Parameters
        ----------
        old_table_name : str
            Old Prisma table name.

        Returns
        -------
        int
            Total number of rows in the table.

        Raises
        ------
        RuntimeError
            If engine is not set.
        """
        if not self.engine:
            msg = "Engine not set. Call set_engine() first."
            raise RuntimeError(msg)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(f'SELECT COUNT(*) FROM "{old_table_name}"'),
                )
                count = result.scalar()
                return count or 0
        except Exception as e:
            logger.error(f"Failed to get row count for '{old_table_name}': {e}")
            raise

    def extract_table(
        self,
        old_table_name: str,
        batch_size: int | None = None,
    ) -> Iterator[list[dict[str, Any]]]:
        """
        Extract data from a table in batches.

        Parameters
        ----------
        old_table_name : str
            Old Prisma table name.
        batch_size : int | None, optional
            Number of rows per batch. If None, uses config batch_size.

        Yields
        ------
        list[dict[str, Any]]
            Batch of transformed rows ready for insertion.

        Raises
        ------
        RuntimeError
            If engine is not set.
        """
        if not self.engine:
            msg = "Engine not set. Call set_engine() first."
            raise RuntimeError(msg)

        batch_size = batch_size or self.config.batch_size
        offset = 0

        logger.info(
            f"Extracting data from '{old_table_name}' (batch_size={batch_size})",
        )

        # Determine primary key column(s) for ordering
        # Most tables use a single PK column, but some use composite keys
        # For composite keys, we order by both parts to ensure consistent ordering
        # Special cases:
        # - Case: Order by guild_id and case_created_at to ensure chronological order
        #   even if case_number has gaps. This ensures proper insertion order.
        #   Falls back to case_id if case_created_at is NULL.
        pk_order_by: dict[str, str] = {
            "Guild": '"guild_id"',
            "GuildConfig": '"guild_id"',
            "Case": '"guild_id", "case_created_at" NULLS LAST, "case_id"',  # Order by guild and creation time for proper chronological order, fallback to case_id
            "Snippet": '"snippet_id"',
            "Reminder": '"reminder_id"',
            "AFKModel": '"member_id", "guild_id"',  # Order by both parts (old DB may have only member_id as PK, but we order by both for consistency)
            "Levels": '"member_id", "guild_id"',  # Composite PK: order by both parts
            "Starboard": '"guild_id"',
            "StarboardMessage": '"message_id"',
            "Note": '"note_id"',
        }
        order_by_clause = pk_order_by.get(old_table_name, '"id"')

        while True:
            try:
                with self.engine.connect() as conn:
                    # Fetch batch
                    query = text(
                        f'SELECT * FROM "{old_table_name}" '
                        f"ORDER BY {order_by_clause} LIMIT :limit OFFSET :offset",
                    )
                    result = conn.execute(
                        query,
                        {"limit": batch_size, "offset": offset},
                    )

                    rows = result.fetchall()
                    if not rows:
                        break

                    # Convert rows to dictionaries
                    column_names = result.keys()
                    batch = [dict(zip(column_names, row, strict=True)) for row in rows]

                    # Transform batch
                    transformed_batch: list[dict[str, Any]] = []
                    for old_row in batch:
                        try:
                            transformed_row = self.transform_row(
                                old_table_name,
                                old_row,
                            )
                            if transformed_row:
                                transformed_batch.append(transformed_row)
                        except Exception as e:
                            logger.warning(
                                f"Failed to transform row in '{old_table_name}': {e}",
                            )
                            continue

                    if transformed_batch:
                        yield transformed_batch

                    # Check if we've processed all rows
                    if len(rows) < batch_size:
                        break

                    offset += batch_size

            except Exception as e:
                logger.error(f"Failed to extract batch from '{old_table_name}': {e}")
                raise

        logger.success(f"Finished extracting data from '{old_table_name}'")

    def transform_row(
        self,
        old_table_name: str,
        old_row: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Transform a single row using the model mapper.

        Parameters
        ----------
        old_table_name : str
            Old Prisma table name.
        old_row : dict[str, Any]
            Row data from old database.

        Returns
        -------
        dict[str, Any]
            Transformed row data.

        Notes
        -----
        This method delegates to ModelMapper.transform_row().
        """
        return self.mapper.transform_row(old_table_name, old_row)

    def validate_row(
        self,
        table_name: str,
        row_data: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """
        Validate transformed row against SQLModel schema.

        Parameters
        ----------
        table_name : str
            New SQLModel table name.
        row_data : dict[str, Any]
            Transformed row data.

        Returns
        -------
        tuple[bool, str | None]
            (is_valid, error_message). If valid, error_message is None.

        Notes
        -----
        Uses Pydantic validation through SQLModel to ensure data
        conforms to model constraints.
        """
        try:
            model_class = self.mapper.get_model_class(table_name)

            # Create model instance to validate
            # This will raise ValidationError if data is invalid
            model_class(**row_data)
        except ValidationError as e:
            error_msg = str(e)
            logger.debug(f"Validation error for row in '{table_name}': {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected validation error: {e}"
            logger.warning(f"Validation error for row in '{table_name}': {error_msg}")
            return False, error_msg
        else:
            # If we get here, validation passed
            return True, None

    def extract_and_validate_table(
        self,
        old_table_name: str,
        batch_size: int | None = None,
    ) -> Iterator[tuple[list[dict[str, Any]], int, int]]:
        """
        Extract, transform, and validate table data in batches.

        Parameters
        ----------
        old_table_name : str
            Old Prisma table name.
        batch_size : int | None, optional
            Number of rows per batch.

        Yields
        ------
        tuple[list[dict[str, Any]], int, int]
            (valid_rows, total_rows, invalid_rows) for each batch.

        Notes
        -----
        This is a convenience method that combines extraction,
        transformation, and validation in one generator.
        """
        new_table_name = self.mapper.get_table_mapping(old_table_name)
        total_rows = 0
        invalid_rows = 0

        for batch in self.extract_table(old_table_name, batch_size):
            valid_rows: list[dict[str, Any]] = []
            for row in batch:
                is_valid, error = self.validate_row(new_table_name, row)
                if is_valid:
                    valid_rows.append(row)
                else:
                    invalid_rows += 1
                    logger.debug(f"Invalid row skipped: {error}")

            total_rows += len(batch)
            yield valid_rows, total_rows, invalid_rows
