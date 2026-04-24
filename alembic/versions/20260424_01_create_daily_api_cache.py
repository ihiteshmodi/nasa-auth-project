"""create daily api cache table

Revision ID: 20260424_01
Revises: 
Create Date: 2026-04-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260424_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "daily_api_cache",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("endpoint", sa.String(length=128), nullable=False),
        sa.Column("cache_date", sa.Date(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("endpoint", "cache_date", name="uq_daily_api_cache_endpoint_date"),
    )


def downgrade() -> None:
    op.drop_table("daily_api_cache")
