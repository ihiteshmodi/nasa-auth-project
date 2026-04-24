from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.infrastructure.config import settings
from app.infrastructure.db import SessionLocal
from app.interfaces.api.auth import router as auth_router
from app.interfaces.api.nasa import router as nasa_router


@asynccontextmanager
async def lifespan(app: FastAPI):
	async with httpx.AsyncClient() as http_client:
		app.state.http_client = http_client
		app.state.settings = settings
		app.state.db_session_factory = SessionLocal
		yield


def create_app() -> FastAPI:
	app = FastAPI(
		title="NASA Auth Project API",
		version="0.1.0",
		lifespan=lifespan,
	)

	@app.get("/health", tags=["health"])
	async def health() -> dict[str, str]:
		return {"status": "ok"}

	app.include_router(nasa_router)
	app.include_router(auth_router)
	return app


app = create_app()
