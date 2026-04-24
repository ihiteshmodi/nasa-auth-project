from typing import Annotated

from fastapi import Depends
from fastapi import Request
from sqlalchemy.orm import Session

from app.application.nasa_service import NasaService
from app.infrastructure.nasa_client import NasaClient
from app.interfaces.dependencies.db import get_db_session


def get_nasa_service(
	request: Request,
	db_session: Annotated[Session, Depends(get_db_session)],
) -> NasaService:
    client = NasaClient(settings=request.app.state.settings, client=request.app.state.http_client)
    return NasaService(client=client, db_session=db_session)
