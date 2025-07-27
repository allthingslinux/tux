"""Base cog classes with dependency injection support."""

from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from tux.core.interfaces import (
    IConfigurationService,
    IDatabaseService,
    IEmbedService,
    ILoggingService,
    IServiceContainer,
)

if TYPE_CHECKING:
    from tux.bot import Tux


class BaseCog(commands.Cog):
    """Base cog class with dependency injection support."""

    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self._container: IServiceContainer | None = getattr(bot, "container", None)

        # Initialize services if container is available
        if self._container:
            self._init_services()
        else:
            # Fallback to direct instantiation for backward compatibility
            self._init_fallback_services()

    def _init_services(self) -> None:
        """Initialize services using dependency injection."""
        if not self._container:
            return

        self.db_service = self._container.get_optional(IDatabaseService)
        self.config_service = self._container.get_optional(IConfigurationService)
        self.embed_service = self._container.get_optional(IEmbedService)
        self.logging_service = self._container.get_optional(ILoggingService)

    def _init_fallback_services(self) -> None:
        """Initialize services using direct instantiation (fallback)."""
        # Import here to avoid circular imports
        from tux.core.services import (
            ConfigurationService,
            DatabaseService,
            EmbedService,
            LoggingService,
        )

        self.db_service = DatabaseService()
        self.config_service = ConfigurationService()
        self.embed_service = EmbedService(self.bot)
        self.logging_service = LoggingService()

    @property
    def db(self) -> IDatabaseService:
        """Get database service (backward compatibility)."""
        if hasattr(self, "db_service") and self.db_service:
            return self.db_service.get_controller()

        # Fallback for backward compatibility
        from tux.database.controllers import DatabaseController

        return DatabaseController()


class ModerationBaseCog(BaseCog):
    """Base class for moderation cogs with common functionality."""

    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)

    async def log_moderation_action(
        self,
        action: str,
        user_id: int,
        moderator_id: int,
        reason: str | None = None,
    ) -> None:
        """Log a moderation action."""
        if self.logging_service:
            self.logging_service.log_info(
                f"Moderation action: {action}",
                user_id=user_id,
                moderator_id=moderator_id,
                reason=reason,
            )


class UtilityBaseCog(BaseCog):
    """Base class for utility cogs with common functionality."""

    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)

    def create_info_embed(self, title: str, description: str, **kwargs) -> None:
        """Create an info embed using the embed service."""
        if self.embed_service:
            return self.embed_service.create_info_embed(title, description, **kwargs)

        # Fallback
        from tux.ui.embeds import EmbedCreator, EmbedType

        return EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedType.INFO,
            title=title,
            description=description,
            **kwargs,
        )
