"""Setup function for error handling system."""

from loguru import logger

from tux.core.bot import Tux

from .handler import ErrorHandler


async def setup(bot: Tux) -> None:
    """Standard setup function to add the ErrorHandler cog to the bot."""
    logger.debug("Setting up ErrorHandler")
    await bot.add_cog(ErrorHandler(bot))
    logger.debug("ErrorHandler setup complete")
