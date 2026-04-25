from typing import Annotated
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.security import create_access_token, verify_password
from app.interfaces.dependencies.db import get_db_session
from app.interfaces.schemas.token import TokenResponse
from app.interfaces.schemas.user import LoginRequest
from app.models.user import AuthUser

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def _scope_for_username(username: str, request: Request) -> str:
	if username == request.app.state.settings.premium_username:
		return "premium"
	return "basic"


def _authenticate_and_issue_token(
	*,
	username: str,
	password: str,
	request: Request,
	db_session: Session,
) -> TokenResponse:
	user = db_session.execute(
		select(AuthUser).where(AuthUser.username == username)
	).scalar_one_or_none()

	invalid_credentials_error = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Invalid credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)

	if user is None:
		logger.info("auth_failed", extra={"username": username, "reason": "user_not_found"})
		raise invalid_credentials_error

	if not verify_password(
		password=password,
		password_hash=user.password_hash,
		salt=request.app.state.settings.auth_password_salt,
	):
		logger.info("auth_failed", extra={"username": username, "reason": "password_mismatch"})
		raise invalid_credentials_error

	scope = _scope_for_username(username=user.username, request=request)
	logger.info("auth_success", extra={"username": user.username, "scope": scope})
	token = create_access_token(subject=user.username, scope=scope, settings=request.app.state.settings)
	return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(
	payload: LoginRequest,
	request: Request,
	db_session: Annotated[Session, Depends(get_db_session)],
) -> TokenResponse:
	return _authenticate_and_issue_token(
		username=payload.username,
		password=payload.password,
		request=request,
		db_session=db_session,
	)


@router.post("/token", response_model=TokenResponse)
def token_login(
	request: Request,
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
	db_session: Annotated[Session, Depends(get_db_session)],
) -> TokenResponse:
	return _authenticate_and_issue_token(
		username=form_data.username,
		password=form_data.password,
		request=request,
		db_session=db_session,
	)
