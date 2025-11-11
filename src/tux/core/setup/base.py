"""Base setup service providing standardized patterns for bot initialization."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from loguru import logger

from tux.services.sentry import capture_exception_safe
from tux.services.sentry.tracing import start_span

if TYPE_CHECKING:
    from tux.core.bot import Tux


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
        self.logger = logger.bind(service=name)

    @abstractmethod
    async def setup(self) -> None:
        """Execute the setup process. Must be implemented by subclasses."""

    async def safe_setup(self) -> bool:
        """Execute setup with standardized error handling and tracing.

        Returns
        -------
            True if setup succeeded, False if it failed
        """
        with start_span(f"bot.setup_{self.name}", f"Setting up {self.name}") as span:
            try:
                self.logger.info(f"🔧 Setting up {self.name}...")
                await self.setup()
                self.logger.info(f"✅ {self.name.title()} setup completed")
                span.set_tag(f"{self.name}.setup", "success")
            except KeyboardInterrupt:
                # Re-raise KeyboardInterrupt to allow signal handling
                self.logger.info(f"{self.name.title()} setup interrupted by user signal")
                raise
            except Exception as e:
                # Only log if error wasn't already logged by the service
                # Database errors are already logged by database service
                if self.name != "database":
                    # Use error() instead of exception() to avoid duplicate tracebacks
                    # Sentry already captures full exception details
                    self.logger.error(f"❌ {self.name.title()} setup failed: {e}")  # noqa: TRY400
                span.set_tag(f"{self.name}.setup", "failed")
                span.set_data("error", str(e))
                capture_exception_safe(e)
                return False
            else:
                return True

    def _log_step(self, step: str, status: str = "info") -> None:
        """Log a setup step with consistent formatting."""
        emoji = {"info": "🔧", "success": "✅", "warning": "⚠️", "error": "❌"}
        getattr(self.logger, status)(f"{emoji.get(status, '🔧')} {step}")


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
