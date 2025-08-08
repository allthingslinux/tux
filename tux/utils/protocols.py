"""
Defines structural type hints (Protocols) for dependency injection.

This module contains Protocol classes that define the structure of objects
required by different parts of the application. By using these protocols
for type hinting instead of concrete classes (like `Tux`), we can achieve
loose coupling between components.

This approach, known as structural subtyping or static duck typing, allows
any object that has the required attributes and methods to be used,
breaking circular import dependencies and making the codebase more modular
and easier to test.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import ModuleType
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from discord.ext import commands

    from tux.services.sentry_manager import SentryManager


@runtime_checkable
class BotProtocol(Protocol):
    """A protocol for the bot instance to provide necessary attributes."""

    @property
    def cogs(self) -> Mapping[str, commands.Cog]: ...

    @property
    def extensions(self) -> Mapping[str, ModuleType]: ...

    help_command: Any

    sentry_manager: SentryManager

    async def load_extension(self, name: str) -> None: ...
    async def reload_extension(self, name: str) -> None: ...
    async def add_cog(self, cog: commands.Cog, /, *, override: bool = False) -> None: ...
