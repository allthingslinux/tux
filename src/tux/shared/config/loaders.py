"""Custom settings sources for loading configuration from multiple file formats.

This module provides custom settings sources for pydantic-settings to load
configuration from TOML, YAML, and JSON files with proper priority handling.

Note: Import warnings (PLC0415) for `warnings` module are intentional - lazy imports
in error handlers avoid import overhead when errors don't occur.
"""

import json
import tomllib
import warnings
from pathlib import Path
from typing import Any

import yaml
from pydantic.fields import FieldInfo
from pydantic_settings import PydanticBaseSettingsSource


class TomlConfigSource(PydanticBaseSettingsSource):
    """Load configuration from a TOML file."""

    def __init__(self, settings_cls: type, config_file: Path = Path("config.toml")) -> None:
        """Initialize TOML config source.

        Parameters
        ----------
        settings_cls : type
            The settings class to load config for
        config_file : Path, optional
            Path to TOML config file, by default Path("config.toml")

        """
        super().__init__(settings_cls)
        self.config_file = config_file
        self._data: dict[str, Any] = {}

        if self.config_file.exists():
            try:
                with self.config_file.open("rb") as f:
                    self._data = tomllib.load(f)
            except (OSError, tomllib.TOMLDecodeError) as e:
                # Log error but don't fail - graceful degradation

                warnings.warn(f"Failed to load TOML config from {self.config_file}: {e}", stacklevel=2)

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        """Get field value from TOML data.

        Parameters
        ----------
        field : FieldInfo
            The field info
        field_name : str
            The field name

        Returns
        -------
        tuple[Any, str, bool]
            Tuple of (value, field_name, value_is_complex)

        """
        # Handle nested fields with double underscore delimiter
        value = self._data
        for key in field_name.split("__"):
            if isinstance(value, dict) and key.lower() in value:
                value = value[key.lower()]  # type: ignore[assignment]
            else:
                return None, field_name, False

        return value, field_name, False  # type: ignore[return-value]

    def __call__(self) -> dict[str, Any]:
        """Return all loaded config data.

        Returns
        -------
        dict[str, Any]
            Configuration data from TOML file

        """
        return self._flatten_nested_dict(self._data)

    @staticmethod
    def _flatten_nested_dict(d: dict[str, Any], parent_key: str = "") -> dict[str, Any]:
        """Flatten nested dict with double underscore delimiter.

        Parameters
        ----------
        d : dict[str, Any]
            Dictionary to flatten
        parent_key : str, optional
            Parent key prefix, by default ""

        Returns
        -------
        dict[str, Any]
            Flattened dictionary

        """
        items: list[tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}__{k}".upper() if parent_key else k.upper()
            if isinstance(v, dict):
                items.extend(TomlConfigSource._flatten_nested_dict(v, new_key).items())  # type: ignore[arg-type]
            else:
                items.append((new_key, v))
        return dict(items)


class YamlConfigSource(PydanticBaseSettingsSource):
    """Load configuration from a YAML file."""

    def __init__(self, settings_cls: type, config_file: Path = Path("config.yaml")) -> None:
        """Initialize YAML config source.

        Parameters
        ----------
        settings_cls : type
            The settings class to load config for
        config_file : Path, optional
            Path to YAML config file, by default Path("config.yaml")

        """
        super().__init__(settings_cls)
        self.config_file = config_file
        self._data: dict[str, Any] = {}

        if self.config_file.exists():
            try:
                with self.config_file.open() as f:
                    self._data = yaml.safe_load(f) or {}
            except (OSError, yaml.YAMLError) as e:
                # Log error but don't fail - graceful degradation

                warnings.warn(f"Failed to load YAML config from {self.config_file}: {e}", stacklevel=2)

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        """Get field value from YAML data.

        Parameters
        ----------
        field : FieldInfo
            The field info
        field_name : str
            The field name

        Returns
        -------
        tuple[Any, str, bool]
            Tuple of (value, field_name, value_is_complex)

        """
        # Handle nested fields with double underscore delimiter
        value = self._data
        for key in field_name.split("__"):
            if isinstance(value, dict) and key.lower() in value:
                value = value[key.lower()]  # type: ignore[assignment]
            else:
                return None, field_name, False

        return value, field_name, False  # type: ignore[return-value]

    def __call__(self) -> dict[str, Any]:
        """Return all loaded config data.

        Returns
        -------
        dict[str, Any]
            Configuration data from YAML file

        """
        return self._flatten_nested_dict(self._data)

    @staticmethod
    def _flatten_nested_dict(d: dict[str, Any], parent_key: str = "") -> dict[str, Any]:
        """Flatten nested dict with double underscore delimiter.

        Parameters
        ----------
        d : dict[str, Any]
            Dictionary to flatten
        parent_key : str, optional
            Parent key prefix, by default ""

        Returns
        -------
        dict[str, Any]
            Flattened dictionary

        """
        items: list[tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}__{k}".upper() if parent_key else k.upper()
            if isinstance(v, dict):
                items.extend(YamlConfigSource._flatten_nested_dict(v, new_key).items())  # type: ignore[arg-type]
            else:
                items.append((new_key, v))
        return dict(items)


class JsonConfigSource(PydanticBaseSettingsSource):
    """Load configuration from a JSON file."""

    def __init__(self, settings_cls: type, config_file: Path = Path("config.json")) -> None:
        """Initialize JSON config source.

        Parameters
        ----------
        settings_cls : type
            The settings class to load config for
        config_file : Path, optional
            Path to JSON config file, by default Path("config.json")

        """
        super().__init__(settings_cls)
        self.config_file = config_file
        self._data: dict[str, Any] = {}

        if self.config_file.exists():
            try:
                with self.config_file.open() as f:
                    self._data = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                # Log error but don't fail - graceful degradation

                warnings.warn(f"Failed to load JSON config from {self.config_file}: {e}", stacklevel=2)

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        """Get field value from JSON data.

        Parameters
        ----------
        field : FieldInfo
            The field info
        field_name : str
            The field name

        Returns
        -------
        tuple[Any, str, bool]
            Tuple of (value, field_name, value_is_complex)

        """
        # Handle nested fields with double underscore delimiter
        value = self._data
        for key in field_name.split("__"):
            if isinstance(value, dict) and key.lower() in value:
                value = value[key.lower()]  # type: ignore[assignment]
            else:
                return None, field_name, False

        return value, field_name, False  # type: ignore[return-value]

    def __call__(self) -> dict[str, Any]:
        """Return all loaded config data.

        Returns
        -------
        dict[str, Any]
            Configuration data from JSON file

        """
        return self._flatten_nested_dict(self._data)

    @staticmethod
    def _flatten_nested_dict(d: dict[str, Any], parent_key: str = "") -> dict[str, Any]:
        """Flatten nested dict with double underscore delimiter.

        Parameters
        ----------
        d : dict[str, Any]
            Dictionary to flatten
        parent_key : str, optional
            Parent key prefix, by default ""

        Returns
        -------
        dict[str, Any]
            Flattened dictionary

        """
        items: list[tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}__{k}".upper() if parent_key else k.upper()
            if isinstance(v, dict):
                items.extend(JsonConfigSource._flatten_nested_dict(v, new_key).items())  # type: ignore[arg-type]
            else:
                items.append((new_key, v))
        return dict(items)
