from fastapi.testclient import TestClient

from app.application.nasa_service import NasaService
from app.infrastructure.config import settings
from app.interfaces.dependencies.nasa import get_nasa_service
from app.interfaces.main import create_app


class FakeNasaService(NasaService):
    def __init__(self) -> None:  # pragma: no cover
        pass

    async def fetch_donki_notifications(self, api_key: str | None = None) -> list[dict[str, str]]:
        return [{"messageType": "all"}]

    async def fetch_eonet_events(self, api_key: str | None = None) -> dict[str, list[dict[str, str]]]:
        return {"events": [{"id": "EONET_1"}]}

    async def fetch_insight_weather(self, api_key: str | None = None) -> dict[str, list[str]]:
        return {"sol_keys": ["1000"]}

    async def fetch_asteroids_feed(self, api_key: str | None = None) -> dict[str, object]:
        return {
            "data": {"near_earth_objects": {}},
            "cached": True,
            "cache_date": "2026-04-24",
        }

    async def fetch_epic_images(self, api_key: str | None = None) -> dict[str, object]:
        return {
            "data": [{"identifier": "epic-id"}],
            "cached": False,
            "cache_date": "2026-04-24",
        }


def test_health_endpoint() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_nasa_endpoints_return_nocache_payloads() -> None:
    app = create_app()
    app.dependency_overrides[get_nasa_service] = lambda: FakeNasaService()

    with TestClient(app) as client:
        donki_response = client.get("/api/v1/nasa/donki/notifications")
        eonet_response = client.get("/api/v1/nasa/eonet/events")
        insight_response = client.get("/api/v1/nasa/insight/weather")

    assert donki_response.status_code == 200
    assert donki_response.headers["Cache-Control"] == "no-store"
    assert donki_response.headers["X-Cache-Status"] == "BYPASS"
    assert donki_response.headers["X-Data-Source"] == "upstream"
    assert donki_response.json() == {
        "source": "DONKI",
        "nocache": True,
        "data": [{"messageType": "all"}],
    }

    assert eonet_response.status_code == 200
    assert eonet_response.headers["Cache-Control"] == "no-store"
    assert eonet_response.headers["X-Cache-Status"] == "BYPASS"
    assert eonet_response.headers["X-Data-Source"] == "upstream"
    assert eonet_response.json() == {
        "source": "EONET",
        "nocache": True,
        "data": {"events": [{"id": "EONET_1"}]},
    }

    assert insight_response.status_code == 200
    assert insight_response.headers["Cache-Control"] == "no-store"
    assert insight_response.headers["X-Cache-Status"] == "BYPASS"
    assert insight_response.headers["X-Data-Source"] == "upstream"
    assert insight_response.json() == {
        "source": "INSIGHT",
        "nocache": True,
        "data": {"sol_keys": ["1000"]},
    }


def test_nasa_cached_endpoints_return_cached_metadata() -> None:
    app = create_app()
    app.dependency_overrides[get_nasa_service] = lambda: FakeNasaService()

    with TestClient(app) as client:
        asteroids_response = client.get("/api/v1/nasa/asteroids/feed")
        epic_response = client.get("/api/v1/nasa/epic/natural")

    assert asteroids_response.status_code == 200
    assert asteroids_response.headers["X-Cache-Status"] == "HIT"
    assert asteroids_response.headers["X-Data-Source"] == "cache"
    assert asteroids_response.headers["X-Cache-Date"] == "2026-04-24"
    assert asteroids_response.json() == {
        "source": "ASTEROIDS_NEO_WS",
        "nocache": False,
        "cached": True,
        "cache_date": "2026-04-24",
        "data": {"near_earth_objects": {}},
    }

    assert epic_response.status_code == 200
    assert epic_response.headers["X-Cache-Status"] == "MISS"
    assert epic_response.headers["X-Data-Source"] == "upstream"
    assert epic_response.headers["X-Cache-Date"] == "2026-04-24"
    assert epic_response.json() == {
        "source": "EPIC_NATURAL",
        "nocache": False,
        "cached": False,
        "cache_date": "2026-04-24",
        "data": [{"identifier": "epic-id"}],
    }


def test_docs_request_requires_query_api_key() -> None:
    app = create_app()
    app.dependency_overrides[get_nasa_service] = lambda: FakeNasaService()

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/nasa/eonet/events",
            headers={"referer": "http://testserver/docs"},
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "query param 'api_key' is required."}


def test_docs_request_with_query_api_key_succeeds() -> None:
    app = create_app()
    app.dependency_overrides[get_nasa_service] = lambda: FakeNasaService()

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/nasa/eonet/events",
            params={"api_key": "from-docs"},
            headers={"referer": "http://testserver/docs"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "source": "EONET",
        "nocache": True,
        "data": {"events": [{"id": "EONET_1"}]},
    }


def test_nasa_api_returns_400_when_api_key_missing() -> None:
    app = create_app()
    original_key = settings.nasa_api_key
    settings.nasa_api_key = ""

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/nasa/eonet/events")
    finally:
        settings.nasa_api_key = original_key

    assert response.status_code == 400
    assert response.json() == {
        "detail": "NASA API key is required. Provide query param 'api_key' or set NASA_API_KEY."
    }
