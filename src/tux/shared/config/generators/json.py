"""JSON configuration file generator.

Generates JSON configuration files from Pydantic settings models.
"""
# ruff: noqa: PLR0911, PLR0912

import ast
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings_export.generators import AbstractGenerator  # type: ignore[import-untyped]
from pydantic_settings_export.models import FieldInfoModel, SettingsInfoModel  # type: ignore[import-untyped]

from .base import camel_to_snake


class JsonGeneratorSettings(BaseModel):
    """Configuration for JSON generator."""

    paths: list[Path] = Field(default_factory=list, description="Output file paths")
    indent: int = Field(2, description="JSON indentation spaces")


class JsonGenerator(AbstractGenerator):  # type: ignore[type-arg]
    """Generate JSON configuration files."""

    name = "json"
    config = JsonGeneratorSettings  # type: ignore[assignment]

    def generate_single(self, settings_info: SettingsInfoModel, level: int = 1) -> str:
        """Generate JSON format configuration.

        Parameters
        ----------
        settings_info : SettingsInfoModel
            Settings information model
        level : int, optional
            Nesting level, by default 1

        Returns
        -------
        str
            Generated JSON content

        """
        # Build config dict
        config: dict[str, Any] = {}

        # Process top-level (non-nested) fields
        for field in settings_info.fields:
            config[field.name.lower()] = self._parse_value(field)

        # Process child settings (nested models) as nested dicts
        # Convert CamelCase class names to snake_case keys
        for child in settings_info.child_settings:
            child_config: dict[str, Any] = {}
            for field in child.fields:
                child_config[field.name.lower()] = self._parse_value(field)
            # Convert class name (e.g. "ExternalServices") to snake_case (e.g. "external_services")
            section_name = camel_to_snake(child.name)
            config[section_name] = child_config

        # Convert to JSON with indentation
        return json.dumps(config, indent=self.generator_config.indent, ensure_ascii=False)  # type: ignore[attr-defined]

    def _parse_value(self, field: FieldInfoModel) -> Any:
        """Parse field value to appropriate Python type.

        Parameters
        ----------
        field : FieldInfoModel
            Field information

        Returns
        -------
        Any
            Parsed value

        """
        if not field.default:
            if field.types and "list" in field.types[0].lower():
                return []
            if field.types and "dict" in field.types[0].lower():
                return {}
            if field.types and "bool" in field.types:
                return False
            if field.types and "int" in field.types:
                return 0
            if field.types and ("NoneType" in field.types or "None" in field.types):
                return None
            return ""

        value = field.default

        # If value is a string representation from pydantic, try to parse it
        if isinstance(value, str):  # type: ignore[reportUnnecessaryIsInstance]
            # Remove surrounding quotes if present (may need multiple passes)
            max_iterations = 5  # Safety limit
            iterations = 0
            while value and iterations < max_iterations:
                stripped = False
                if len(value) >= 2 and (
                    (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'"))
                ):
                    value = value[1:-1]
                    stripped = True

                if not stripped:
                    break
                iterations += 1

            # Handle None
            if value == "None":
                return None

            # Handle boolean strings
            if value.lower() in ("true", "false"):
                return value.lower() == "true"

            # Handle numeric strings
            if value.isdigit():
                return int(value)

            try:
                # Try to parse as float
                float_val = float(value)
                # Only return as float if it has a decimal point
                if "." in value:
                    return float_val
            except ValueError:
                pass

            # Handle list/dict literals
            if value.startswith("[") and value.endswith("]"):
                try:
                    return ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    return []

            if value.startswith("{") and value.endswith("}"):
                try:
                    return ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    return {}

        return value
