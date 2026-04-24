from pydantic import BaseModel


class LoginRequest(BaseModel):
	username: str
	password: str


class UserPrincipal(BaseModel):
	username: str
	scope: str
