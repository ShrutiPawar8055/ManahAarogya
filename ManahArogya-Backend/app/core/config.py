from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "ManahAarogya Backend"
    app_version: str = "2.0.0"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    database_url: str = ""
    sqlite_file: str = "backend.db"
    cerebras_api_key: str = ""
    cerebras_base_url: str = "https://api.cerebras.ai/v1"
    cerebras_model: str = "qwen-3-235b-a22b-instruct-2507"
    firebase_project_id: str = ""
    firebase_private_key: str = ""
    firebase_client_email: str = ""
    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""
    livekit_token_ttl_minutes: int = 60
    sarvam_api_key: str = ""
    cron_secret: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def sqlite_url(self) -> str:
        """Build the SQLAlchemy URL for SQLite."""
        database_path = Path(self.sqlite_file).as_posix()
        return f"sqlite:///{database_path}"

    @property
    def sqlalchemy_url(self) -> str:
        """Return DATABASE_URL when set, otherwise fallback to SQLite."""
        if self.database_url:
            return self.database_url.replace("postgres://", "postgresql://", 1)
        return self.sqlite_url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()


settings = get_settings()
