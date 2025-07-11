from typing import Any, ClassVar

import discord
import sentry_sdk
from discord.ext import commands
from loguru import logger

from core.bot import Tux

# Type alias using PEP695 syntax
type CommandObject = (
    commands.Command[Any, ..., Any] | discord.app_commands.Command[Any, ..., Any] | discord.app_commands.ContextMenu
)


class SentryHandler(commands.Cog):
    """
    Handles Sentry transaction tracking for commands and interactions.

    This cog listens for Discord events to create and complete Sentry
    transactions, providing performance monitoring and error context
    for both prefix commands and slash commands.
    """

    # Standard Sentry transaction statuses with ClassVar
    # See: https://develop.sentry.dev/sdk/event-payloads/transaction/#transaction-status
    STATUS: ClassVar[dict[str, str]] = {
        "OK": "ok",
        "UNKNOWN": "unknown",
        "ERROR": "internal_error",
        "NOT_FOUND": "not_found",
        "PERMISSION_DENIED": "permission_denied",
        "INVALID_ARGUMENT": "invalid_argument",
        "RESOURCE_EXHAUSTED": "resource_exhausted",
        "UNAUTHENTICATED": "unauthenticated",
        "CANCELLED": "cancelled",
    }

    def __init__(self, bot: Tux) -> None:
        """Initialize the Sentry handler cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach the listeners to
        """
        self.bot = bot
        logger.info("Sentry handler initialized")

    def _is_sentry_available(self) -> bool:
        """Check if Sentry is initialized and available for use.

        Returns
        -------
        bool
            True if Sentry is initialized, False otherwise
        """
        return sentry_sdk.is_initialized()

    def _create_transaction(
        self,
        operation: str,
        name: str,
        description: str,
        tags: dict[str, Any],
    ) -> Any | None:
        """Create a Sentry transaction with the given parameters.

        Parameters
        ----------
        operation : str
            The operation type (e.g., "discord.command")
        name : str
            The name of the transaction
        description : str
            A description of the transaction
        tags : dict[str, Any]
            Tags to attach to the transaction

        Returns
        -------
        Optional[Any]
            The created transaction or None if Sentry is not initialized
        """
        if not self._is_sentry_available():
            return None

        try:
            transaction = sentry_sdk.start_transaction(op=operation, name=name, description=description)

            # Add all tags to the transaction
            for key, value in tags.items():
                transaction.set_tag(key, value)
        except Exception as e:
            logger.error(f"Error creating Sentry transaction: {e}")
            sentry_sdk.capture_exception(e)
            return None
        else:
            return transaction

    def _finish_transaction(self, object_id: int, status: str = STATUS["OK"]) -> None:
        """Finish a stored transaction with the given status.

        Parameters
        ----------
        object_id : int
            The ID of the interaction or message
        status : str
            The status to set on the transaction
        """
        if not self._is_sentry_available():
            return

        if transaction := self.bot.active_sentry_transactions.pop(object_id, None):
            transaction.set_status(status)
            transaction.finish()
            logger.trace(f"Finished Sentry transaction ({status}) for {transaction.name}")

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context[Tux]) -> None:
        """
        Start a Sentry transaction for a prefix command.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context
        """
        if not self._is_sentry_available():
            return

        if command_name := (ctx.command.qualified_name if ctx.command else "Unknown Command"):
            tags = {
                "discord.command.name": command_name,
                "discord.guild.id": str(ctx.guild.id) if ctx.guild else "DM",
                "discord.channel.id": ctx.channel.id,
                "discord.user.id": ctx.author.id,
                "discord.message.id": ctx.message.id,
                "discord.command.type": "prefix",
            }

            if transaction := self._create_transaction(
                operation="discord.command",
                name=command_name,
                description=ctx.message.content,
                tags=tags,
            ):
                self.bot.active_sentry_transactions[ctx.message.id] = transaction
                logger.trace(f"Started transaction for prefix command: {command_name}")

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context[Tux]) -> None:
        """
        Finish the Sentry transaction for a completed prefix command.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context
        """
        self._finish_transaction(ctx.message.id, self.STATUS["OK"])

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        """
        Start a Sentry transaction for application command interactions.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object
        """
        if not self._is_sentry_available() or interaction.type != discord.InteractionType.application_command:
            return

        if command_name := (interaction.command.qualified_name if interaction.command else "Unknown App Command"):
            tags = {
                "discord.command.name": command_name,
                "discord.guild.id": str(interaction.guild_id) if interaction.guild_id else "DM",
                "discord.channel.id": interaction.channel_id,
                "discord.user.id": interaction.user.id,
                "discord.interaction.id": interaction.id,
                "discord.interaction.type": interaction.type.name,
                "discord.command.type": "slash",
            }

            if transaction := self._create_transaction(
                operation="discord.app_command",
                name=command_name,
                description=f"/{command_name}",
                tags=tags,
            ):
                self.bot.active_sentry_transactions[interaction.id] = transaction
                logger.trace(f"Started transaction for app command: {command_name}")

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: CommandObject) -> None:
        """
        Finish the Sentry transaction for a completed application command.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object
        command : CommandObject
            The command that was completed
        """
        self._finish_transaction(interaction.id, self.STATUS["OK"])


async def setup(bot: Tux) -> None:
    """Add the SentryHandler cog to the bot."""
    await bot.add_cog(SentryHandler(bot))
