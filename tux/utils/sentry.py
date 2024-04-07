import sentry_sdk
from opentelemetry import trace
from opentelemetry.propagate import set_global_textmap  # type: ignore
from opentelemetry.sdk.trace import TracerProvider
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.loguru import LoguruIntegration
from sentry_sdk.integrations.opentelemetry import (
    SentryPropagator,  # type: ignore
    SentrySpanProcessor,  # type: ignore
)

from tux.utils.constants import Constants as CONST

provider = TracerProvider()
provider.add_span_processor(SentrySpanProcessor())
trace.set_tracer_provider(provider)
set_global_textmap(SentryPropagator())


def setup_sentry():
    dsn = CONST.SENTRY_URL
    traces_sample_rate = 1.0
    profiles_sample_rate = 1.0
    enable_tracing = True
    instrumenter = "otel"
    staging = CONST.STAGING == "True"
    environment = "staging" if staging else "production"

    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,
        enable_tracing=enable_tracing,
        instrumenter=instrumenter,
        integrations=[AioHttpIntegration(), AsyncioIntegration(), LoguruIntegration()],
        environment=environment,
    )
