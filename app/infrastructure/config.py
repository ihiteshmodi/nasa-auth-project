import os

from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
	nasa_api_key: str = Field(default_factory=lambda: os.getenv("NASA_API_KEY", ""))
	nasa_api_base_url: str = "https://api.nasa.gov"
	eonet_base_url: str = "https://eonet.gsfc.nasa.gov/api/v3"
	database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./nasa_cache.db"))
	http_timeout_seconds: float = Field(default=10.0)


settings = Settings()
