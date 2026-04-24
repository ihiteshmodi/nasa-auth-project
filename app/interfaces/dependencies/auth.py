from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.security import InvalidTokenError, decode_access_token
from app.interfaces.dependencies.db import get_db_session
from app.interfaces.schemas.user import UserPrincipal
from app.models.user import AuthUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def _credentials_error() -> HTTPException:
	return HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Invalid credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)


def _scope_for_username(username: str, request: Request) -> str:
	if username == request.app.state.settings.premium_username:
		return "premium"
	return "basic"


def get_current_user(
	request: Request,
	token: Annotated[str, Depends(oauth2_scheme)],
	db_session: Annotated[Session, Depends(get_db_session)],
) -> UserPrincipal:
	credentials_error = _credentials_error()
	try:
		payload = decode_access_token(token=token, settings=request.app.state.settings)
	except InvalidTokenError as exc:
		raise credentials_error from exc

	username = payload.get("sub")
	if not isinstance(username, str) or not username:
		raise credentials_error

	user = db_session.execute(select(AuthUser).where(AuthUser.username == username)).scalar_one_or_none()
	if user is None:
		raise credentials_error

	return UserPrincipal(username=username, scope=_scope_for_username(username=username, request=request))


def require_premium_user(
	current_user: Annotated[UserPrincipal, Depends(get_current_user)],
) -> UserPrincipal:
	if current_user.scope != "premium":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized for this API")
	return current_user


def require_cached_api_user(
	current_user: Annotated[UserPrincipal, Depends(get_current_user)],
) -> UserPrincipal:
	if current_user.scope not in {"basic", "premium"}:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized for this API")
	return current_user
