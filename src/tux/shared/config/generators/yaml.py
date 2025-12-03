"""YAML configuration file generator.

Generates YAML configuration files from Pydantic settings models.
"""

# ruff: noqa: PLR0911, PLR0912

import ast
import contextlib
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings_export.generators import (
    AbstractGenerator,  # type: ignore[import-untyped]
)
from pydantic_settings_export.models import (
    FieldInfoModel,
    SettingsInfoModel,
)

from .base import camel_to_snake


class YamlGeneratorSettings(BaseModel):
    """Configuration for YAML generator."""

    paths: list[Path] = Field(default_factory=list, description="Output file paths")
    include_comments: bool = Field(
        True,
        description="Include field descriptions as comments",
    )


class YamlGenerator(AbstractGenerator):  # type: ignore[type-arg]
    """Generate YAML configuration files."""

    name = "yaml"
    config = YamlGeneratorSettings

    def generate_single(self, settings_info: SettingsInfoModel, level: int = 1) -> str:
        # sourcery skip: low-code-quality, merge-list-extend, move-assign-in-block
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

        config: dict[str, Any] = {
            field.name.lower(): self._parse_value(field)
            for field in settings_info.fields
        }
        # Process child settings (nested models) as nested dicts
        # Convert CamelCase class names to snake_case keys
        for child in settings_info.child_settings:
            child_config: dict[str, Any] = {
                field.name.lower(): self._parse_value(field) for field in child.fields
            }
            # Convert class name (e.g. "ExternalServices") to snake_case (e.g. "external_services")
            section_name = camel_to_snake(child.name)
            config[section_name] = child_config

        # Convert to YAML
        yaml_str = yaml.dump(
            config,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

        # Comment out all values and add descriptions
        yaml_lines = yaml_str.split("\n")
        result_lines: list[str] = []

        for line in yaml_lines:
            if not line or not line.strip():
                # Keep empty lines
                result_lines.append(line)
            elif ":" in line:
                # Check if this is a section header (ends with : and no value after)
                stripped = line.strip()
                if not stripped.endswith(":") or stripped.startswith("-"):
                    # Value line - add description and comment out
                    field_name = line.split(":")[0].strip()

                    # Look for description
                    if self.generator_config.include_comments:  # type: ignore[attr-defined]
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

                # Section header - comment it out too for consistency
                result_lines.append(f"# {line}")
            else:
                result_lines.append(line)

        lines.extend(result_lines)

        return "\n".join(lines)

    def _parse_value(self, field: FieldInfoModel) -> Any:
        # sourcery skip: low-code-quality
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
            return 0 if field.types and "int" in field.types else ""
        value = field.default

        # If value is a string representation from pydantic, try to parse it
        if isinstance(value, str):  # type: ignore[reportUnnecessaryIsInstance]
            # Remove surrounding quotes if present (may need multiple passes)
            max_iterations = 5  # Safety limit
            iterations = 0
            while value and iterations < max_iterations:
                stripped = False
                if len(value) >= 2 and (
                    (value.startswith('"') and value.endswith('"'))
                    or (value.startswith("'") and value.endswith("'"))
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

            with contextlib.suppress(ValueError):
                # Only return as float if it has a decimal point
                if "." in value:
                    return float(value)
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
