import logging
from importlib import import_module
from typing import Any, Protocol

from fastapi import FastAPI

logger = logging.getLogger(__name__)


class TelemetrySettings(Protocol):
    app_env: str
    opentelemetry_tracing_enabled: bool
    opentelemetry_service_name: str
    opentelemetry_otlp_endpoint: str
    opentelemetry_otlp_insecure: bool

_HTTPX_INSTRUMENTED = False


def _load_opentelemetry_components() -> dict[str, Any] | None:
    try:
        return {
            "trace": import_module("opentelemetry.trace"),
            "Resource": import_module("opentelemetry.sdk.resources").Resource,
            "TracerProvider": import_module("opentelemetry.sdk.trace").TracerProvider,
            "BatchSpanProcessor": import_module("opentelemetry.sdk.trace.export").BatchSpanProcessor,
            "OTLPSpanExporter": import_module(
                "opentelemetry.exporter.otlp.proto.grpc.trace_exporter"
            ).OTLPSpanExporter,
            "FastAPIInstrumentor": import_module("opentelemetry.instrumentation.fastapi").FastAPIInstrumentor,
            "HTTPXClientInstrumentor": import_module("opentelemetry.instrumentation.httpx").HTTPXClientInstrumentor,
        }
    except Exception:
        return None


def configure_telemetry(app: FastAPI, settings: TelemetrySettings) -> bool:
    global _HTTPX_INSTRUMENTED

    if not settings.opentelemetry_tracing_enabled:
        logger.info("telemetry_disabled")
        return False

    if getattr(app.state, "opentelemetry_configured", False):
        return True

    components = _load_opentelemetry_components()
    if components is None:
        logger.warning("telemetry_unavailable", extra={"reason": "missing_opentelemetry_packages"})
        return False

    resource = components["Resource"].create(
        {
            "service.name": settings.opentelemetry_service_name,
            "deployment.environment": settings.app_env,
        }
    )
    provider = components["TracerProvider"](resource=resource)
    exporter = components["OTLPSpanExporter"](
        endpoint=settings.opentelemetry_otlp_endpoint,
        insecure=settings.opentelemetry_otlp_insecure,
    )
    provider.add_span_processor(components["BatchSpanProcessor"](exporter))
    components["trace"].set_tracer_provider(provider)

    components["FastAPIInstrumentor"].instrument_app(app)
    if not _HTTPX_INSTRUMENTED:
        components["HTTPXClientInstrumentor"]().instrument()
        _HTTPX_INSTRUMENTED = True

    app.state.opentelemetry_configured = True
    logger.info(
        "telemetry_enabled",
        extra={
            "otlp_endpoint": settings.opentelemetry_otlp_endpoint,
            "service_name": settings.opentelemetry_service_name,
            "environment": settings.app_env,
        },
    )
    return True
