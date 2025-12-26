"""Tests for configuration priority system.

This module tests that configuration sources are loaded in the correct
priority order: ENV vars > .env > config.toml > config.yaml > config.json > defaults.
"""

import json
from pathlib import Path

import pytest
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from tux.shared.config.loaders import (
    JsonConfigSource,
    TomlConfigSource,
    YamlConfigSource,
)


class PriorityTestConfig(BaseSettings):
    """Configuration model for testing priority order."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    VALUE_FROM_ENV: str = Field(default="default_env")
    VALUE_FROM_TOML: str = Field(default="default_toml")
    VALUE_FROM_YAML: str = Field(default="default_yaml")
    VALUE_FROM_JSON: str = Field(default="default_json")
    SHARED_VALUE: str = Field(default="default_shared")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources with multi-format support.

        Parameters
        ----------
        settings_cls : type[BaseSettings]
            The settings class
        init_settings : PydanticBaseSettingsSource
            Init settings source
        env_settings : PydanticBaseSettingsSource
            Environment settings source
        dotenv_settings : PydanticBaseSettingsSource
            Dotenv settings source
        file_secret_settings : PydanticBaseSettingsSource
            File secret settings source

        Returns
        -------
        tuple[PydanticBaseSettingsSource, ...]
            Tuple of settings sources in priority order

        """
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSource(settings_cls, Path("config.toml")),
            YamlConfigSource(settings_cls, Path("config.yaml")),
            JsonConfigSource(settings_cls, Path("config.json")),
            file_secret_settings,
        )


@pytest.fixture
def setup_config_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up test configuration files.

    Parameters
    ----------
    tmp_path : Path
        Pytest temp path fixture
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    Returns
    -------
    Path
        Temporary directory with config files

    """
    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    # Create config.toml
    toml_file = tmp_path / "config.toml"
    toml_file.write_text("""
value_from_toml = "from_toml_file"
shared_value = "toml_wins_over_yaml_and_json"
""")

    # Create config.yaml
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text("""
value_from_yaml: "from_yaml_file"
shared_value: "yaml_wins_over_json"
""")

    # Create config.json
    json_file = tmp_path / "config.json"
    json_file.write_text(
        json.dumps(
            {
                "value_from_json": "from_json_file",
                "shared_value": "json_value",
            },
        ),
    )

    return tmp_path


def test_priority_order_no_env(setup_config_files: Path) -> None:
    """Test priority order without environment variables.

    Parameters
    ----------
    setup_config_files : Path
        Temporary directory with config files

    """
    settings = PriorityTestConfig()

    # Each value should come from its respective file
    assert settings.VALUE_FROM_TOML == "from_toml_file"
    assert settings.VALUE_FROM_YAML == "from_yaml_file"
    assert settings.VALUE_FROM_JSON == "from_json_file"

    # Shared value should come from TOML (highest priority config file)
    assert settings.SHARED_VALUE == "toml_wins_over_yaml_and_json"

    # No env var set, so should use default
    assert settings.VALUE_FROM_ENV == "default_env"


def test_priority_env_overrides_all(
    setup_config_files: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that environment variables override all config files.

    Parameters
    ----------
    setup_config_files : Path
        Temporary directory with config files
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    """
    # Set environment variable
    monkeypatch.setenv("SHARED_VALUE", "env_var_wins")
    monkeypatch.setenv("VALUE_FROM_ENV", "from_environment")

    settings = PriorityTestConfig()

    # Environment variable should override everything
    assert settings.SHARED_VALUE == "env_var_wins"
    assert settings.VALUE_FROM_ENV == "from_environment"

    # Other values still from their files
    assert settings.VALUE_FROM_TOML == "from_toml_file"
    assert settings.VALUE_FROM_YAML == "from_yaml_file"
    assert settings.VALUE_FROM_JSON == "from_json_file"


def test_priority_toml_over_yaml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that TOML takes priority over YAML.

    Parameters
    ----------
    tmp_path : Path
        Pytest temp path fixture
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    """
    monkeypatch.chdir(tmp_path)

    # Create config.toml and config.yaml with conflicting values
    toml_file = tmp_path / "config.toml"
    toml_file.write_text('shared_value = "toml_value"')

    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text('shared_value: "yaml_value"')

    settings = PriorityTestConfig()

    # TOML should win
    assert settings.SHARED_VALUE == "toml_value"


def test_priority_yaml_over_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that YAML takes priority over JSON.

    Parameters
    ----------
    tmp_path : Path
        Pytest temp path fixture
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    """
    monkeypatch.chdir(tmp_path)

    # Create config.yaml and config.json with conflicting values
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text('shared_value: "yaml_value"')

    json_file = tmp_path / "config.json"
    json_file.write_text(json.dumps({"shared_value": "json_value"}))

    settings = PriorityTestConfig()

    # YAML should win
    assert settings.SHARED_VALUE == "yaml_value"


def test_missing_files_use_defaults(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that missing config files result in default values being used.

    Parameters
    ----------
    tmp_path : Path
        Pytest temp path fixture
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    """
    monkeypatch.chdir(tmp_path)

    # Don't create any config files
    settings = PriorityTestConfig()

    # All values should be defaults
    assert settings.VALUE_FROM_ENV == "default_env"
    assert settings.VALUE_FROM_TOML == "default_toml"
    assert settings.VALUE_FROM_YAML == "default_yaml"
    assert settings.VALUE_FROM_JSON == "default_json"
    assert settings.SHARED_VALUE == "default_shared"


def test_partial_config_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test priority with only some config files present.

    Parameters
    ----------
    tmp_path : Path
        Pytest temp path fixture
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    """
    monkeypatch.chdir(tmp_path)

    # Only create config.yaml
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text("""
value_from_yaml: "from_yaml_file"
shared_value: "yaml_value"
""")

    settings = PriorityTestConfig()

    # Value from YAML file
    assert settings.VALUE_FROM_YAML == "from_yaml_file"
    assert settings.SHARED_VALUE == "yaml_value"

    # Others use defaults
    assert settings.VALUE_FROM_ENV == "default_env"
    assert settings.VALUE_FROM_TOML == "default_toml"
    assert settings.VALUE_FROM_JSON == "default_json"
