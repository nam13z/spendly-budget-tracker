"""Validated environment settings for the API."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = REPOSITORY_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables or a local .env file."""

    app_env: Literal["development", "test", "production"] = "development"
    db_host: str = Field(default="127.0.0.1", min_length=1)
    db_port: int = Field(default=3307, ge=1, le=65535)
    db_name: str = Field(default="spendly", min_length=1)
    db_user: str = Field(default="spendly_app", min_length=1)
    db_password: SecretStr

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    @property
    def sqlalchemy_url(self) -> URL:
        """Build a safely escaped SQLAlchemy URL without rendering credentials."""
        return URL.create(
            drivername="mysql+pymysql",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
