from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import Date, DateTime, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db import Base


class DailyApiCache(Base):
    __tablename__ = "daily_api_cache"
    __table_args__ = (UniqueConstraint("endpoint", "cache_date", name="uq_daily_api_cache_endpoint_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    endpoint: Mapped[str] = mapped_column(String(128), nullable=False)
    cache_date: Mapped[date] = mapped_column(Date, nullable=False)
    payload: Mapped[Any] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
