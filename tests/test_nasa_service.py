import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.application.nasa_service import NasaService
from app.infrastructure.db import Base


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

    async def get_asteroids_feed(self, api_key: str | None = None) -> dict[str, dict]:
        assert api_key == "query-key"
        return {"near_earth_objects": {}}

    async def get_epic_images(self, api_key: str | None = None) -> list[dict[str, str]]:
        assert api_key == "query-key"
        return [{"identifier": "epic-id"}]


def _build_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return Session()


@pytest.mark.anyio
async def test_nasa_service_forwards_all_calls() -> None:
    session = _build_session()
    service = NasaService(client=FakeNasaClient(), db_session=session)

    donki = await service.fetch_donki_notifications(api_key="query-key")
    eonet = await service.fetch_eonet_events(api_key="query-key")
    insight = await service.fetch_insight_weather(api_key="query-key")
    asteroids = await service.fetch_asteroids_feed(api_key="query-key")
    epic = await service.fetch_epic_images(api_key="query-key")

    assert donki == [{"kind": "donki"}]
    assert eonet == {"events": [{"id": "EONET_1"}]}
    assert insight["data"] == {"sol_keys": ["1000"]}
    assert insight["cached"] is False
    assert asteroids["data"] == {"near_earth_objects": {}}
    assert epic["data"] == [{"identifier": "epic-id"}]
