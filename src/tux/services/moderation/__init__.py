"""
Moderation services using composition over inheritance.

This module provides service-based implementations that replace the mixin-based
approach, eliminating type ignores while leveraging the existing DI container
and database controllers.

Services are automatically registered in the DI container via ServiceRegistry.
See ServiceRegistry._configure_moderation_services() for the implementation details.

Usage:
    # Services are automatically registered in ServiceRegistry
    # See ServiceRegistry._configure_moderation_services() for implementation

    # Manual registration (if needed):
    # Get dependencies from container
    db_service = container.get(DatabaseService)
    bot_service = container.get(IBotService)

    # Create service instances with dependencies
    case_service = CaseService(db_service.case)
    communication_service = CommunicationService(bot_service.bot)
    execution_service = ExecutionService()

    # Register instances in container
    container.register_instance(CaseService, case_service)
    container.register_instance(CommunicationService, communication_service)
    container.register_instance(ExecutionService, execution_service)
    container.register_instance(ModerationCoordinator, ModerationCoordinator(
        case_service=case_service,
        communication_service=communication_service,
        execution_service=execution_service,
    ))

    # Use in cog
    class BanCog(BaseCog):
        def __init__(self, bot: Tux):
            super().__init__(bot)
            self.moderation = self.container.get(ModerationCoordinator)

        @commands.command()
        async def ban(self, ctx, user: discord.Member, *, reason="No reason"):
            await self.moderation.execute_moderation_action(
                ctx, CaseType.BAN, user, reason
            )
"""

from .case_service import CaseService
from .communication_service import CommunicationService
from .execution_service import ExecutionService
from .moderation_coordinator import ModerationCoordinator

__all__ = [
    "CaseService",
    "CommunicationService",
    "ExecutionService",
    "ModerationCoordinator",
]
