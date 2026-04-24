from datetime import UTC, datetime, timedelta
import hashlib
import hmac
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError

from app.infrastructure.config import Settings


def hash_password(password: str, salt: str) -> str:
	seed = f"{salt}:{password}".encode("utf-8")
	return hashlib.sha256(seed).hexdigest()


def verify_password(password: str, password_hash: str, salt: str) -> bool:
	computed_hash = hash_password(password=password, salt=salt)
	return hmac.compare_digest(computed_hash, password_hash)


def create_access_token(*, subject: str, scope: str, settings: Settings) -> str:
	now = datetime.now(UTC)
	expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
	payload: dict[str, Any] = {
		"sub": subject,
		"scope": scope,
		"iat": int(now.timestamp()),
		"exp": int(expire.timestamp()),
	}
	return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
	return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


__all__ = [
	"InvalidTokenError",
	"create_access_token",
	"decode_access_token",
	"hash_password",
	"verify_password",
]
