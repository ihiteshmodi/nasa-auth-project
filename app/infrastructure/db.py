from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.infrastructure.config import settings


class Base(DeclarativeBase):
	pass


def _is_sqlite(url: str) -> bool:
	return url.startswith("sqlite")


connect_args = {"check_same_thread": False} if _is_sqlite(settings.database_url) else {}

engine = create_engine(settings.database_url, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
