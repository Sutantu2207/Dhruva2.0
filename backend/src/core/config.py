"""Dhruva.AI V2 — Centralized Configuration Management.

Handles environment-based configuration across development, test, staging, and production.
Enforces fail-fast validation in staging and production to prevent insecure deployments.
"""

from enum import Enum
from functools import lru_cache
from typing import List, Union
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Environment & Service
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT
    DEBUG: bool = False
    SERVICE_NAME: str = "dhruva-backend"
    API_V1_PREFIX: str = "/api/v1"

    # Security & Cryptography
    SECRET_KEY: str = Field(
        default="dev_insecure_secret_key_change_in_production_min_32_chars_ok",
        description="Master secret key for signing tokens and HMACs",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Argon2id Hashing Parameters (OWASP recommendations)
    ARGON2_TIME_COST: int = 3
    ARGON2_MEMORY_COST: int = 65536  # 64 MB
    ARGON2_PARALLELISM: int = 4

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./dhruva_dev.db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False

    # Redis Cache / Session Store
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False

    # Rate Limiting
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5
    RATE_LIMIT_DEFAULT_PER_MINUTE: int = 100

    # CORS & Cookies
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Fail-fast validator: Staging and Production must not run with default or insecure secrets."""
        if self.ENVIRONMENT in (EnvironmentType.PRODUCTION, EnvironmentType.STAGING):
            if "dev_" in self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    f"Production/Staging violation: SECRET_KEY must be a cryptographically secure random string with at least 32 characters. Provided length: {len(self.SECRET_KEY)}"
                )
            if self.DATABASE_URL.startswith("sqlite"):
                raise ValueError(
                    "Production/Staging violation: SQLite cannot be used in production or staging. Must be a valid PostgreSQL 16 connection URI."
                )
            if self.DEBUG:
                raise ValueError(
                    "Production/Staging violation: DEBUG mode must be disabled in production/staging."
                )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
