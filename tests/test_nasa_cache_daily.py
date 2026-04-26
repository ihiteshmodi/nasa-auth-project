from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.application.nasa_service import NasaService
from app.infrastructure.db import Base


class CountingClient:
    def __init__(self) -> None:
        self.asteroids_calls = 0
        self.epic_calls = 0
        self.weather_calls = 0

    async def get_donki_notifications(self, api_key: str | None = None) -> list[dict[str, str]]:
        return [{"kind": "unused"}]

    async def get_eonet_events(self, api_key: str | None = None) -> dict[str, list[dict[str, str]]]:
        return {"events": [{"id": "unused"}]}

    async def get_asteroids_feed(self, api_key: str | None = None) -> dict[str, dict]:
        self.asteroids_calls += 1
        return {"near_earth_objects": {"count": self.asteroids_calls}}

    async def get_epic_images(self, api_key: str | None = None) -> list[dict[str, int]]:
        self.epic_calls += 1
        return [{"sequence": self.epic_calls}]

    async def get_insight_weather(self, api_key: str | None = None) -> dict[str, list[str]]:
        self.weather_calls += 1
        return {"sol_keys": [str(self.weather_calls)]}


def _build_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return Session()


@pytest.mark.anyio
async def test_daily_cache_hits_once_per_day() -> None:
    session = _build_session()
    client = CountingClient()
    service = NasaService(client=client, db_session=session, today_provider=lambda: date(2026, 4, 24))

    first = await service.fetch_asteroids_feed(api_key="k")
    second = await service.fetch_asteroids_feed(api_key="k")

    assert first["cached"] is False
    assert second["cached"] is True
    assert first["data"] == {"near_earth_objects": {"count": 1}}
    assert second["data"] == {"near_earth_objects": {"count": 1}}
    assert client.asteroids_calls == 1


@pytest.mark.anyio
async def test_daily_cache_refreshes_when_day_changes() -> None:
    session = _build_session()
    client = CountingClient()
    state = {"day": date(2026, 4, 24)}

    def today_provider() -> date:
        return state["day"]

    service = NasaService(client=client, db_session=session, today_provider=today_provider)

    day1 = await service.fetch_epic_images(api_key="k")
    state["day"] = date(2026, 4, 25)
    day2 = await service.fetch_epic_images(api_key="k")

    assert day1["cached"] is False
    assert day2["cached"] is False
    assert day1["cache_date"] == "2026-04-24"
    assert day2["cache_date"] == "2026-04-25"
    assert client.epic_calls == 2


@pytest.mark.anyio
async def test_weather_daily_cache_hits_once_per_day() -> None:
    session = _build_session()
    client = CountingClient()
    service = NasaService(client=client, db_session=session, today_provider=lambda: date(2026, 4, 24))

    first = await service.fetch_insight_weather(api_key="k")
    second = await service.fetch_insight_weather(api_key="k")

    assert first["cached"] is False
    assert second["cached"] is True
    assert first["data"] == {"sol_keys": ["1"]}
    assert second["data"] == {"sol_keys": ["1"]}
    assert client.weather_calls == 1
