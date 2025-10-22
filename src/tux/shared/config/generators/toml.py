"""TOML configuration file generator.

Generates TOML configuration files from Pydantic settings models.
"""
# ruff: noqa: PLR0911, PLR0912

import ast
from pathlib import Path
from typing import Any

import tomli_w
from pydantic import BaseModel, Field
from pydantic_settings_export.generators import AbstractGenerator  # type: ignore[import-untyped]
from pydantic_settings_export.models import FieldInfoModel, SettingsInfoModel  # type: ignore[import-untyped]

from .base import camel_to_snake


class TomlGeneratorSettings(BaseModel):
    """Configuration for TOML generator."""

    paths: list[Path] = Field(default_factory=list, description="Output file paths")
    include_comments: bool = Field(True, description="Include field descriptions as comments")


class TomlGenerator(AbstractGenerator):  # type: ignore[type-arg]
    """Generate TOML configuration files."""

    name = "toml"
    config = TomlGeneratorSettings  # type: ignore[assignment]

    def generate_single(self, settings_info: SettingsInfoModel, level: int = 1) -> str:
        """Generate TOML format configuration.

        Parameters
        ----------
        settings_info : SettingsInfoModel
            Settings information model
        level : int, optional
            Nesting level, by default 1

        Returns
        -------
        str
            Generated TOML content

        """
        lines: list[str] = []

        # Build config dict
        config: dict[str, Any] = {}

        # Process each top-level (non-nested) field
        for field in settings_info.fields:
            field_value = self._parse_value(field)
            config[field.name.lower()] = field_value

        # Process child settings (nested models) as TOML sections
        # Convert CamelCase class names to snake_case section names
        for child in settings_info.child_settings:
            child_config: dict[str, Any] = {}
            for field in child.fields:
                child_config[field.name.lower()] = self._parse_value(field)
            # Convert class name (e.g. "ExternalServices") to snake_case (e.g. "external_services")
            section_name = camel_to_snake(child.name)
            config[section_name] = child_config

        # Convert dict to TOML
        toml_str = tomli_w.dumps(config)
        toml_lines = toml_str.split("\n")

        # Add comments if enabled and comment out values
        if self.generator_config.include_comments:  # type: ignore[attr-defined]
            result_lines: list[str] = []
            for line in toml_lines:
                # Check if this line starts with a field name (not a section header)
                if line and not line.startswith("[") and "=" in line:
                    field_name = line.split("=")[0].strip()
                    # Find matching field in main settings
                    for field in settings_info.fields:
                        if field.name.lower() == field_name:
                            if field.description:
                                result_lines.append(f"# {field.description}")
                            break
                    # Check in child settings
                    for child in settings_info.child_settings:
                        for field in child.fields:
                            if field.name.lower() == field_name:
                                if field.description:
                                    result_lines.append(f"# {field.description}")
                                break
                    # Comment out the value line
                    result_lines.append(f"# {line}")
                else:
                    # Keep section headers and empty lines
                    result_lines.append(line)
            lines.extend(result_lines)
        else:
            lines.extend(toml_lines)

        return "\n".join(lines)

    def _format_value(self, field: FieldInfoModel) -> str:
        """Format field value for TOML.

        Parameters
        ----------
        field : FieldInfoModel
            Field information

        Returns
        -------
        str
            Formatted value
        """
        if field.default:
            value = field.default
            # Handle string values
            if field.types and "str" in field.types:
                return f'"{value}"'
            # Handle boolean values
            if field.types and "bool" in field.types:
                return str(value).lower()
            # Handle numeric values
            if field.types and ("int" in field.types or "float" in field.types):
                return str(value)
            # Handle lists
            if hasattr(value, "startswith") and value.startswith("["):
                return value
            return f'"{value}"'

        # No default - use placeholder based on type
        if field.types:
            if "str" in field.types:
                return '""'
            if "bool" in field.types:
                return "false"
            if "int" in field.types:
                return "0"
            if "float" in field.types:
                return "0.0"
            if "list" in field.types[0].lower():
                return "[]"
            if "dict" in field.types[0].lower():
                return "{}"

        return '""'

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
