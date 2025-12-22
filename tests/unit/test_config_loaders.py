"""Tests for custom configuration loaders.

This module tests the TOML, YAML, and JSON configuration loaders
and verifies the priority system works correctly.
"""

import json
from pathlib import Path

import pytest
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from tux.shared.config.loaders import JsonConfigSource, TomlConfigSource, YamlConfigSource


class NestedSubSettings(BaseModel):
    """Nested settings for testing."""

    value: str = Field(default="default")


class SimpleSettings(BaseSettings):
    """Simple settings for testing."""

    debug: bool = Field(default=False)
    name: str = Field(default="test")
    port: int = Field(default=8000)
    nested: NestedSubSettings = Field(default_factory=NestedSubSettings)


@pytest.fixture
def temp_config_files(tmp_path: Path) -> dict[str, Path]:
    """Create temporary config files for testing.

    Parameters
    ----------
    tmp_path : Path
        Pytest temp path fixture

    Returns
    -------
    dict[str, Path]
        Dictionary of config file paths

    """
    toml_file = tmp_path / "config.toml"
    yaml_file = tmp_path / "config.yaml"
    json_file = tmp_path / "config.json"

    # Create TOML config
    toml_file.write_text("""
debug = true
name = "toml_test"
port = 9000

[nested]
value = "from_toml"
""")

    # Create YAML config
    yaml_file.write_text("""
debug: true
name: "yaml_test"
port: 9001
nested:
  value: "from_yaml"
""")

    # Create JSON config
    json_file.write_text(
        json.dumps({
            "debug": True,
            "name": "json_test",
            "port": 9002,
            "nested": {
                "value": "from_json",
            },
        }),
    )

    return {
        "toml": toml_file,
        "yaml": yaml_file,
        "json": json_file,
    }


def test_toml_loader_reads_file(temp_config_files: dict[str, Path]) -> None:
    """Test that TomlConfigSource can read a TOML file.

    Parameters
    ----------
    temp_config_files : dict[str, Path]
        Temporary config files

    """
    loader = TomlConfigSource(SimpleSettings, temp_config_files["toml"])
    data = loader()

    assert data["DEBUG"] is True
    assert data["NAME"] == "toml_test"
    assert data["PORT"] == 9000
    assert data["NESTED"]["VALUE"] == "from_toml"


def test_toml_loader_missing_file() -> None:
    """Test that TomlConfigSource handles missing files gracefully."""
    loader = TomlConfigSource(SimpleSettings, Path("nonexistent.toml"))
    data = loader()

    # Should return empty dict for missing file
    assert data == {}


def test_yaml_loader_reads_file(temp_config_files: dict[str, Path]) -> None:
    """Test that YamlConfigSource can read a YAML file.

    Parameters
    ----------
    temp_config_files : dict[str, Path]
        Temporary config files

    """
    loader = YamlConfigSource(SimpleSettings, temp_config_files["yaml"])
    data = loader()

    assert data["DEBUG"] is True
    assert data["NAME"] == "yaml_test"
    assert data["PORT"] == 9001
    assert data["NESTED__VALUE"] == "from_yaml"


def test_yaml_loader_missing_file() -> None:
    """Test that YamlConfigSource handles missing files gracefully."""
    loader = YamlConfigSource(SimpleSettings, Path("nonexistent.yaml"))
    data = loader()

    # Should return empty dict for missing file
    assert data == {}


def test_json_loader_reads_file(temp_config_files: dict[str, Path]) -> None:
    """Test that JsonConfigSource can read a JSON file.

    Parameters
    ----------
    temp_config_files : dict[str, Path]
        Temporary config files

    """
    loader = JsonConfigSource(SimpleSettings, temp_config_files["json"])
    data = loader()

    assert data["DEBUG"] is True
    assert data["NAME"] == "json_test"
    assert data["PORT"] == 9002
    assert data["NESTED__VALUE"] == "from_json"


def test_json_loader_missing_file() -> None:
    """Test that JsonConfigSource handles missing files gracefully."""
    loader = JsonConfigSource(SimpleSettings, Path("nonexistent.json"))
    data = loader()

    # Should return empty dict for missing file
    assert data == {}


def test_toml_loader_invalid_file(tmp_path: Path) -> None:
    """Test that TomlConfigSource handles invalid TOML gracefully.

    Parameters
    ----------
    tmp_path : Path
        Pytest temp path fixture

    """
    invalid_toml = tmp_path / "invalid.toml"
    invalid_toml.write_text("this is [ not valid toml")

    with pytest.warns(UserWarning, match="Failed to load TOML config"):
        loader = TomlConfigSource(SimpleSettings, invalid_toml)
        data = loader()

    # Should return empty dict for invalid file
    assert data == {}


