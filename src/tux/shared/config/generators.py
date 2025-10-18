"""Custom generators for pydantic-settings-export.

This module provides custom generators for TOML, YAML, and JSON formats
that pydantic-settings-export doesn't include by default.

Note: Complexity warnings (PLR0911, PLR0912) are expected for parser functions
that need to handle multiple data types from configuration files.
"""

import ast
import json
import re
from pathlib import Path
from typing import Any

import tomli_w
import yaml
from pydantic import BaseModel, Field
from pydantic_settings_export.generators import AbstractGenerator  # type: ignore[import-untyped]
from pydantic_settings_export.models import FieldInfoModel, SettingsInfoModel  # type: ignore[import-untyped]


def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case.

    Parameters
    ----------
    name : str
        CamelCase string

    Returns
    -------
    str
        snake_case string

    """
    # Insert underscore before uppercase letters (except at start)
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Insert underscore before uppercase letters preceded by lowercase
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class TomlGeneratorSettings(BaseModel):
    """Configuration for TOML generator."""

    paths: list[Path] = Field(default_factory=list, description="Output file paths")
    include_comments: bool = Field(True, description="Include field descriptions as comments")


class TomlGenerator(AbstractGenerator):  # type: ignore[type-arg]
    """Generate TOML configuration files."""

    name = "toml"
    config = TomlGeneratorSettings  # type: ignore[assignment]

    def generate_single(self, settings_info: SettingsInfoModel, level: int = 1) -> str:  # noqa: PLR0912
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

        # Add header comment
        if settings_info.docs:
            lines.append(f"# {settings_info.docs}")
            lines.append("")

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

        # Add comments if enabled
        if self.generator_config.include_comments:  # type: ignore[attr-defined]
            result_lines: list[str] = []
            for line in toml_lines:
                # Check if this line starts with a field name
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
                result_lines.append(line)
            lines.extend(result_lines)
        else:
            lines.extend(toml_lines)

        return "\n".join(lines)

    def _format_value(self, field: FieldInfoModel) -> str:  # noqa: PLR0911
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

    def _parse_value(self, field: FieldInfoModel) -> Any:  # noqa: PLR0911, PLR0912
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


class YamlGeneratorSettings(BaseModel):
    """Configuration for YAML generator."""

    paths: list[Path] = Field(default_factory=list, description="Output file paths")
    include_comments: bool = Field(True, description="Include field descriptions as comments")


class YamlGenerator(AbstractGenerator):  # type: ignore[type-arg]
    """Generate YAML configuration files."""

    name = "yaml"
    config = YamlGeneratorSettings  # type: ignore[assignment]

    def generate_single(self, settings_info: SettingsInfoModel, level: int = 1) -> str:
        """Generate YAML format configuration.

        Parameters
        ----------
        settings_info : SettingsInfoModel
            Settings information model
        level : int, optional
            Nesting level, by default 1

        Returns
        -------
        str
            Generated YAML content

        """
        lines: list[str] = []

        # Add header comment
        if settings_info.docs:
            lines.append(f"# {settings_info.docs}")
            lines.append("")

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

        # Convert to YAML
        yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True)

        # Add comments if enabled
        if self.generator_config.include_comments:  # type: ignore[attr-defined]
            yaml_lines = yaml_str.split("\n")
            result_lines: list[str] = []

            for field in settings_info.fields:
                # Find the line with this field
                field_name = field.name.lower()
                for i, line in enumerate(yaml_lines):
                    if line and line.startswith(f"{field_name}:"):
                        if field.description:
                            result_lines.append(f"# {field.description}")
                        result_lines.append(line)
                        yaml_lines[i] = ""  # Mark as processed
                        break

            # Add any remaining lines (from nested structures)
            result_lines.extend(line for line in yaml_lines if line and line.strip())
            lines.extend(result_lines)
        else:
            lines.append(yaml_str)

        return "\n".join(lines)

    def _parse_value(self, field: FieldInfoModel) -> Any:  # noqa: PLR0911, PLR0912
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

        # Add schema info
        if settings_info.docs:
            config["$schema_description"] = settings_info.docs

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

    def _parse_value(self, field: FieldInfoModel) -> Any:  # noqa: PLR0911, PLR0912
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
