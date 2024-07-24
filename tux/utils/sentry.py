import sentry_sdk
from discord.ext import commands
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.loguru import LoguruIntegration

from tux.utils.constants import Constants as CONST


def setup_sentry(bot: commands.Bot) -> None:
    """
    Sets up Sentry for error tracking and monitoring.
    """
    environment = "dev" if CONST.DEV == "True" else "prod"

    sentry_sdk.init(
        dsn=CONST.SENTRY_URL,
        environment=environment,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        enable_tracing=True,
        integrations=[AsyncioIntegration(), LoguruIntegration()],
    )

    # @bot.before_invoke
    # async def before_invoke(ctx: commands.Context[commands.Bot]):  # type: ignore

    # @bot.after_invoke
    # async def after_invoke(ctx: commands.Context[commands.Bot]):  # type: ignore
