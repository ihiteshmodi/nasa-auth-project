from typing import Any
from datetime import UTC, date, datetime
from collections.abc import Awaitable, Callable
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.daily_api_cache import DailyApiCache


class NasaClientProtocol(Protocol):
	async def get_donki_notifications(self, api_key: str | None = None) -> list[dict[str, Any]]: ...

	async def get_eonet_events(self, api_key: str | None = None) -> dict[str, Any]: ...

	async def get_insight_weather(self, api_key: str | None = None) -> dict[str, Any]: ...

	async def get_asteroids_feed(self, api_key: str | None = None) -> dict[str, Any]: ...

	async def get_epic_images(self, api_key: str | None = None) -> list[dict[str, Any]]: ...


class NasaService:
	def __init__(
		self,
		client: NasaClientProtocol,
		db_session: Session,
		today_provider: Callable[[], date] | None = None,
	) -> None:
		self._client = client
		self._db_session = db_session
		self._today_provider = today_provider or (lambda: datetime.now(UTC).date())

	async def fetch_donki_notifications(self, api_key: str | None = None) -> list[dict[str, Any]]:
		return await self._client.get_donki_notifications(api_key=api_key)

	async def fetch_eonet_events(self, api_key: str | None = None) -> dict[str, Any]:
		return await self._client.get_eonet_events(api_key=api_key)

	async def fetch_insight_weather(self, api_key: str | None = None) -> dict[str, Any]:
		data, cached, cache_date = await self._fetch_with_daily_cache(
			endpoint="insight_weather",
			fetcher=lambda: self._client.get_insight_weather(api_key=api_key),
		)
		return {"data": data, "cached": cached, "cache_date": cache_date.isoformat()}

	async def fetch_asteroids_feed(self, api_key: str | None = None) -> dict[str, Any]:
		data, cached, cache_date = await self._fetch_with_daily_cache(
			endpoint="asteroids_neows",
			fetcher=lambda: self._client.get_asteroids_feed(api_key=api_key),
		)
		return {"data": data, "cached": cached, "cache_date": cache_date.isoformat()}

	async def fetch_epic_images(self, api_key: str | None = None) -> dict[str, Any]:
		data, cached, cache_date = await self._fetch_with_daily_cache(
			endpoint="epic_natural",
			fetcher=lambda: self._client.get_epic_images(api_key=api_key),
		)
		return {"data": data, "cached": cached, "cache_date": cache_date.isoformat()}

	async def _fetch_with_daily_cache(
		self,
		endpoint: str,
		fetcher: Callable[[], Awaitable[Any]],
	) -> tuple[Any, bool, date]:
		today = self._today_provider()
		existing = self._get_daily_cache(endpoint=endpoint, cache_date=today)
		if existing is not None:
			return existing.payload, True, today

		payload = await fetcher()
		persisted_payload, cached = self._store_daily_cache(
			endpoint=endpoint,
			cache_date=today,
			payload=payload,
		)
		return persisted_payload, cached, today

	def _get_daily_cache(self, endpoint: str, cache_date: date) -> DailyApiCache | None:
		return self._db_session.execute(
			select(DailyApiCache).where(
				DailyApiCache.endpoint == endpoint,
				DailyApiCache.cache_date == cache_date,
			)
		).scalar_one_or_none()

	def _store_daily_cache(self, endpoint: str, cache_date: date, payload: Any) -> tuple[Any, bool]:
		self._db_session.add(DailyApiCache(endpoint=endpoint, cache_date=cache_date, payload=payload))
		try:
			self._db_session.commit()
		except IntegrityError:
			self._db_session.rollback()
			existing_after_race = self._get_daily_cache(endpoint=endpoint, cache_date=cache_date)
			if existing_after_race is not None:
				return existing_after_race.payload, True
			raise

		return payload, False