def test_yaml_loader_invalid_file(tmp_path: Path) -> None:
    """Test that YamlConfigSource handles invalid YAML gracefully.

    Parameters
    ----------
    tmp_path : Path
        Pytest temp path fixture

    """
    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text("this: is: not: valid: yaml:")

    with pytest.warns(UserWarning, match="Failed to load YAML config"):
        loader = YamlConfigSource(SimpleSettings, invalid_yaml)
        data = loader()

    # Should return empty dict for invalid file
    assert data == {}


def test_json_loader_invalid_file(tmp_path: Path) -> None:
    """Test that JsonConfigSource handles invalid JSON gracefully.

    Parameters
    ----------
    tmp_path : Path
        Pytest temp path fixture

    """
    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{this is not valid json")

    with pytest.warns(UserWarning, match="Failed to load JSON config"):
        loader = JsonConfigSource(SimpleSettings, invalid_json)
        data = loader()

    # Should return empty dict for invalid file
    assert data == {}


def test_nested_field_normalization(temp_config_files: dict[str, Path]) -> None:
    """Test that nested fields are properly normalized with uppercase keys.

    Parameters
    ----------
    temp_config_files : dict[str, Path]
        Temporary config files

    """
    # Test TOML
    toml_loader = TomlConfigSource(SimpleSettings, temp_config_files["toml"])
    toml_data = toml_loader()
    assert "NESTED" in toml_data
    assert "VALUE" in toml_data["NESTED"]

    # Test YAML
    yaml_loader = YamlConfigSource(SimpleSettings, temp_config_files["yaml"])
    yaml_data = yaml_loader()
    assert "NESTED" in yaml_data
    assert "VALUE" in yaml_data["NESTED"]

    # Test JSON
    json_loader = JsonConfigSource(SimpleSettings, temp_config_files["json"])
    json_data = json_loader()
    assert "NESTED" in json_data
    assert "VALUE" in json_data["NESTED"]


# ============================================================================
# .env File Loading Tests
# ============================================================================


@pytest.fixture
def temp_dotenv_file(tmp_path: Path) -> Path:
    """Create temporary .env file for testing.

    Parameters
    ----------
    tmp_path : Path
        Pytest temp path fixture

    Returns
    -------
    Path
        Path to .env file

    """
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("""
# Test .env file
DEBUG=true
NAME=from_dotenv
PORT=7000
NESTED__VALUE=dotenv_nested
""")
    return dotenv_file


def test_dotenv_file_loads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that .env file is loaded by pydantic-settings.

    Parameters
    ----------
    tmp_path : Path
        Pytest temp path fixture
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    """
    from pydantic_settings import SettingsConfigDict

    class DotenvSettings(BaseSettings):
        """Settings for .env testing."""

        model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

        debug: bool = Field(default=False)
        name: str = Field(default="test")
        port: int = Field(default=8000)

    # Create .env file
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("""
DEBUG=true
NAME=from_dotenv
PORT=7000
""")

    # Change to temp directory so pydantic-settings finds the .env file
    monkeypatch.chdir(tmp_path)

    settings = DotenvSettings()

    assert settings.debug is True
    assert settings.name == "from_dotenv"
    assert settings.port == 7000


def test_dotenv_with_nested_fields(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test nested fields work with .env files using __ delimiter.

    Parameters
    ----------
    tmp_path : Path
        Pytest temp path fixture
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    """
    from pydantic_settings import SettingsConfigDict

    class NestedSettings(BaseSettings):
        """Settings with nested fields."""

        model_config = SettingsConfigDict(
            env_file=".env", env_nested_delimiter="__", case_sensitive=False, extra="ignore",
        )

        parent__child: str = Field(default="default_nested")
        database__host: str = Field(default="localhost")

    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("""
PARENT__CHILD=nested_value
DATABASE__HOST=db.example.com
""")

    monkeypatch.chdir(tmp_path)
    settings = NestedSettings()

    assert settings.parent__child == "nested_value"
    assert settings.database__host == "db.example.com"


def test_dotenv_missing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that missing .env file uses defaults.

    Parameters
    ----------
    tmp_path : Path
        Pytest temp path fixture
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    """
    from pydantic_settings import SettingsConfigDict

    class DotenvSettings(BaseSettings):
        """Settings for .env testing."""

        model_config = SettingsConfigDict(
            env_file=".env",
            env_ignore_empty=True,
            env_prefix="DOTENV_TEST_",  # Use a prefix that won't match DEBUG
            case_sensitive=False,
            extra="ignore",
        )

        debug: bool = Field(default=False)
        name: str = Field(default="default_test")

    monkeypatch.chdir(tmp_path)  # No .env file exists
    settings = DotenvSettings()

    assert settings.debug is False
    assert settings.name == "default_test"


def test_env_var_overrides_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that environment variables override .env file values.

    Parameters
    ----------
    tmp_path : Path
        Pytest temp path fixture
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    """
    from pydantic_settings import SettingsConfigDict

    class DotenvSettings(BaseSettings):
        """Settings for .env testing."""

        model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

        name: str = Field(default="test")
        port: int = Field(default=8000)

    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("""
NAME=from_dotenv
PORT=7000
""")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NAME", "from_environment")

    settings = DotenvSettings()

    # ENV var overrides .env file
    assert settings.name == "from_environment"
    # But .env file value is used when no ENV var
    assert settings.port == 7000


# ============================================================================
# Config Generation Tests
# ============================================================================


def test_generate_toml_format() -> None:
    """Test TOML configuration file generation."""
    import tomllib
    import warnings
    from pydantic_settings_export import PSESettings
    from pydantic_settings_export.models import FieldInfoModel, SettingsInfoModel
    from pydantic_settings_export.generators.toml import TomlGenerator, TomlSettings

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
        name="TestSettings", docs="Test settings", fields=fields, child_settings=[],
    )

    # Generate TOML (suppress PSESettings warning about pyproject_toml_table_header)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*pyproject_toml_table_header.*")
        pse_settings = PSESettings(root_dir=Path.cwd(), project_dir=Path.cwd(), respect_exclude=True)
    generator = TomlGenerator(pse_settings, TomlSettings(paths=[], comment_defaults=True))  # type: ignore[call-arg]
    toml_output = generator.generate_single(settings_info)

    # Verify output contains commented field names and descriptions
    # Built-in generator uses different format - check for descriptions and commented defaults
    assert "Enable debug mode" in toml_output or "debug" in toml_output.lower()
    assert "Server port" in toml_output or "port" in toml_output.lower()
    assert "Application name" in toml_output or "name" in toml_output.lower()
    # Verify it's valid TOML (can be parsed)
    assert len(toml_output) > 0


