"""Shared utilities for configuration generators."""

import re


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
