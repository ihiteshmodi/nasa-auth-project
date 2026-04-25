from typing import Any
import asyncio
import logging
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, status

from app.infrastructure.config import Settings

logger = logging.getLogger(__name__)


class NasaClient:
	RETRIABLE_STATUS_CODES = {429, 500, 502, 503, 504}

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

	async def _sleep_before_retry(self, attempt: int) -> None:
		backoff_seconds = self._settings.http_retry_backoff_seconds * (2 ** (attempt - 1))
		await asyncio.sleep(backoff_seconds)

	async def _get_json(self, url: str, params: dict[str, Any]) -> Any:
		attempts = max(1, self._settings.http_retry_attempts)
		endpoint = urlparse(url).path
		for attempt in range(1, attempts + 1):
			try:
				response = await self._client.get(url, params=params, timeout=self._settings.http_timeout_seconds)
				response.raise_for_status()
				return response.json()
			except httpx.TimeoutException as exc:
				if attempt < attempts:
					logger.warning(
						"retry_scheduled",
						extra={
							"endpoint": endpoint,
							"reason": "timeout",
							"attempt": attempt,
							"max_attempts": attempts,
						},
					)
					await self._sleep_before_retry(attempt)
					continue
				logger.error(
					"upstream_failure",
					extra={
						"endpoint": endpoint,
						"reason": "timeout",
						"attempt": attempt,
						"max_attempts": attempts,
					},
				)
				raise HTTPException(
					status_code=status.HTTP_504_GATEWAY_TIMEOUT,
					detail="Upstream NASA service timed out",
				) from exc
			except httpx.HTTPStatusError as exc:
				if exc.response.status_code in self.RETRIABLE_STATUS_CODES and attempt < attempts:
					logger.warning(
						"retry_scheduled",
						extra={
							"endpoint": endpoint,
							"reason": "http_status",
							"status_code": exc.response.status_code,
							"attempt": attempt,
							"max_attempts": attempts,
						},
					)
					await self._sleep_before_retry(attempt)
					continue
				logger.error(
					"upstream_failure",
					extra={
						"endpoint": endpoint,
						"reason": "http_status",
						"status_code": exc.response.status_code,
						"attempt": attempt,
						"max_attempts": attempts,
					},
				)
				raise HTTPException(
					status_code=status.HTTP_502_BAD_GATEWAY,
					detail="Upstream NASA service returned an error",
				) from exc
			except httpx.TransportError as exc:
				if attempt < attempts:
					logger.warning(
						"retry_scheduled",
						extra={
							"endpoint": endpoint,
							"reason": "transport_error",
							"attempt": attempt,
							"max_attempts": attempts,
						},
					)
					await self._sleep_before_retry(attempt)
					continue
				logger.error(
					"upstream_failure",
					extra={
						"endpoint": endpoint,
						"reason": "transport_error",
						"attempt": attempt,
						"max_attempts": attempts,
					},
				)
				raise HTTPException(
					status_code=status.HTTP_502_BAD_GATEWAY,
					detail="Failed to reach upstream NASA service",
				) from exc
			except httpx.HTTPError as exc:
				logger.error(
					"upstream_failure",
					extra={
						"endpoint": endpoint,
						"reason": "http_error",
						"attempt": attempt,
						"max_attempts": attempts,
					},
				)
				raise HTTPException(
					status_code=status.HTTP_502_BAD_GATEWAY,
					detail="Failed to reach upstream NASA service",
				) from exc

		logger.error(
			"upstream_failure",
			extra={
				"endpoint": endpoint,
				"reason": "retry_exhausted",
				"max_attempts": attempts,
			},
		)
		raise HTTPException(
			status_code=status.HTTP_502_BAD_GATEWAY,
			detail="Failed to reach upstream NASA service",
		)

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

	async def get_asteroids_feed(self, api_key: str | None = None) -> dict[str, Any]:
		url = f"{self._settings.nasa_api_base_url}/neo/rest/v1/feed"
		payload = await self._get_json(url, {"api_key": self._resolve_api_key(api_key)})
		if isinstance(payload, dict):
			return payload
		return {}

	async def get_epic_images(self, api_key: str | None = None) -> list[dict[str, Any]]:
		url = f"{self._settings.nasa_api_base_url}/EPIC/api/natural"
		payload = await self._get_json(url, {"api_key": self._resolve_api_key(api_key)})
		if isinstance(payload, list):
			return payload
		return []
