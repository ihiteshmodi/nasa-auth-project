from datetime import datetime, timezone
import logging

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.db import Base
from app.infrastructure.security import hash_password
from app.infrastructure.config import settings
from app.interfaces.dependencies.db import get_db_session
from app.interfaces.dependencies.nasa import get_nasa_service
from app.interfaces.main import create_app
from app.models.user import AuthUser


class FakeNasaService:
    async def fetch_donki_notifications(self, api_key: str | None = None) -> list[dict[str, str]]:
        return [{"messageType": "all"}]

    async def fetch_eonet_events(self, api_key: str | None = None) -> dict[str, list[dict[str, str]]]:
        return {"events": [{"id": "EONET_1"}]}

    async def fetch_insight_weather(self, api_key: str | None = None) -> dict[str, list[str]]:
        return {"sol_keys": ["1000"]}

    async def fetch_asteroids_feed(self, api_key: str | None = None) -> dict[str, object]:
        return {
            "data": {"near_earth_objects": {}},
            "cached": True,
            "cache_date": "2026-04-24",
        }

    async def fetch_epic_images(self, api_key: str | None = None) -> dict[str, object]:
        return {
            "data": [{"identifier": "epic-id"}],
            "cached": False,
            "cache_date": "2026-04-24",
        }


def _seed_users(session: Session) -> None:
    session.add(
        AuthUser(
            username="basic_user",
            password_hash=hash_password("basic_password", "nasa-auth-sample-salt"),
            created_at=datetime.now(timezone.utc),
        )
    )
    session.add(
        AuthUser(
            username="premium_user",
            password_hash=hash_password("premium_password", "nasa-auth-sample-salt"),
            created_at=datetime.now(timezone.utc),
        )
    )
    session.commit()


def _build_test_app() -> tuple[TestClient, Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session: Session = session_factory()
    _seed_users(session)

    def override_db_session():
        try:
            yield session
        finally:
            pass

    app = create_app()
    app.state.settings = settings
    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_nasa_service] = lambda: FakeNasaService()

    return TestClient(app), session


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_login_rejects_invalid_credentials(caplog) -> None:
    client, session = _build_test_app()
    try:
        with caplog.at_level(logging.INFO):
            response = client.post("/api/v1/auth/login", json={"username": "basic_user", "password": "wrong"})
    finally:
        session.close()
        client.close()

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}
    auth_failed_records = [record for record in caplog.records if record.msg == "auth_failed"]
    assert auth_failed_records
    assert auth_failed_records[-1].__dict__.get("username") == "basic_user"
    assert auth_failed_records[-1].__dict__.get("reason") == "password_mismatch"


def test_token_login_accepts_oauth2_form_data(caplog) -> None:
    client, session = _build_test_app()
    try:
        with caplog.at_level(logging.INFO):
            response = client.post(
                "/api/v1/auth/token",
                data={"username": "basic_user", "password": "basic_password"},
            )
    finally:
        session.close()
        client.close()

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert isinstance(response.json()["access_token"], str)
    auth_success_records = [record for record in caplog.records if record.msg == "auth_success"]
    assert auth_success_records
    assert auth_success_records[-1].__dict__.get("username") == "basic_user"
    assert auth_success_records[-1].__dict__.get("scope") == "basic"
    assert all("basic_password" not in record.getMessage() for record in caplog.records)


def test_token_login_rejects_invalid_form_credentials() -> None:
    client, session = _build_test_app()
    try:
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "basic_user", "password": "wrong"},
        )
    finally:
        session.close()
        client.close()

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_basic_user_can_access_cached_api() -> None:
    client, session = _build_test_app()
    try:
        token = _login(client, "basic_user", "basic_password")
        response = client.get(
            "/api/v1/nasa/asteroids/feed",
            params={"api_key": "DEMO_KEY"},
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        session.close()
        client.close()

    assert response.status_code == 200
    assert response.json()["source"] == "ASTEROIDS_NEO_WS"


def test_basic_user_is_forbidden_for_nocache_api() -> None:
    client, session = _build_test_app()
    try:
        token = _login(client, "basic_user", "basic_password")
        response = client.get(
            "/api/v1/nasa/eonet/events",
            params={"api_key": "DEMO_KEY"},
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        session.close()
        client.close()

    assert response.status_code == 403
    assert response.json() == {"detail": "Unauthorized for this API"}


def test_premium_user_can_access_nocache_api() -> None:
    client, session = _build_test_app()
    try:
        token = _login(client, "premium_user", "premium_password")
        response = client.get(
            "/api/v1/nasa/eonet/events",
            params={"api_key": "DEMO_KEY"},
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        session.close()
        client.close()

    assert response.status_code == 200
    assert response.json()["source"] == "EONET"


def test_api_key_is_still_required_even_with_auth() -> None:
    client, session = _build_test_app()
    try:
        token = _login(client, "premium_user", "premium_password")
        response = client.get(
            "/api/v1/nasa/eonet/events",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        session.close()
        client.close()

    assert response.status_code == 400
    assert response.json() == {"detail": "query param 'api_key' is required."}
