"""Custom settings sources for loading configuration from multiple file formats.

This module provides custom settings sources for pydantic-settings to load
configuration from TOML, YAML, and JSON files with proper priority handling.

All loaders share common logic for field resolution, with only the file
parsing implementation differing per format.
"""

import json
import tomllib
import warnings
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, cast

import yaml
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
        self._raw_data: dict[str, Any] = {}

        if self.config_file.exists():
            try:
                self._raw_data = self._parse_file(self.config_file)
            except Exception as e:
                # Graceful degradation - log error but continue
                format_name = self._get_format_name()
                warnings.warn(
                    f"Failed to load {format_name} config from {self.config_file}: {e}",
                    stacklevel=2,
                )

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

    def _flatten_dict(self, d: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        """Flatten a nested dictionary with double underscore delimiter and uppercase keys.

        Parameters
        ----------
        d : dict[str, Any]
            Dictionary to flatten
        prefix : str, optional
            Prefix for keys, by default ""

        Returns
        -------
        dict[str, Any]
            Flattened dictionary
        """
        result: dict[str, Any] = {}
        for k, v in d.items():
            key = f"{prefix}{k.upper()}"
            if isinstance(v, dict):
                result.update(self._flatten_dict(cast(dict[str, Any], v), f"{key}__"))
            else:
                result[key] = v
        return result

    def get_field_value(
        self,
        field: Any,
        field_name: str,
    ) -> tuple[Any, str, bool]:
        """Get field value (not used as we implement __call__)."""
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        """Return all loaded config data, flattened and uppercased.

        Returns
        -------
        dict[str, Any]
            Configuration data
        """
        return self._flatten_dict(self._raw_data)


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
