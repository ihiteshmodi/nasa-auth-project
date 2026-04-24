"""create auth users table and seed sample users

Revision ID: 20260424_02
Revises: 20260424_01
Create Date: 2026-04-24 01:00:00.000000
"""

import hashlib
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


revision = "20260424_02"
down_revision = "20260424_01"
branch_labels = None
depends_on = None


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def upgrade() -> None:
    op.create_table(
        "auth_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )

    salt = "nasa-auth-sample-salt"
    users_table = sa.table(
        "auth_users",
        sa.column("username", sa.String),
        sa.column("password_hash", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )

    op.bulk_insert(
        users_table,
        [
            {
                "username": "basic_user",
                "password_hash": _hash_password("basic_password", salt),
                "created_at": datetime.now(timezone.utc),
            },
            {
                "username": "premium_user",
                "password_hash": _hash_password("premium_password", salt),
                "created_at": datetime.now(timezone.utc),
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("auth_users")
