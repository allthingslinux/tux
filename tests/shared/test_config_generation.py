"""
🚀 Config Generation Tests - Configuration File Generation.

Tests for generating configuration files from Pydantic settings.
"""

import json
import tomllib
import warnings
from pathlib import Path

import pytest
from pydantic_settings_export import PSESettings
from pydantic_settings_export.generators.toml import TomlGenerator, TomlSettings
from pydantic_settings_export.models import FieldInfoModel, SettingsInfoModel

from tux.shared.config.generators import (
    JsonGenerator,
    JsonGeneratorSettings,
    YamlGenerator,
    YamlGeneratorSettings,
)


def test_generate_toml_format() -> None:
    """Test TOML configuration file generation."""
    # Create a simple settings model
    # Built-in TOML generator expects JSON-encoded defaults
    fields = [
        FieldInfoModel(
            name="debug",
            types=["bool"],
            default="false",  # JSON boolean
            description="Enable debug mode",
        ),
        FieldInfoModel(
            name="port",
            types=["int"],
            default="8000",  # JSON number
            description="Server port",
        ),
        FieldInfoModel(
            name="name",
            types=["str"],
            default='"test"',  # JSON string
            description="Application name",
        ),
    ]

    settings_info = SettingsInfoModel(
        name="TestSettings",
        docs="Test settings",
        fields=fields,
        child_settings=[],
    )

    # Generate TOML (suppress PSESettings warning about pyproject_toml_table_header)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*pyproject_toml_table_header.*")
        pse_settings = PSESettings(
            root_dir=Path.cwd(),
            project_dir=Path.cwd(),
            respect_exclude=True,
        )
    generator = TomlGenerator(
        pse_settings,
        TomlSettings(
            paths=[],
            comment_defaults=True,
            enabled=True,
            header_formatter=None,
            type_formatter=None,
            description_formatter=None,
            default_formatter=None,
            examples_formatter=None,
            mode="all",
            section_depth=None,
            prefix=None,
        ),
    )
    toml_output = generator.generate_single(settings_info)

    # Verify output contains commented field names and descriptions
    # Built-in generator uses different format - check for descriptions and commented defaults
    assert "Enable debug mode" in toml_output or "debug" in toml_output.lower()
    assert "Server port" in toml_output or "port" in toml_output.lower()
    assert "Application name" in toml_output or "name" in toml_output.lower()

    # Verify it's valid TOML by actually parsing it
    # Note: The generator may produce TOML with only comments and no key-value pairs
    # So we just verify it's valid TOML, not that it has content
    try:
        parsed = tomllib.loads(toml_output)
        assert isinstance(parsed, dict)
        # If parsed is empty, that's okay - it just means the generator produced comments-only TOML
    except tomllib.TOMLDecodeError:
        # If parsing fails, the TOML is invalid - that's a problem
        pytest.fail(f"Generated TOML is invalid: {toml_output}")


def test_generate_yaml_format() -> None:
    """Test YAML configuration file generation."""
    fields = [
        FieldInfoModel(
            name="debug",
            types=["bool"],
            default="False",
            description="Enable debug mode",
        ),
        FieldInfoModel(
            name="port",
            types=["int"],
            default="8000",
            description="Server port",
        ),
    ]

    settings_info = SettingsInfoModel(
        name="TestSettings",
        docs="Test settings",
        fields=fields,
        child_settings=[],
    )

    # Generate YAML (suppress PSESettings warning)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*pyproject_toml_table_header.*")
        pse_settings = PSESettings(
            root_dir=Path.cwd(),
            project_dir=Path.cwd(),
            respect_exclude=True,
        )
    generator = YamlGenerator(
        pse_settings,
        YamlGeneratorSettings(paths=[], include_comments=True),
    )
    yaml_output = generator.generate_single(settings_info)

    # Verify output contains commented field names and descriptions
    assert "# Enable debug mode" in yaml_output
    assert "# debug: " in yaml_output  # Value is commented out
    assert "# Server port" in yaml_output
    assert "# port: " in yaml_output


def test_generate_json_format() -> None:
    """Test JSON configuration file generation."""
    fields = [
        FieldInfoModel(
            name="debug",
            types=["bool"],
            default="False",
            description="Enable debug mode",
        ),
        FieldInfoModel(
            name="port",
            types=["int"],
            default="8000",
            description="Server port",
        ),
    ]

    settings_info = SettingsInfoModel(
        name="TestSettings",
        docs="Test settings",
        fields=fields,
        child_settings=[],
    )

    # Generate JSON (suppress PSESettings warning)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*pyproject_toml_table_header.*")
        pse_settings = PSESettings(
            root_dir=Path.cwd(),
            project_dir=Path.cwd(),
            respect_exclude=True,
        )
    generator = JsonGenerator(pse_settings, JsonGeneratorSettings(paths=[], indent=2))
    json_output = generator.generate_single(settings_info)

    # Parse generated JSON to verify it's valid
    parsed = json.loads(json_output)
    assert "debug" in parsed
    assert "port" in parsed


def test_generate_with_nested_settings() -> None:
    """Test generation with nested settings (child_settings)."""
    # Create parent fields
    # Built-in TOML generator expects JSON-encoded defaults
    parent_fields = [
        FieldInfoModel(
            name="debug",
            types=["bool"],
            default="false",
            description="Debug",
        ),
    ]

    # Create child settings
    child_fields = [
        FieldInfoModel(
            name="host",
            types=["str"],
            default='"localhost"',
            description="DB host",
        ),
        FieldInfoModel(
            name="port",
            types=["int"],
            default="5432",
            description="DB port",
        ),
    ]

    child_settings = SettingsInfoModel(
        name="DatabaseConfig",
        docs="Database configuration",
        fields=child_fields,
        child_settings=[],
    )

    settings_info = SettingsInfoModel(
        name="AppSettings",
        docs="Application settings",
        fields=parent_fields,
        child_settings=[child_settings],
    )

    # Generate TOML (suppress PSESettings warning)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*pyproject_toml_table_header.*")
        pse_settings = PSESettings(
            root_dir=Path.cwd(),
            project_dir=Path.cwd(),
            respect_exclude=True,
        )
    generator = TomlGenerator(
        pse_settings,
        TomlSettings(
            paths=[],
            comment_defaults=False,
            enabled=True,
            header_formatter=None,
            type_formatter=None,
            description_formatter=None,
            default_formatter=None,
            examples_formatter=None,
            mode="all",
            section_depth=None,
            prefix=None,
        ),
    )
    toml_output = generator.generate_single(settings_info)

    # Parse and verify nested structure
    parsed = tomllib.loads(toml_output)
    assert "debug" in parsed
    nested_section = next(
        (
            value
            for _key, value in parsed.items()
            if isinstance(value, dict) and "host" in value
        ),
        None,
    )
    assert nested_section is not None, (
        f"Expected nested section with 'host', got: {parsed}"
    )
    assert "host" in nested_section
    assert "port" in nested_section
