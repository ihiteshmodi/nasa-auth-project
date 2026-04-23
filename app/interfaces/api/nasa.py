from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.application.nasa_service import NasaService
from app.interfaces.dependencies.nasa import get_nasa_service
from app.interfaces.schemas.nasa import NasaListResponse, NasaObjectResponse

router = APIRouter(prefix="/api/v1/nasa", tags=["nasa"])


def _resolve_api_key_for_request(request: Request, api_key: str | None) -> str | None:
	referer = request.headers.get("referer", "")
	is_docs_request = "/docs" in referer
	if is_docs_request and not api_key:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="query param 'api_key' is required.",
		)
	return api_key


@router.get("/donki/notifications", response_model=NasaListResponse)
async def get_donki_notifications(
	request: Request,
	response: Response,
	service: Annotated[NasaService, Depends(get_nasa_service)],
	api_key: str | None = Query(
		default=None,
		detail="query param 'api_key' is required.",
	),
) -> NasaListResponse:
	response.headers["Cache-Control"] = "no-store"
	payload = await service.fetch_donki_notifications(
		api_key=_resolve_api_key_for_request(request=request, api_key=api_key)
	)
	return NasaListResponse(source="DONKI", data=payload)


@router.get("/eonet/events", response_model=NasaObjectResponse)
async def get_eonet_events(
	request: Request,
	response: Response,
	service: Annotated[NasaService, Depends(get_nasa_service)],
	api_key: str | None = Query(
		default=None,
		detail="query param 'api_key' is required.",
	),
) -> NasaObjectResponse:
	response.headers["Cache-Control"] = "no-store"
	payload = await service.fetch_eonet_events(
		api_key=_resolve_api_key_for_request(request=request, api_key=api_key)
	)
	return NasaObjectResponse(source="EONET", data=payload)


@router.get("/insight/weather", response_model=NasaObjectResponse)
async def get_insight_weather(
	request: Request,
	response: Response,
	service: Annotated[NasaService, Depends(get_nasa_service)],
	api_key: str | None = Query(
		default=None,
		detail="query param 'api_key' is required.",
	),
) -> NasaObjectResponse:
	response.headers["Cache-Control"] = "no-store"
	payload = await service.fetch_insight_weather(
		api_key=_resolve_api_key_for_request(request=request, api_key=api_key)
	)
	return NasaObjectResponse(source="INSIGHT", data=payload)
