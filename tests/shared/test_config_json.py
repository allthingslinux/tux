"""
Config JSON tests: loading from config.json and priority vs env.

Uses pydantic-settings JsonConfigSettingsSource. Does not import Config
to avoid validate_environment at import.
"""

import json
from pathlib import Path

import pytest
from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

pytestmark = pytest.mark.unit


def _json_settings_sources(
    settings_cls: type[BaseSettings],
    init_settings: PydanticBaseSettingsSource,
    env_settings: PydanticBaseSettingsSource,
    dotenv_settings: PydanticBaseSettingsSource,
    file_secret_settings: PydanticBaseSettingsSource,
) -> tuple[PydanticBaseSettingsSource, ...]:
    """Order: init > env > dotenv > config.json > file_secret."""
    return (
        init_settings,
        env_settings,
        dotenv_settings,
        JsonConfigSettingsSource(settings_cls, json_file="config.json"),
        file_secret_settings,
    )


def test_json_config_loads_from_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Values are loaded from config.json when the file exists."""

    class JsonSettings(BaseSettings):
        model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)
        name: str = Field(default="default")
        port: int = Field(default=8000)
        debug: bool = Field(default=False)

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            return _json_settings_sources(
                settings_cls,
                init_settings,
                env_settings,
                dotenv_settings,
                file_secret_settings,
            )

    (tmp_path / "config.json").write_text(
        '{"name": "from_json", "port": 9000, "debug": true}',
    )
    monkeypatch.chdir(tmp_path)

    s = JsonSettings()
    assert s.name == "from_json"
    assert s.port == 9000
    assert s.debug is True


def test_json_config_missing_uses_defaults(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Defaults are used when config.json is missing."""

    class JsonSettings(BaseSettings):
        model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)
        name: str = Field(default="default")
        port: int = Field(default=8000)

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            return _json_settings_sources(
                settings_cls,
                init_settings,
                env_settings,
                dotenv_settings,
                file_secret_settings,
            )

    monkeypatch.chdir(tmp_path)
    s = JsonSettings()
    assert s.name == "default"
    assert s.port == 8000


def test_init_overrides_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Programmatic init kwargs override environment variables."""

    class JsonSettings(BaseSettings):
        model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)
        name: str = Field(default="default")
        port: int = Field(default=8000)

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            return _json_settings_sources(
                settings_cls,
                init_settings,
                env_settings,
                dotenv_settings,
                file_secret_settings,
            )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NAME", "from_env")
    monkeypatch.setenv("PORT", "9000")

    s = JsonSettings(name="from_init", port=7000)
    assert s.name == "from_init"
    assert s.port == 7000


def test_env_overrides_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Environment variables override values from config.json."""

    class JsonSettings(BaseSettings):
        model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)
        name: str = Field(default="default")
        port: int = Field(default=8000)

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            return _json_settings_sources(
                settings_cls,
                init_settings,
                env_settings,
                dotenv_settings,
                file_secret_settings,
            )

    (tmp_path / "config.json").write_text('{"name": "from_json", "port": 9000}')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NAME", "from_env")

    s = JsonSettings()
    assert s.name == "from_env"
    assert s.port == 9000


def test_json_loads_nested_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nested models in config.json are loaded and validated."""

    class Nested(BaseModel):
        host: str = "localhost"
        port: int = 5432

    class JsonSettings(BaseSettings):
        model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)
        name: str = Field(default="default")
        db: Nested = Field(default_factory=Nested)

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            return _json_settings_sources(
                settings_cls,
                init_settings,
                env_settings,
                dotenv_settings,
                file_secret_settings,
            )

    (tmp_path / "config.json").write_text(
        '{"name": "from_json", "db": {"host": "db.example.com", "port": 3306}}',
    )
    monkeypatch.chdir(tmp_path)

    s = JsonSettings()
    assert s.name == "from_json"
    assert s.db.host == "db.example.com"
    assert s.db.port == 3306


def test_json_multiple_files_latter_overrides(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When json_file is a list, later files override earlier (ConfigFileSourceMixin)."""
    p1 = tmp_path / "config1.json"
    p2 = tmp_path / "config2.json"
    p1.write_text('{"name": "first", "port": 1000}')
    p2.write_text('{"name": "second", "port": 2000}')

    class JsonSettings(BaseSettings):
        model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)
        name: str = Field(default="default")
        port: int = Field(default=8000)

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            return (
                init_settings,
                env_settings,
                dotenv_settings,
                JsonConfigSettingsSource(settings_cls, json_file=[p1, p2]),
                file_secret_settings,
            )

    monkeypatch.chdir(tmp_path)
    s = JsonSettings()
    assert s.name == "second"
    assert s.port == 2000


