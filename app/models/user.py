from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db import Base


class AuthUser(Base):
	__tablename__ = "auth_users"

	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
	password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
