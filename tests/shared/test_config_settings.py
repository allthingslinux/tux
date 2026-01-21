"""
Tests for Config (tux.shared.config.settings) helpers and behavior.

Uses init overrides to avoid depending on project .env/config.json.
Sets POSTGRES_PASSWORD to a safe value so validate_environment does not raise.
"""

import base64
from typing import Any
from unittest.mock import patch

import pytest

from tux.shared.config.models import BotInfo, ExternalServices

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _safe_env_for_config(monkeypatch: pytest.MonkeyPatch) -> None:  # type: ignore[reportUnusedFunction]
    """Ensure POSTGRES_PASSWORD is safe so validate_environment does not raise on import."""
    monkeypatch.setenv("POSTGRES_PASSWORD", "ChangeThisToAStrongPassword123!")


def _config(**kwargs: Any) -> Any:
    from tux.shared.config.settings import Config  # noqa: PLC0415

    defaults: dict[str, Any] = {
        "BOT_TOKEN": "test-token",
        "POSTGRES_PASSWORD": "ChangeThisToAStrongPassword123!",
    }
    defaults.update(kwargs)
    return Config(**defaults)


def test_config_database_url_uses_explicit_database_url() -> None:
    """When DATABASE_URL is set, database_url returns it unchanged."""
    c = _config(DATABASE_URL="postgresql://u:p@host:5433/mydb")
    assert c.database_url == "postgresql://u:p@host:5433/mydb"


def test_config_database_url_builds_from_postgres_vars() -> None:
    """When DATABASE_URL is empty, database_url is built from POSTGRES_* (pytest uses localhost)."""
    c = _config(
        DATABASE_URL="",
        POSTGRES_USER="u",
        POSTGRES_PASSWORD="p",
        POSTGRES_HOST="somehost",
        POSTGRES_PORT=5434,
        POSTGRES_DB="db",
    )
    url = c.database_url
    assert "postgresql+psycopg://u:p@" in url
    assert ":5434/" in url
    assert "/db" in url
    assert "localhost" in url


def test_config_get_prefix() -> None:
    """get_prefix returns BOT_INFO.PREFIX."""
    c = _config(BOT_INFO=BotInfo.model_construct(PREFIX="!"))
    assert c.get_prefix() == "!"


def test_config_is_prefix_override_enabled_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """is_prefix_override_enabled is True when BOT_INFO__PREFIX is in os.environ."""
    monkeypatch.setenv("BOT_INFO__PREFIX", "!")
    c = _config()
    assert c.is_prefix_override_enabled() is True


def test_config_is_prefix_override_enabled_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """is_prefix_override_enabled is False when BOT_INFO__PREFIX is not in os.environ."""
    monkeypatch.delenv("BOT_INFO__PREFIX", raising=False)
    c = _config()
    assert c.is_prefix_override_enabled() is False


def test_config_is_debug_enabled() -> None:
    """is_debug_enabled returns DEBUG."""
    assert _config(DEBUG=True).is_debug_enabled() is True
    assert _config(DEBUG=False).is_debug_enabled() is False


def test_config_get_cog_ignore_list() -> None:
    """get_cog_ignore_list returns the fixed set."""
    c = _config()
    assert c.get_cog_ignore_list() == {"test", "example"}


def test_config_get_database_url() -> None:
    """get_database_url returns the same as database_url (legacy)."""
    c = _config(DATABASE_URL="postgresql://x:y@h:5/db")
    assert c.get_database_url() == c.database_url == "postgresql://x:y@h:5/db"


def test_config_get_github_private_key_empty() -> None:
    """get_github_private_key returns empty string when GITHUB_PRIVATE_KEY is empty."""
    c = _config(
        EXTERNAL_SERVICES=ExternalServices.model_construct(GITHUB_PRIVATE_KEY=""),
    )
    assert c.get_github_private_key() == ""


def test_config_get_github_private_key_passthrough_when_pem_prefix() -> None:
    """get_github_private_key returns key as-is when it starts with -----BEGIN."""
    key = "-----BEGIN RSA PRIVATE KEY-----\nMIIE..."
    c = _config(
        EXTERNAL_SERVICES=ExternalServices.model_construct(GITHUB_PRIVATE_KEY=key),
    )
    assert c.get_github_private_key() == key


def test_config_get_github_private_key_decodes_base64() -> None:
    """get_github_private_key decodes base64 when key does not start with -----BEGIN."""
    plain = b"decoded-key"
    encoded = base64.b64encode(plain).decode("utf-8")
    c = _config(
        EXTERNAL_SERVICES=ExternalServices.model_construct(GITHUB_PRIVATE_KEY=encoded),
    )
    assert c.get_github_private_key() == "decoded-key"


def test_config_get_github_private_key_invalid_base64_returns_raw() -> None:
    """get_github_private_key returns raw key when base64 decode fails."""
    invalid_b64 = "x"
    c = _config(
        EXTERNAL_SERVICES=ExternalServices.model_construct(
            GITHUB_PRIVATE_KEY=invalid_b64,
        ),
    )
    with patch.object(base64, "b64decode", side_effect=ValueError("invalid")):
        assert c.get_github_private_key() == invalid_b64
