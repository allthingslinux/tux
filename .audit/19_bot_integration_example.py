"""Example of how to integrate the DI container into the Tux bot."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from tux.core.service_registry import ServiceRegistry

if TYPE_CHECKING:
    from tux.bot import Tux
    from tux.core.container import ServiceContainer


def integrate_dependency_injection(bot: Tux) -> ServiceContainer:
    """
    Integrate dependency injection into the bot.

    This function should be called during bot initialization,
    after the bot instance is created but before cogs are loaded.

    Parameters
    ----------
    bot : Tux
        The bot instance.

    Returns
    -------
    ServiceContainer
        The configured service container.
    """
    logger.info("Integrating dependency injection container...")

    try:
        # Configure the service container
        container = ServiceRegistry.configure_container(bot)

        # Attach container to bot for easy access
        bot.container = container

        logger.info("Dependency injection integration completed successfully")
        return container

    except Exception as e:
        logger.error(f"Failed to integrate dependency injection: {e}")
        raise


# Example of how to modify bot.py to use DI
"""
In tux/bot.py, add this to the setup method:

async def setup(self) -> None:
    try:
        with start_span("bot.setup", "Bot setup process") as span:
            span.set_tag("setup_phase", "starting")

            await self._setup_database()
            span.set_tag("setup_phase", "database_connected")

            # NEW: Initialize dependency injection
            from bot_integration_example import integrate_dependency_injection
            integrate_dependency_injection(self)
            span.set_tag("setup_phase", "di_initialized")

            await self._load_extensions()
            span.set_tag("setup_phase", "extensions_loaded")

            await self._load_cogs()
            span.set_tag("setup_phase", "cogs_loaded")

            await self._setup_hot_reload()
            span.set_tag("setup_phase", "hot_reload_ready")

            self._start_monitoring()
            span.set_tag("setup_phase", "monitoring_started")

    except Exception as e:
        logger.critical(f"Critical error during setup: {e}")
        # ... rest of error handling
"""

# Example of how to create a new cog using DI
"""
from tux.core.base_cog import BaseCog
from tux.core.interfaces import IDatabaseService, IEmbedService

class ExampleCog(BaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        # Services are automatically injected via BaseCog

    @commands.command()
    async def example_command(self, ctx: commands.Context) -> None:
        # Use injected services
        if self.db_service:
            # Database operations
            controller = self.db_service.get_controller()
            # ... use controller

        if self.embed_service:
            # Create embeds
            embed = self.embed_service.create_info_embed(
                title="Example",
                description="This uses dependency injection!"
            )
            await ctx.send(embed=embed)
"""

# Example of migrating an existing cog
"""
# BEFORE (old pattern):
class OldCog(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()  # Direct instantiation
        self.github = GithubService()   # Direct instantiation

# AFTER (DI pattern):
class NewCog(BaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        # Services are injected automatically

    @property
    def github(self):
        # Access external API service
        if hasattr(self, 'external_api_service'):
            return self.external_api_service.get_service()
        # Fallback for backward compatibility
        from tux.wrappers.github import GithubService
        return GithubService()
"""