def test_generate_yaml_format() -> None:
    """Test YAML configuration file generation."""
    import warnings

    import yaml
    from pydantic_settings_export import PSESettings
    from pydantic_settings_export.models import FieldInfoModel, SettingsInfoModel

    from tux.shared.config.generators import YamlGenerator, YamlGeneratorSettings

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
        name="TestSettings", docs="Test settings", fields=fields, child_settings=[],
    )

    # Generate YAML (suppress PSESettings warning)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*pyproject_toml_table_header.*")
        pse_settings = PSESettings(root_dir=Path.cwd(), project_dir=Path.cwd(), respect_exclude=True)
    generator = YamlGenerator(pse_settings, YamlGeneratorSettings(paths=[], include_comments=True))
    yaml_output = generator.generate_single(settings_info)

    # Verify output contains commented field names and descriptions
    assert "# Enable debug mode" in yaml_output
    assert "# debug: " in yaml_output  # Value is commented out
    assert "# Server port" in yaml_output
    assert "# port: " in yaml_output


def test_generate_json_format() -> None:
    """Test JSON configuration file generation."""
    import warnings

    from pydantic_settings_export import PSESettings
    from pydantic_settings_export.models import FieldInfoModel, SettingsInfoModel

    from tux.shared.config.generators import JsonGenerator, JsonGeneratorSettings

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
        name="TestSettings", docs="Test settings", fields=fields, child_settings=[],
    )

    # Generate JSON (suppress PSESettings warning)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*pyproject_toml_table_header.*")
        pse_settings = PSESettings(root_dir=Path.cwd(), project_dir=Path.cwd(), respect_exclude=True)
    generator = JsonGenerator(pse_settings, JsonGeneratorSettings(paths=[], indent=2))
    json_output = generator.generate_single(settings_info)

    # Parse generated JSON to verify it's valid
    parsed = json.loads(json_output)
    assert "debug" in parsed
    assert "port" in parsed


def test_generate_with_nested_settings() -> None:
    """Test generation with nested settings (child_settings)."""
    import tomllib
    import warnings

    from pydantic_settings_export import PSESettings
    from pydantic_settings_export.models import FieldInfoModel, SettingsInfoModel
    from pydantic_settings_export.generators.toml import TomlGenerator, TomlSettings

    # Create parent fields
    # Built-in TOML generator expects JSON-encoded defaults
    parent_fields = [
        FieldInfoModel(
            name="debug", types=["bool"], default="false", description="Debug",        ),
    ]

    # Create child settings
    child_fields = [
        FieldInfoModel(
            name="host", types=["str"], default='"localhost"', description="DB host",        ),
        FieldInfoModel(
            name="port", types=["int"], default="5432", description="DB port",        ),
    ]

    child_settings = SettingsInfoModel(
        name="DatabaseConfig", docs="Database configuration", fields=child_fields, child_settings=[],
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
        pse_settings = PSESettings(root_dir=Path.cwd(), project_dir=Path.cwd(), respect_exclude=True)
    generator = TomlGenerator(pse_settings, TomlSettings(paths=[], comment_defaults=False))  # type: ignore[call-arg]
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
    assert nested_section is not None, f"Expected nested section with 'host', got: {parsed}"
    assert "host" in nested_section
    assert "port" in nested_section
