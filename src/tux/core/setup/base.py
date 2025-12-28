"""Base setup service providing standardized patterns for bot initialization."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from loguru import logger

from tux.services.sentry import capture_exception_safe
from tux.services.sentry.tracing import start_span

if TYPE_CHECKING:
    from tux.core.bot import Tux

__all__ = ["BaseSetupService", "BotSetupService"]


class BaseSetupService(ABC):
    """Base class for all setup services with standardized patterns."""

    def __init__(self, name: str) -> None:
        """Initialize the base setup service.

        Parameters
        ----------
        name : str
            The name of the setup service for logging and tracing.
        """
        self.name = name

    @abstractmethod
    async def setup(self) -> None:
        """Execute the setup process. Must be implemented by subclasses."""

    async def safe_setup(self) -> bool:
        """Execute setup with standardized error handling and tracing.

        Wraps the setup process with Sentry tracing and error handling.
        Logs setup progress and captures exceptions for monitoring.

        Returns
        -------
        bool
            True if setup succeeded, False if it failed.
        """
        with start_span(f"bot.setup_{self.name}", f"Setting up {self.name}") as span:
            try:
                logger.info(f"Setting up {self.name}...")
                await self.setup()
                logger.success(f"{self.name.title()} setup completed")
                span.set_data("setup.status", "success")
            except KeyboardInterrupt:
                raise
            except Exception as e:
                # Database errors are already logged with context by DatabaseService
                if self.name != "database":
                    logger.exception(f"{self.name.title()} setup failed")

                span.set_data("setup.status", "failed")
                span.set_data("setup.error", str(e))
                span.set_data("setup.error_type", type(e).__name__)
                capture_exception_safe(e)
                return False
            else:
                return True


class BotSetupService(BaseSetupService):
    """Base class for setup services that need bot access."""

    def __init__(self, bot: Tux, name: str) -> None:
        """Initialize the bot setup service.

        Parameters
        ----------
        bot : Tux
            The Discord bot instance to set up.
        name : str
            The name of the setup service for logging and tracing.
        """
        super().__init__(name)
        self.bot = bot
