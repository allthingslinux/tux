"""
CLI Infrastructure Package.

This package provides a clean, object-oriented foundation for building CLI applications
with proper separation of concerns and extensibility.
"""

from scripts.base import BaseCLI
from scripts.config import ConfigCLI
from scripts.db import DatabaseCLI
from scripts.dev import DevCLI
from scripts.docker_cli import DockerCLI
from scripts.docs import DocsCLI
from scripts.registry import Command, CommandGroup, CommandRegistry
from scripts.rich_utils import RichCLI
from scripts.rules import RulesCLI
from scripts.test import TestCLI
from scripts.tux import TuxCLI

__all__ = [
    "BaseCLI",
    "Command",
    "CommandGroup",
    "CommandRegistry",
    "ConfigCLI",
    "RulesCLI",
    "DatabaseCLI",
    "DevCLI",
    "DockerCLI",
    "DocsCLI",
    "RichCLI",
    "TestCLI",
    "TuxCLI",
]
