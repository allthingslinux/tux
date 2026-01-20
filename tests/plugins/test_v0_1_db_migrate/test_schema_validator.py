"""Tests for schema validator."""

import pytest

from tux.plugins.v0_1_db_migrate.mapper import ModelMapper
from tux.plugins.v0_1_db_migrate.schema_validator import SchemaValidator


@pytest.mark.unit
class TestSchemaValidator:
    """Test SchemaValidator class."""

    @pytest.fixture
    def mapper(self) -> ModelMapper:
        """Create mapper instance."""
        return ModelMapper()

    @pytest.fixture
    def validator(self, mapper: ModelMapper) -> SchemaValidator:
        """Create validator instance."""
        return SchemaValidator(mapper)

    def test_init(self, validator: SchemaValidator) -> None:
        """Test initialization."""
        assert validator.mapper is not None
        assert validator.expected_pks is not None
        assert validator.required_fields is not None

    def test_validate_schema_report_valid(
        self,
        validator: SchemaValidator,
    ) -> None:
        """Test validation with valid schema."""
        schema_report = {
            "tables": ["Guild", "AFKModel"],
            "table_details": {
                "Guild": [
                    {
                        "name": "guild_id",
                        "type": "BIGINT",
                        "nullable": False,
                        "default": None,
                        "primary_key": True,
                        "foreign_keys": [],
                    },
                    {
                        "name": "guild_joined_at",
                        "type": "TIMESTAMP",
                        "nullable": True,
                        "default": None,
                        "primary_key": False,
                        "foreign_keys": [],
                    },
                    {
                        "name": "case_count",
                        "type": "BIGINT",
                        "nullable": False,
                        "default": "0",
                        "primary_key": False,
                        "foreign_keys": [],
                    },
                ],
                "AFKModel": [
                    {
                        "name": "member_id",
                        "type": "BIGINT",
                        "nullable": False,
                        "default": None,
                        "primary_key": True,
                        "foreign_keys": [],
                    },
                    {
                        "name": "guild_id",
                        "type": "BIGINT",
                        "nullable": False,
                        "default": None,
                        "primary_key": True,
                        "foreign_keys": [
                            {
                                "referred_table": "Guild",
                                "referred_columns": ["guild_id"],
                            },
                        ],
                    },
                    {
                        "name": "nickname",
                        "type": "TEXT",
                        "nullable": False,
                        "default": None,
                        "primary_key": False,
                        "foreign_keys": [],
                    },
                    {
                        "name": "reason",
                        "type": "TEXT",
                        "nullable": False,
                        "default": None,
                        "primary_key": False,
                        "foreign_keys": [],
                    },
                    {
                        "name": "since",
                        "type": "TIMESTAMP",
                        "nullable": False,
                        "default": "CURRENT_TIMESTAMP",
                        "primary_key": False,
                        "foreign_keys": [],
                    },
                ],
            },
            "relationships": [
                {
                    "table": "AFKModel",
                    "columns": ["guild_id"],
                    "referred_table": "Guild",
                    "referred_columns": ["guild_id"],
                },
            ],
            "indexes": {},
        }

        result = validator.validate_schema_report(schema_report)

        assert result["valid"] is True
        assert len(result["issues"]) == 0
        assert result["summary"]["errors"] == 0

    def test_validate_schema_report_pk_mismatch(
        self,
        validator: SchemaValidator,
    ) -> None:
        """Test validation with PK mismatch."""
        schema_report = {
            "tables": ["AFKModel"],
            "table_details": {
                "AFKModel": [
                    {
                        "name": "member_id",
                        "type": "BIGINT",
                        "nullable": False,
                        "default": None,
                        "primary_key": True,
                        "foreign_keys": [],
                    },
                    {
                        "name": "guild_id",
                        "type": "BIGINT",
                        "nullable": False,
                        "default": None,
                        "primary_key": False,  # Should be True for composite PK
                        "foreign_keys": [],
                    },
                ],
            },
            "relationships": [],
            "indexes": {},
        }

        result = validator.validate_schema_report(schema_report)

        assert result["valid"] is False
        assert result["summary"]["errors"] > 0
        assert any(
            issue["type"] == "primary_key_mismatch" for issue in result["issues"]
        )

    def test_validate_schema_report_missing_fields(
        self,
        validator: SchemaValidator,
    ) -> None:
        """Test validation with missing required fields."""
        schema_report = {
            "tables": ["Guild"],
            "table_details": {
                "Guild": [
                    {
                        "name": "guild_id",
                        "type": "BIGINT",
                        "nullable": False,
                        "default": None,
                        "primary_key": True,
                        "foreign_keys": [],
                    },
                    # Missing guild_joined_at and case_count
                ],
            },
            "relationships": [],
            "indexes": {},
        }

        result = validator.validate_schema_report(schema_report)

        assert result["valid"] is False
        assert any(
            issue["type"] == "missing_required_fields" for issue in result["issues"]
        )

    def test_validate_schema_report_missing_table_details(
        self,
        validator: SchemaValidator,
    ) -> None:
        """Test validation with missing table details."""
        schema_report = {
            "tables": ["Guild", "AFKModel"],
            "table_details": {
                "Guild": [],
            },
            "relationships": [],
            "indexes": {},
        }

        result = validator.validate_schema_report(schema_report)

        assert result["valid"] is False
        assert any(
            issue["type"] == "missing_table_details" for issue in result["issues"]
        )

    def test_validate_schema_report_invalid_foreign_key(
        self,
        validator: SchemaValidator,
    ) -> None:
        """Test validation with invalid foreign key reference."""
        schema_report = {
            "tables": ["AFKModel"],
            "table_details": {
                "AFKModel": [
                    {
                        "name": "guild_id",
                        "type": "BIGINT",
                        "nullable": False,
                        "default": None,
                        "primary_key": True,
                        "foreign_keys": [
                            {
                                "referred_table": "NonExistentTable",
                                "referred_columns": ["id"],
                            },
                        ],
                    },
                ],
            },
            "relationships": [
                {
                    "table": "AFKModel",
                    "columns": ["guild_id"],
                    "referred_table": "NonExistentTable",
                    "referred_columns": ["id"],
                },
            ],
            "indexes": {},
        }

        result = validator.validate_schema_report(schema_report)

        assert result["valid"] is False
        assert any(issue["type"] == "invalid_foreign_key" for issue in result["issues"])

    def test_validate_schema_report_missing_guild_table(
        self,
        validator: SchemaValidator,
    ) -> None:
        """Test validation when Guild table is missing."""
        schema_report = {
            "tables": ["AFKModel"],
            "table_details": {
                "AFKModel": [],
            },
            "relationships": [],
            "indexes": {},
        }

        result = validator.validate_schema_report(schema_report)

        assert result["valid"] is False
        assert any(
            issue["type"] == "missing_critical_table" for issue in result["issues"]
        )

    def test_validate_primary_keys_composite(
        self,
        validator: SchemaValidator,
    ) -> None:
        """Test PK validation with correct composite PK."""
        columns = [
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
        ]

        issues = validator._validate_primary_keys("Levels", columns)

        assert len(issues) == 0

    def test_validate_primary_keys_mismatch(
        self,
        validator: SchemaValidator,
    ) -> None:
        """Test PK validation with mismatch."""
        columns = [
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
                "primary_key": False,  # Should be True
            },
        ]

        issues = validator._validate_primary_keys("AFKModel", columns)

        assert len(issues) > 0
        assert issues[0]["type"] == "primary_key_mismatch"

    def test_validate_required_fields_missing(
        self,
        validator: SchemaValidator,
    ) -> None:
        """Test required fields validation with missing fields."""
        column_names = {"guild_id"}  # Missing guild_joined_at and case_count

        issues = validator._validate_required_fields("Guild", column_names)

        assert len(issues) > 0
        assert issues[0]["type"] == "missing_required_fields"
        assert "guild_joined_at" in issues[0]["missing_fields"]
        assert "case_count" in issues[0]["missing_fields"]

    def test_validate_required_fields_present(
        self,
        validator: SchemaValidator,
    ) -> None:
        """Test required fields validation with all fields present."""
        column_names = {"guild_id", "guild_joined_at", "case_count"}

        issues = validator._validate_required_fields("Guild", column_names)

        assert len(issues) == 0
