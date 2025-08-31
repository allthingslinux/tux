"""
Configuration management for Tux.

This package provides configuration loading.
No environment concepts - just use DEBUG for conditional logic.
"""

from .settings import CONFIG

__all__ = [
    "CONFIG",
]
