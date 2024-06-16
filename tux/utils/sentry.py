import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.loguru import LoguruIntegration

from tux.utils.constants import Constants as CONST


def setup_sentry():
    dsn = CONST.SENTRY_URL
    traces_sample_rate = 1.0
    profiles_sample_rate = 1.0
    enable_tracing = True
    environment = "dev" if CONST.DEV == "True" else "prod"

    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,
        enable_tracing=enable_tracing,
        integrations=[AsyncioIntegration(), LoguruIntegration()],
        environment=environment,
    )
