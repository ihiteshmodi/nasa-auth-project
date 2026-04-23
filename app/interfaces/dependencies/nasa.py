from fastapi import Request

from app.application.nasa_service import NasaService
from app.infrastructure.nasa_client import NasaClient


def get_nasa_service(request: Request) -> NasaService:
    client = NasaClient(settings=request.app.state.settings, client=request.app.state.http_client)
    return NasaService(client=client)
