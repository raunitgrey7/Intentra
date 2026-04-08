from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	app_name: str = "Intentra API"
	environment: str = "development"
	debug: bool = False
	cors_origins: str = "*"
	request_timeout_seconds: int = Field(default=45, ge=5, le=180)
	recommend_timeout_seconds: int = Field(default=60, ge=5, le=240)
	external_api_timeout_seconds: int = Field(default=6, ge=2, le=60)
	max_place_types_per_query: int = Field(default=4, ge=1, le=8)
	overpass_max_mirrors_per_query: int = Field(default=2, ge=1, le=3)
	fallback_phase_timeout_seconds: int = Field(default=8, ge=2, le=40)

	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		case_sensitive=False,
		extra="ignore",
	)

	@property
	def parsed_cors_origins(self) -> list[str]:
		value = self.cors_origins.strip()
		if value == "*":
			return ["*"]
		return [origin.strip() for origin in value.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
	return Settings()
