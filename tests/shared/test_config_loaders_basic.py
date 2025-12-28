"""
🚀 Config Loaders Basic Tests - TOML/YAML/JSON Configuration Loading.

Tests for basic configuration loader functionality.
"""

import json
from pathlib import Path

import pytest
from pydantic import Field
from pydantic_settings import BaseSettings

from tux.shared.config.loaders import (
    JsonConfigSource,
    TomlConfigSource,
    YamlConfigSource,
)


class SimpleSettings(BaseSettings):
    """Simple settings for testing."""

    debug: bool = Field(default=False)
    name: str = Field(default="test")
    port: int = Field(default=8000)
    nested__value: str = Field(default="default")


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
        json.dumps(
            {
                "debug": True,
                "name": "json_test",
                "port": 9002,
                "nested": {
                    "value": "from_json",
                },
            },
        ),
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
    assert data["NESTED__VALUE"] == "from_toml"


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

    # Warning is emitted during initialization, not when calling loader()
    with pytest.warns(UserWarning, match="Failed to load TOML config"):
        loader = TomlConfigSource(SimpleSettings, invalid_toml)

    # Should return empty dict for invalid file
    data = loader()
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

    # Warning is emitted during initialization, not when calling loader()
    with pytest.warns(UserWarning, match="Failed to load YAML config"):
        loader = YamlConfigSource(SimpleSettings, invalid_yaml)

    # Should return empty dict for invalid file
    data = loader()
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

    # Warning is emitted during initialization, not when calling loader()
    with pytest.warns(UserWarning, match="Failed to load JSON config"):
        loader = JsonConfigSource(SimpleSettings, invalid_json)

    # Should return empty dict for invalid file
    data = loader()
    assert data == {}


def test_nested_field_flattening(temp_config_files: dict[str, Path]) -> None:
    """Test that nested fields are properly flattened with double underscore.

    Parameters
    ----------
    temp_config_files : dict[str, Path]
        Temporary config files

    """
    # Test TOML
    toml_loader = TomlConfigSource(SimpleSettings, temp_config_files["toml"])
    toml_data = toml_loader()
    assert "NESTED__VALUE" in toml_data

    # Test YAML
    yaml_loader = YamlConfigSource(SimpleSettings, temp_config_files["yaml"])
    yaml_data = yaml_loader()
    assert "NESTED__VALUE" in yaml_data

    # Test JSON
    json_loader = JsonConfigSource(SimpleSettings, temp_config_files["json"])
    json_data = json_loader()
    assert "NESTED__VALUE" in json_data
