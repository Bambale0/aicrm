from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = "production"
    debug: bool = False
    log_level: str = "INFO"

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    public_registration_enabled: bool = False
    auth_required: bool = True

    database_url: str
    redis_url: str
    telegram_api_base_url: str
    ai_api_base_url: str
    ai_api_timeout_seconds: float = 30.0
    automation_max_depth: int = 8

    cors_origins: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            item.strip()
            for item in self.cors_origins.split(",")
            if item.strip()
        ]


settings = Settings()
