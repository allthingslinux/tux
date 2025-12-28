"""Hot reload cog for file watching and automatic reloading."""

from loguru import logger

from tux.core.bot import Tux
from tux.services.hot_reload.service import HotReload


async def setup(bot: Tux) -> None:
    """Cog setup for hot reload.

    Parameters
    ----------
    bot : Tux
        The bot instance.
    """
    await bot.add_cog(HotReload(bot))
    logger.trace("Hot reload cog loaded")
