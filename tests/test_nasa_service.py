import pytest

from app.application.nasa_service import NasaService


class FakeNasaClient:
    async def get_donki_notifications(self, api_key: str | None = None) -> list[dict[str, str]]:
        assert api_key == "query-key"
        return [{"kind": "donki"}]

    async def get_eonet_events(self, api_key: str | None = None) -> dict[str, list[dict[str, str]]]:
        assert api_key == "query-key"
        return {"events": [{"id": "EONET_1"}]}

    async def get_insight_weather(self, api_key: str | None = None) -> dict[str, list[str]]:
        assert api_key == "query-key"
        return {"sol_keys": ["1000"]}


@pytest.mark.anyio
async def test_nasa_service_forwards_all_calls() -> None:
    service = NasaService(client=FakeNasaClient())

    donki = await service.fetch_donki_notifications(api_key="query-key")
    eonet = await service.fetch_eonet_events(api_key="query-key")
    insight = await service.fetch_insight_weather(api_key="query-key")

    assert donki == [{"kind": "donki"}]
    assert eonet == {"events": [{"id": "EONET_1"}]}
    assert insight == {"sol_keys": ["1000"]}
