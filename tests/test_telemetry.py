from types import SimpleNamespace

from fastapi import FastAPI

from app.infrastructure.config import Settings
from app.infrastructure import telemetry


def _settings(enabled: bool) -> SimpleNamespace:
    return SimpleNamespace(
        app_env="test",
        opentelemetry_tracing_enabled=enabled,
        opentelemetry_service_name="nasa-auth-project-test",
        opentelemetry_otlp_endpoint="http://localhost:4317",
        opentelemetry_otlp_insecure=True,
    )


def test_configure_telemetry_returns_false_when_disabled() -> None:
    app = FastAPI()

    configured = telemetry.configure_telemetry(app, _settings(False))

    assert configured is False
    assert not hasattr(app.state, "opentelemetry_configured")


def test_configure_telemetry_disabled_does_not_attempt_component_loading(monkeypatch) -> None:
    app = FastAPI()
    called = {"value": False}

    def _loader():
        called["value"] = True
        return {}

    monkeypatch.setattr(telemetry, "_load_opentelemetry_components", _loader)

    configured = telemetry.configure_telemetry(app, _settings(False))

    assert configured is False
    assert called["value"] is False


def test_configure_telemetry_returns_false_when_enabled_but_packages_unavailable(monkeypatch) -> None:
    app = FastAPI()
    monkeypatch.setattr(telemetry, "_load_opentelemetry_components", lambda: None)

    configured = telemetry.configure_telemetry(app, _settings(True))

    assert configured is False
    assert not hasattr(app.state, "opentelemetry_configured")


def test_configure_telemetry_returns_true_when_already_configured_even_if_loader_missing(monkeypatch) -> None:
    app = FastAPI()
    app.state.opentelemetry_configured = True
    monkeypatch.setattr(telemetry, "_load_opentelemetry_components", lambda: None)

    configured = telemetry.configure_telemetry(app, _settings(True))

    assert configured is True


def test_settings_parse_opentelemetry_booleans_from_env(monkeypatch) -> None:
    monkeypatch.setenv("OPENTELEMETRY_TRACING", "YES")
    monkeypatch.setenv("OPENTELEMETRY_OTLP_INSECURE", "off")

    parsed = Settings()

    assert parsed.opentelemetry_tracing_enabled is True
    assert parsed.opentelemetry_otlp_insecure is False


def test_configure_telemetry_enabled_configures_components(monkeypatch) -> None:
    app = FastAPI()
    state: dict[str, object] = {}

    class FakeResource:
        @staticmethod
        def create(attrs):
            state["resource_attrs"] = attrs
            return attrs

    class FakeTracerProvider:
        def __init__(self, resource):
            state["provider_resource"] = resource

        def add_span_processor(self, processor):
            state["span_processor"] = processor

    class FakeBatchSpanProcessor:
        def __init__(self, exporter):
            state["batch_exporter"] = exporter

    class FakeOTLPSpanExporter:
        def __init__(self, *, endpoint, insecure):
            state["otlp_endpoint"] = endpoint
            state["otlp_insecure"] = insecure

    class FakeTraceModule:
        @staticmethod
        def set_tracer_provider(provider):
            state["trace_provider_set"] = provider

    class FakeFastAPIInstrumentor:
        @staticmethod
        def instrument_app(_app):
            state["fastapi_instrumented"] = _app

    class FakeHTTPXClientInstrumentor:
        def instrument(self):
            state["httpx_instrumented"] = True

    monkeypatch.setattr(
        telemetry,
        "_load_opentelemetry_components",
        lambda: {
            "trace": FakeTraceModule,
            "Resource": FakeResource,
            "TracerProvider": FakeTracerProvider,
            "BatchSpanProcessor": FakeBatchSpanProcessor,
            "OTLPSpanExporter": FakeOTLPSpanExporter,
            "FastAPIInstrumentor": FakeFastAPIInstrumentor,
            "HTTPXClientInstrumentor": FakeHTTPXClientInstrumentor,
        },
    )
    monkeypatch.setattr(telemetry, "_HTTPX_INSTRUMENTED", False)

    configured = telemetry.configure_telemetry(app, _settings(True))

    assert configured is True
    assert app.state.opentelemetry_configured is True
    assert state["otlp_endpoint"] == "http://localhost:4317"
    assert state["otlp_insecure"] is True
    assert state["resource_attrs"] == {
        "service.name": "nasa-auth-project-test",
        "deployment.environment": "test",
    }
    assert state["fastapi_instrumented"] is app
    assert state["httpx_instrumented"] is True
