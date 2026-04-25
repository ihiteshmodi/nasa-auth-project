from types import SimpleNamespace

from fastapi import FastAPI

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


def test_configure_telemetry_returns_false_when_enabled_but_packages_unavailable(monkeypatch) -> None:
    app = FastAPI()
    monkeypatch.setattr(telemetry, "_load_opentelemetry_components", lambda: None)

    configured = telemetry.configure_telemetry(app, _settings(True))

    assert configured is False
    assert not hasattr(app.state, "opentelemetry_configured")
