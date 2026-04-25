import os

from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
	nasa_api_key: str = Field(default_factory=lambda: os.getenv("NASA_API_KEY", ""))
	nasa_api_base_url: str = "https://api.nasa.gov"
	eonet_base_url: str = "https://eonet.gsfc.nasa.gov/api/v3"
	database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./nasa_artifacts.db"))
	app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "local"))
	log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
	log_json: bool = Field(default_factory=lambda: os.getenv("LOG_JSON", "true").lower() in {"1", "true", "yes", "on"})
	log_service_name: str = Field(default_factory=lambda: os.getenv("LOG_SERVICE_NAME", "nasa-auth-project"))
	http_timeout_seconds: float = Field(default=10.0)
	http_retry_attempts: int = 3
	http_retry_backoff_seconds: float = 0.2
	jwt_secret_key: str = Field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", "replace-this-in-prod"))
	jwt_algorithm: str = "HS256"
	jwt_access_token_expire_minutes: int = 60
	auth_password_salt: str = Field(default_factory=lambda: os.getenv("AUTH_PASSWORD_SALT", "nasa-auth-sample-salt"))
	basic_username: str = Field(default_factory=lambda: os.getenv("BASIC_USERNAME", "basic_user"))
	premium_username: str = Field(default_factory=lambda: os.getenv("PREMIUM_USERNAME", "premium_user"))


settings = Settings()
