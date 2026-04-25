from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.config import settings
from app.infrastructure.db import Base
from app.infrastructure.security import hash_password
from app.interfaces.dependencies.db import get_db_session
from app.interfaces.dependencies.nasa import get_nasa_service
from app.interfaces.main import create_app
from app.models.user import AuthUser


class FakeNasaService:
    async def fetch_eonet_events(self, api_key: str | None = None) -> dict[str, list[dict[str, str]]]:
        return {"events": [{"id": "EONET_SMOKE"}]}


def _seed_users(session: Session) -> None:
    session.add(
        AuthUser(
            username="premium_user",
            password_hash=hash_password("premium_password", "nasa-auth-sample-salt"),
            created_at=datetime.now(timezone.utc),
        )
    )
    session.commit()


def _build_smoke_client() -> tuple[TestClient, Session]:
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


def test_e2e_smoke_health_login_and_protected_endpoint() -> None:
    client, session = _build_smoke_client()
    try:
        health = client.get("/health")
        assert health.status_code == 200

        login = client.post(
            "/api/v1/auth/login",
            json={"username": "premium_user", "password": "premium_password"},
        )
        assert login.status_code == 200
        access_token = login.json()["access_token"]

        protected = client.get(
            "/api/v1/nasa/eonet/events",
            params={"api_key": "DEMO_KEY"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert protected.status_code == 200
        assert protected.json()["source"] == "EONET"
        assert protected.json()["data"] == {"events": [{"id": "EONET_SMOKE"}]}
    finally:
        session.close()
        client.close()
