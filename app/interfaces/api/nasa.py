from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.application.nasa_service import NasaService
from app.interfaces.dependencies.auth import require_cached_api_user, require_premium_user
from app.interfaces.dependencies.nasa import get_nasa_service
from app.interfaces.schemas.nasa import (
	NasaCachedListResponse,
	NasaCachedObjectResponse,
	NasaListResponse,
	NasaObjectResponse,
)
from app.interfaces.schemas.user import UserPrincipal

router = APIRouter(prefix="/api/v1/nasa", tags=["nasa"])


def _resolve_api_key_for_request(request: Request, api_key: str | None) -> str | None:
	if not api_key:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="query param 'api_key' is required.",
		)
	return api_key


def _set_cache_headers(response: Response, *, status_value: str, source_value: str, cache_date: str | None = None) -> None:
	response.headers["X-Cache-Status"] = status_value
	response.headers["X-Data-Source"] = source_value
	if cache_date is not None:
		response.headers["X-Cache-Date"] = cache_date


@router.get("/donki/notifications", response_model=NasaListResponse)
async def get_donki_notifications(
	request: Request,
	response: Response,
	_current_user: Annotated[UserPrincipal, Depends(require_premium_user)],
	service: Annotated[NasaService, Depends(get_nasa_service)],
	api_key: str | None = Query(
		default=None,
		detail="query param 'api_key' is required.",
	),
) -> NasaListResponse:
	response.headers["Cache-Control"] = "no-store"
	_set_cache_headers(response, status_value="BYPASS", source_value="upstream")
	payload = await service.fetch_donki_notifications(
		api_key=_resolve_api_key_for_request(request=request, api_key=api_key)
	)
	return NasaListResponse(source="DONKI", data=payload)


@router.get("/eonet/events", response_model=NasaObjectResponse)
async def get_eonet_events(
	request: Request,
	response: Response,
	_current_user: Annotated[UserPrincipal, Depends(require_premium_user)],
	service: Annotated[NasaService, Depends(get_nasa_service)],
	api_key: str | None = Query(
		default=None,
		detail="query param 'api_key' is required.",
	),
) -> NasaObjectResponse:
	response.headers["Cache-Control"] = "no-store"
	_set_cache_headers(response, status_value="BYPASS", source_value="upstream")
	payload = await service.fetch_eonet_events(
		api_key=_resolve_api_key_for_request(request=request, api_key=api_key)
	)
	return NasaObjectResponse(source="EONET", data=payload)


@router.get("/insight/weather", response_model=NasaCachedObjectResponse)
async def get_insight_weather(
	request: Request,
	response: Response,
	_current_user: Annotated[UserPrincipal, Depends(require_cached_api_user)],
	service: Annotated[NasaService, Depends(get_nasa_service)],
	api_key: str | None = Query(
		default=None,
		detail="query param 'api_key' is required.",
	),
) -> NasaCachedObjectResponse:
	response.headers["Cache-Control"] = "no-store"
	payload = await service.fetch_insight_weather(
		api_key=_resolve_api_key_for_request(request=request, api_key=api_key)
	)
	cache_status = "HIT" if payload["cached"] else "MISS"
	data_source = "cache" if payload["cached"] else "upstream"
	_set_cache_headers(
		response,
		status_value=cache_status,
		source_value=data_source,
		cache_date=payload["cache_date"],
	)
	return NasaCachedObjectResponse(
		source="INSIGHT",
		cached=payload["cached"],
		cache_date=payload["cache_date"],
		data=payload["data"],
	)


@router.get("/asteroids/feed", response_model=NasaCachedObjectResponse)
async def get_asteroids_feed(
	request: Request,
	response: Response,
	_current_user: Annotated[UserPrincipal, Depends(require_cached_api_user)],
	service: Annotated[NasaService, Depends(get_nasa_service)],
	api_key: str | None = Query(
		default=None,
		detail="query param 'api_key' is required.",
	),
) -> NasaCachedObjectResponse:
	response.headers["Cache-Control"] = "no-store"
	payload = await service.fetch_asteroids_feed(
		api_key=_resolve_api_key_for_request(request=request, api_key=api_key)
	)
	cache_status = "HIT" if payload["cached"] else "MISS"
	data_source = "cache" if payload["cached"] else "upstream"
	_set_cache_headers(
		response,
		status_value=cache_status,
		source_value=data_source,
		cache_date=payload["cache_date"],
	)
	return NasaCachedObjectResponse(
		source="ASTEROIDS_NEO_WS",
		cached=payload["cached"],
		cache_date=payload["cache_date"],
		data=payload["data"],
	)


@router.get("/epic/natural", response_model=NasaCachedListResponse)
async def get_epic_natural(
	request: Request,
	response: Response,
	_current_user: Annotated[UserPrincipal, Depends(require_cached_api_user)],
	service: Annotated[NasaService, Depends(get_nasa_service)],
	api_key: str | None = Query(
		default=None,
		detail="query param 'api_key' is required.",
	),
) -> NasaCachedListResponse:
	response.headers["Cache-Control"] = "no-store"
	payload = await service.fetch_epic_images(
		api_key=_resolve_api_key_for_request(request=request, api_key=api_key)
	)
	cache_status = "HIT" if payload["cached"] else "MISS"
	data_source = "cache" if payload["cached"] else "upstream"
	_set_cache_headers(
		response,
		status_value=cache_status,
		source_value=data_source,
		cache_date=payload["cache_date"],
	)
	return NasaCachedListResponse(
		source="EPIC_NATURAL",
		cached=payload["cached"],
		cache_date=payload["cache_date"],
		data=payload["data"],
	)
