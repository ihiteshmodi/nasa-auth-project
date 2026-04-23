from typing import Any

import httpx
from fastapi import HTTPException, status

from app.infrastructure.config import Settings


class NasaClient:
	def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
		self._settings = settings
		self._client = client

	def _resolve_api_key(self, api_key: str | None) -> str:
		resolved_api_key = api_key or self._settings.nasa_api_key
		if not resolved_api_key:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="NASA API key is required. Provide query param 'api_key' or set NASA_API_KEY.",
			)
		return resolved_api_key

	async def _get_json(self, url: str, params: dict[str, Any]) -> Any:
		try:
			response = await self._client.get(url, params=params, timeout=self._settings.http_timeout_seconds)
			response.raise_for_status()
			return response.json()
		except httpx.TimeoutException as exc:
			raise HTTPException(
				status_code=status.HTTP_504_GATEWAY_TIMEOUT,
				detail="Upstream NASA service timed out",
			) from exc
		except httpx.HTTPStatusError as exc:
			raise HTTPException(
				status_code=status.HTTP_502_BAD_GATEWAY,
				detail="Upstream NASA service returned an error",
			) from exc
		except httpx.HTTPError as exc:
			raise HTTPException(
				status_code=status.HTTP_502_BAD_GATEWAY,
				detail="Failed to reach upstream NASA service",
			) from exc

	async def get_donki_notifications(self, api_key: str | None = None) -> list[dict[str, Any]]:
		url = f"{self._settings.nasa_api_base_url}/DONKI/notifications"
		payload = await self._get_json(url, {"api_key": self._resolve_api_key(api_key)})
		if isinstance(payload, list):
			return payload
		return []

	async def get_eonet_events(self, api_key: str | None = None) -> dict[str, Any]:
		url = f"{self._settings.eonet_base_url}/events"
		payload = await self._get_json(url, {"api_key": self._resolve_api_key(api_key)})
		if isinstance(payload, dict):
			return payload
		return {"events": []}

	async def get_insight_weather(self, api_key: str | None = None) -> dict[str, Any]:
		url = f"{self._settings.nasa_api_base_url}/insight_weather/"
		payload = await self._get_json(
			url,
			{
				"api_key": self._resolve_api_key(api_key),
				"feedtype": "json",
				"ver": "1.0",
			},
		)
		if isinstance(payload, dict):
			return payload
		return {}
