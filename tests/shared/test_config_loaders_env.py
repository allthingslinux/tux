"""
🚀 Config Loaders Environment Tests - .env File Loading.

Tests for .env file configuration loading and priority.
"""

from pathlib import Path

import pytest
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    class DotenvSettings(BaseSettings):
        """Settings for .env testing."""

        model_config = SettingsConfigDict(
            env_file=".env",
            case_sensitive=False,
            extra="ignore",
        )

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


def test_dotenv_with_nested_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test nested fields work with .env files using __ delimiter.

    Parameters
    ----------
    tmp_path : Path
        Pytest temp path fixture
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    """

    class NestedSettings(BaseSettings):
        """Settings with nested fields."""

        model_config = SettingsConfigDict(
            env_file=".env",
            env_nested_delimiter="__",
            case_sensitive=False,
            extra="ignore",
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


def test_env_var_overrides_dotenv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that environment variables override .env file values.

    Parameters
    ----------
    tmp_path : Path
        Pytest temp path fixture
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    """

    class DotenvSettings(BaseSettings):
        """Settings for .env testing."""

        model_config = SettingsConfigDict(
            env_file=".env",
            case_sensitive=False,
            extra="ignore",
        )

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
