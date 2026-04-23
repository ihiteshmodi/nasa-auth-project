from typing import Any

from app.infrastructure.nasa_client import NasaClient


class NasaService:
	def __init__(self, client: NasaClient) -> None:
		self._client = client

	async def fetch_donki_notifications(self, api_key: str | None = None) -> list[dict[str, Any]]:
		return await self._client.get_donki_notifications(api_key=api_key)

	async def fetch_eonet_events(self, api_key: str | None = None) -> dict[str, Any]:
		return await self._client.get_eonet_events(api_key=api_key)

	async def fetch_insight_weather(self, api_key: str | None = None) -> dict[str, Any]:
		return await self._client.get_insight_weather(api_key=api_key)
