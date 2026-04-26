from contextlib import asynccontextmanager
import logging
import time
import uuid

import httpx
from fastapi import FastAPI, Request

from app.infrastructure.config import settings
from app.infrastructure.db import SessionLocal
from app.infrastructure.logging import clear_request_id, configure_logging, set_request_id
from app.infrastructure.telemetry import configure_telemetry
from app.interfaces.api.auth import router as auth_router
from app.interfaces.api.nasa import router as nasa_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
	async with httpx.AsyncClient() as http_client:
		app.state.http_client = http_client
		app.state.settings = settings
		app.state.db_session_factory = SessionLocal
		yield


def create_app() -> FastAPI:
	configure_logging(settings)

	app = FastAPI(
		title="NASA Auth Project API",
		version="0.1.0",
		lifespan=lifespan,
	)
	configure_telemetry(app, settings)

	@app.middleware("http")
	async def log_request_lifecycle(request: Request, call_next):
		request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
		set_request_id(request_id)

		start = time.perf_counter()
		logger.info(
			"request_start",
			extra={
				"request_id": request_id,
				"method": request.method,
				"path": request.url.path,
			},
		)

		try:
			response = await call_next(request)
		except Exception:
			duration_ms = round((time.perf_counter() - start) * 1000, 2)
			logger.exception(
				"request_failed",
				extra={
					"request_id": request_id,
					"method": request.method,
					"path": request.url.path,
					"duration_ms": duration_ms,
				},
			)
			clear_request_id()
			raise

		duration_ms = round((time.perf_counter() - start) * 1000, 2)
		response.headers["X-Request-ID"] = request_id
		logger.info(
			"request_complete",
			extra={
				"request_id": request_id,
				"method": request.method,
				"path": request.url.path,
				"status_code": response.status_code,
				"duration_ms": duration_ms,
			},
		)
		clear_request_id()
		return response

	@app.get("/health", tags=["health"])
	def health() -> dict[str, str]:
		return {"status": "ok"}

	app.include_router(nasa_router)
	app.include_router(auth_router)
	return app


app = create_app()
