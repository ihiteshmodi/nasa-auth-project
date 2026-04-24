import httpx
import pytest
from fastapi import HTTPException

from app.infrastructure.config import Settings
from app.infrastructure.nasa_client import NasaClient


@pytest.mark.anyio
async def test_get_donki_notifications_success() -> None:
    settings = Settings(nasa_api_key="test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/DONKI/notifications"
        assert request.url.params["api_key"] == "test-key"
        return httpx.Response(status_code=200, json=[{"messageType": "all"}], request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = NasaClient(settings=settings, client=http_client)
        payload = await client.get_donki_notifications()

    assert payload == [{"messageType": "all"}]


@pytest.mark.anyio
async def test_get_eonet_events_success() -> None:
    settings = Settings(nasa_api_key="test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v3/events"
        return httpx.Response(status_code=200, json={"events": [{"id": "EONET_1"}]}, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = NasaClient(settings=settings, client=http_client)
        payload = await client.get_eonet_events()

    assert payload["events"][0]["id"] == "EONET_1"


@pytest.mark.anyio
async def test_get_insight_weather_success() -> None:
    settings = Settings(nasa_api_key="test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/insight_weather/"
        assert request.url.params["feedtype"] == "json"
        assert request.url.params["ver"] == "1.0"
        return httpx.Response(status_code=200, json={"sol_keys": ["1000"]}, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = NasaClient(settings=settings, client=http_client)
        payload = await client.get_insight_weather()

    assert payload["sol_keys"] == ["1000"]


@pytest.mark.anyio
async def test_timeout_is_translated_to_504() -> None:
    settings = Settings(nasa_api_key="test-key")

    async with httpx.AsyncClient() as http_client:
        client = NasaClient(settings=settings, client=http_client)

        async def raise_timeout(*args, **kwargs):
            raise httpx.TimeoutException("timeout")

        http_client.get = raise_timeout  # type: ignore[method-assign]

        with pytest.raises(HTTPException) as exc_info:
            await client.get_donki_notifications()

    assert exc_info.value.status_code == 504
    assert exc_info.value.detail == "Upstream NASA service timed out"


@pytest.mark.anyio
async def test_http_status_error_is_translated_to_502() -> None:
    settings = Settings(nasa_api_key="test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=500, json={"error": "upstream"}, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = NasaClient(settings=settings, client=http_client)

        with pytest.raises(HTTPException) as exc_info:
            await client.get_eonet_events()

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "Upstream NASA service returned an error"


@pytest.mark.anyio
async def test_missing_api_key_returns_400() -> None:
    settings = Settings(nasa_api_key="")

    async with httpx.AsyncClient() as http_client:
        client = NasaClient(settings=settings, client=http_client)

        with pytest.raises(HTTPException) as exc_info:
            await client.get_donki_notifications()

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "NASA API key is required. Provide query param 'api_key' or set NASA_API_KEY."


@pytest.mark.anyio
async def test_get_asteroids_feed_success() -> None:
    settings = Settings(nasa_api_key="test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/neo/rest/v1/feed"
        assert request.url.params["api_key"] == "test-key"
        return httpx.Response(status_code=200, json={"near_earth_objects": {}}, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = NasaClient(settings=settings, client=http_client)
        payload = await client.get_asteroids_feed()

    assert payload == {"near_earth_objects": {}}


@pytest.mark.anyio
async def test_get_epic_images_success() -> None:
    settings = Settings(nasa_api_key="test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/EPIC/api/natural"
        return httpx.Response(status_code=200, json=[{"identifier": "epic-id"}], request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = NasaClient(settings=settings, client=http_client)
        payload = await client.get_epic_images()

    assert payload == [{"identifier": "epic-id"}]


@pytest.mark.anyio
async def test_retries_timeout_then_succeeds() -> None:
    settings = Settings(
        nasa_api_key="test-key",
        http_retry_attempts=3,
        http_retry_backoff_seconds=0.0,
    )
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            raise httpx.TimeoutException("timeout")
        return httpx.Response(status_code=200, json={"events": [{"id": "ok"}]}, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = NasaClient(settings=settings, client=http_client)
        payload = await client.get_eonet_events()

    assert calls["count"] == 2
    assert payload == {"events": [{"id": "ok"}]}


@pytest.mark.anyio
async def test_retries_503_then_succeeds() -> None:
    settings = Settings(
        nasa_api_key="test-key",
        http_retry_attempts=3,
        http_retry_backoff_seconds=0.0,
    )
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(status_code=503, json={"error": "temp"}, request=request)
        return httpx.Response(status_code=200, json={"events": [{"id": "ok"}]}, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = NasaClient(settings=settings, client=http_client)
        payload = await client.get_eonet_events()

    assert calls["count"] == 2
    assert payload == {"events": [{"id": "ok"}]}


@pytest.mark.anyio
async def test_does_not_retry_on_404() -> None:
    settings = Settings(
        nasa_api_key="test-key",
        http_retry_attempts=3,
        http_retry_backoff_seconds=0.0,
    )
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(status_code=404, json={"error": "not found"}, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = NasaClient(settings=settings, client=http_client)
        with pytest.raises(HTTPException) as exc_info:
            await client.get_eonet_events()

    assert calls["count"] == 1
    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "Upstream NASA service returned an error"
