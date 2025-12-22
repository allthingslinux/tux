"""Custom settings sources for loading configuration from multiple file formats.

This module provides custom settings sources for pydantic-settings to load
configuration from TOML, YAML, and JSON files with proper priority handling.

All loaders share common logic for field resolution and dictionary flattening,
with only the file parsing implementation differing per format.
"""

import json
import tomllib
import warnings
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import yaml
from pydantic.fields import FieldInfo
from pydantic_settings import PydanticBaseSettingsSource

__all__ = ["JsonConfigSource", "TomlConfigSource", "YamlConfigSource"]


class FileConfigSource(PydanticBaseSettingsSource, ABC):
    """Abstract base class for file-based configuration sources.

    Provides common functionality for loading configuration from files with
    different formats (TOML, YAML, JSON). Subclasses only need to implement
    the file parsing logic.
    """

    def __init__(self, settings_cls: type, config_file: Path) -> None:
        """Initialize file config source.

        Parameters
        ----------
        settings_cls : type
            The settings class to load config for
        config_file : Path
            Path to configuration file
        """
        super().__init__(settings_cls)
        self.config_file = config_file
        raw_data: dict[str, Any] = {}

        if self.config_file.exists():
            try:
                raw_data = self._parse_file(self.config_file)
            except Exception as e:
                # Graceful degradation - log error but continue
                format_name = self._get_format_name()
                warnings.warn(
                    f"Failed to load {format_name} config from {self.config_file}: {e}",
                    stacklevel=2,
                )

        # Normalize data (recursive uppercase keys) to match Pydantic model fields
        self._data = self._normalize_data(raw_data)

    def _normalize_data(self, d: Any) -> Any:
        """Recursively convert all dictionary keys to uppercase.

        This ensures that configuration from files (which is often lowercase)
        matches the Pydantic model field names (which are uppercase in Tux).

        Parameters
        ----------
        d : Any
            The data to normalize.

        Returns
        -------
        Any
            The normalized data.
        """
        if isinstance(d, dict):
            return {k.upper(): self._normalize_data(v) for k, v in d.items()}
        if isinstance(d, list):
            return [self._normalize_data(v) for v in d]
        return d

    def _get_format_name(self) -> str:
        """Get friendly format name for error messages.

        Returns
        -------
        str
            Format name (e.g., "TOML", "YAML", "JSON")
        """
        # Override in subclasses if needed, default to class name cleanup
        name = self.__class__.__name__.replace("ConfigSource", "")
        return name.upper()

    @abstractmethod
    def _parse_file(self, file_path: Path) -> dict[str, Any]:
        """Parse configuration file and return data as dict.

        Parameters
        ----------
        file_path : Path
            Path to the configuration file

        Returns
        -------
        dict[str, Any]
            Parsed configuration data

        Raises
        ------
        Exception
            If file parsing fails
        """

    def get_field_value(
        self,
        field: FieldInfo,
        field_name: str,
    ) -> tuple[Any, str, bool]:
        """Get field value from configuration data.

        Handles nested fields using double underscore delimiter.

        Parameters
        ----------
        field : FieldInfo
            The field info
        field_name : str
            The field name (may contain __ for nested access)

        Returns
        -------
        tuple[Any, str, bool]
            Tuple of (value, field_name, value_is_complex)
        """
        # Handle nested fields with double underscore delimiter
        value = self._data
        for key in field_name.split("__"):
            if isinstance(value, dict) and key.upper() in value:
                value = value[key.upper()]
            else:
                return None, field_name, False

        return value, field_name, False  # type: ignore[return-value]

    def __call__(self) -> dict[str, Any]:
        """Return all loaded config data.

        Returns
        -------
        dict[str, Any]
            Normalized configuration data (nested dict with uppercase keys)
        """
        return self._data


class TomlConfigSource(FileConfigSource):
    """Load configuration from a TOML file."""

    def __init__(
        self,
        settings_cls: type,
        config_file: Path = Path("config.toml"),
    ) -> None:
        """Initialize TOML config source.

        Parameters
        ----------
        settings_cls : type
            The settings class to load config for
        config_file : Path, optional
            Path to TOML config file, by default Path("config.toml")
        """
        super().__init__(settings_cls, config_file)

    def _parse_file(self, file_path: Path) -> dict[str, Any]:
        """Parse TOML file.

        Parameters
        ----------
        file_path : Path
            Path to TOML file

        Returns
        -------
        dict[str, Any]
            Parsed TOML data
        """
        with file_path.open("rb") as f:
            return tomllib.load(f)


class YamlConfigSource(FileConfigSource):
    """Load configuration from a YAML file."""

    def __init__(
        self,
        settings_cls: type,
        config_file: Path = Path("config.yaml"),
    ) -> None:
        """Initialize YAML config source.

        Parameters
        ----------
        settings_cls : type
            The settings class to load config for
        config_file : Path, optional
            Path to YAML config file, by default Path("config.yaml")
        """
        super().__init__(settings_cls, config_file)

    def _parse_file(self, file_path: Path) -> dict[str, Any]:
        """Parse YAML file.

        Parameters
        ----------
        file_path : Path
            Path to YAML file

        Returns
        -------
        dict[str, Any]
            Parsed YAML data
        """
        with file_path.open() as f:
            return yaml.safe_load(f) or {}


class JsonConfigSource(FileConfigSource):
    """Load configuration from a JSON file."""

    def __init__(
        self,
        settings_cls: type,
        config_file: Path = Path("config.json"),
    ) -> None:
        """Initialize JSON config source.

        Parameters
        ----------
        settings_cls : type
            The settings class to load config for
        config_file : Path, optional
            Path to JSON config file, by default Path("config.json")
        """
        super().__init__(settings_cls, config_file)

    def _parse_file(self, file_path: Path) -> dict[str, Any]:
        """Parse JSON file.

        Parameters
        ----------
        file_path : Path
            Path to JSON file

        Returns
        -------
        dict[str, Any]
            Parsed JSON data
        """
        with file_path.open() as f:
            return json.load(f)
