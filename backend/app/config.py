import os
import ipaddress
from pathlib import Path
from typing import Optional, Set, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator

BASE_DIR = Path(__file__).resolve().parent.parent


def parse_trusted_proxies(value: str) -> Set[str]:
    """Parse comma-separated list of trusted proxies, supports CIDR notation."""
    proxies = set()
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            network = ipaddress.ip_network(item, strict=False)
            proxies.add(str(network))
        except ValueError:
            proxies.add(item)
    return proxies


class Settings(BaseSettings):
    PROJECT_NAME: str = "Mahoun Legal Contribution Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    DATABASE_URL: str = os.getenv(
        "CONTRIBUTION_DATABASE_URL",
        f"sqlite:///{BASE_DIR}/storage/staging.db"
    )

    SECRET_KEY: str = os.getenv("CONTRIBUTION_SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    AUDIT_LEDGER_SECRET: str = os.getenv("AUDIT_LEDGER_SECRET", "")
    AUDIT_LEDGER_KEY_VERSION: int = 1

    REDIS_URL: Optional[str] = os.getenv("CONTRIBUTION_REDIS_URL", None)

    TRUSTED_PROXIES_RAW: str = os.getenv("TRUSTED_PROXIES", "127.0.0.1,::1,localhost")
    TRUSTED_PROXIES: Set[str] = set()

    EXPORT_GATEWAY_TOKEN: str = os.getenv("EXPORT_GATEWAY_TOKEN", "")

    QUARANTINE_STORAGE_PATH: str = os.getenv(
        "QUARANTINE_STORAGE_PATH",
        str(BASE_DIR / "storage" / "quarantine")
    )
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024
    ALLOWED_EXTENSIONS: set = {"pdf", "docx", "txt", "rtf"}

    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30

    RATE_LIMIT_DEFAULT: int = 20
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    @field_validator("TRUSTED_PROXIES", mode="before")
    @classmethod
    def _parse_trusted_proxies(cls, v):
        if isinstance(v, str):
            return parse_trusted_proxies(v)
        if isinstance(v, (set, list)):
            return set(v)
        return set()

    @field_validator("SECRET_KEY", "AUDIT_LEDGER_SECRET", "EXPORT_GATEWAY_TOKEN")
    @classmethod
    def _validate_secrets_not_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} must be set via environment variable")
        if cls._is_production() and ("staging" in v.lower() or "dev" in v.lower() or "test" in v.lower()):
            raise ValueError(f"{info.field_name} appears to be a development value in production")
        return v

    @classmethod
    def _is_production(cls) -> bool:
        env = os.getenv("ENVIRONMENT", "development").lower()
        return env in ("production", "prod")

    @model_validator(mode="after")
    def validate_production_requirements(self):
        if self._is_production():
            if not self.REDIS_URL:
                raise ValueError("REDIS_URL (CONTRIBUTION_REDIS_URL) is required in production")
            if self.DATABASE_URL.startswith("sqlite"):
                raise ValueError("PostgreSQL required in production (DATABASE_URL)")
        return self

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()