def test_dotenv_overrides_json_when_both_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When both .env and config.json set a field, .env wins."""
    (tmp_path / ".env").write_text("NAME=from_dotenv\nPORT=7000")
    (tmp_path / "config.json").write_text('{"name": "from_json", "port": 9000}')

    class JsonSettings(BaseSettings):
        model_config = SettingsConfigDict(
            extra="ignore",
            case_sensitive=False,
            env_file=".env",
        )
        name: str = Field(default="default")
        port: int = Field(default=8000)

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            return _json_settings_sources(
                settings_cls,
                init_settings,
                env_settings,
                dotenv_settings,
                file_secret_settings,
            )

    monkeypatch.chdir(tmp_path)
    s = JsonSettings()
    assert s.name == "from_dotenv"
    assert s.port == 7000


def test_invalid_json_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid JSON in config.json raises an error when loading."""

    class JsonSettings(BaseSettings):
        model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)
        name: str = Field(default="default")
        port: int = Field(default=8000)

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            return _json_settings_sources(
                settings_cls,
                init_settings,
                env_settings,
                dotenv_settings,
                file_secret_settings,
            )

    (tmp_path / "config.json").write_text("{invalid json}")
    monkeypatch.chdir(tmp_path)

    with pytest.raises((json.JSONDecodeError, ValueError)):
        JsonSettings()


def test_partial_json_uses_defaults_for_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When config.json provides only some keys, the rest use field defaults."""

    class JsonSettings(BaseSettings):
        model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)
        name: str = Field(default="default")
        port: int = Field(default=8000)
        enabled: bool = Field(default=True)

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            return _json_settings_sources(
                settings_cls,
                init_settings,
                env_settings,
                dotenv_settings,
                file_secret_settings,
            )

    (tmp_path / "config.json").write_text('{"name": "from_json"}')
    monkeypatch.chdir(tmp_path)

    s = JsonSettings()
    assert s.name == "from_json"
    assert s.port == 8000
    assert s.enabled is True


def test_extra_keys_ignored_with_extra_ignore(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    r"""With extra="ignore", unknown keys in config.json do not cause validation errors."""

    class JsonSettings(BaseSettings):
        model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)
        name: str = Field(default="default")
        port: int = Field(default=8000)

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            return _json_settings_sources(
                settings_cls,
                init_settings,
                env_settings,
                dotenv_settings,
                file_secret_settings,
            )

    (tmp_path / "config.json").write_text(
        '{"name": "from_json", "port": 9000, "unknown_key": "ignored"}',
    )
    monkeypatch.chdir(tmp_path)

    s = JsonSettings()
    assert s.name == "from_json"
    assert s.port == 9000


def test_json_source_uses_model_config_json_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """JsonConfigSettingsSource(settings_cls) without json_file uses model_config.json_file."""
    config_path = tmp_path / "my_config.json"
    config_path.write_text('{"name": "from_model_config", "port": 3333}')

    class JsonSettings(BaseSettings):
        model_config = SettingsConfigDict(
            extra="ignore",
            case_sensitive=False,
            json_file=str(config_path),
        )
        name: str = Field(default="default")
        port: int = Field(default=8000)

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            return (
                init_settings,
                env_settings,
                dotenv_settings,
                JsonConfigSettingsSource(settings_cls),
                file_secret_settings,
            )

    monkeypatch.chdir(tmp_path)
    s = JsonSettings()
    assert s.name == "from_model_config"
    assert s.port == 3333
