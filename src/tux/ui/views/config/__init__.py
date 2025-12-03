"""
Tux Configuration UI Package.

A modular, extensible configuration interface system using Discord Components V2.
Provides a clean foundation for building configuration UIs with proper separation
of concerns, reusable components, and type-safe interactions.
"""

from .dashboard import ConfigDashboard

__all__ = [
    "ConfigDashboard",
]
