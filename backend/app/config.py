import os
from pathlib import Path
from typing import Optional, Set
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Mahoun Legal Contribution Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # Staging Database (PostgreSQL for production/staging, SQLite fallback for dev/testing)
    DATABASE_URL: str = os.getenv(
        "CONTRIBUTION_DATABASE_URL", 
        f"sqlite:///{BASE_DIR}/storage/staging.db"
    )
    
    # Authentication & Session Security (Distinct from internal core secrets)
    SECRET_KEY: str = os.getenv("CONTRIBUTION_SECRET_KEY", "super-secret-contribution-staging-key-do-not-use-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Cryptographic Audit Ledger HMAC Key (Custody separate from database layer)
    AUDIT_LEDGER_SECRET: str = os.getenv("AUDIT_LEDGER_SECRET", "staging-audit-hmac-key-2026-isolated")
    
    # Optional Distributed Redis URL for multi-worker rate limiting
    REDIS_URL: Optional[str] = os.getenv("CONTRIBUTION_REDIS_URL", None)
    TRUSTED_PROXIES: Set[str] = {"127.0.0.1", "::1", "localhost"}
    
    # Internal Pull-Bridge Gateway Token (Used by secure core to pull staging packages)
    EXPORT_GATEWAY_TOKEN: str = os.getenv("EXPORT_GATEWAY_TOKEN", "mahoun-internal-secure-pull-token-dev")
    
    # File Storage & Quarantine Policy
    QUARANTINE_STORAGE_PATH: str = os.getenv(
        "QUARANTINE_STORAGE_PATH", 
        str(BASE_DIR / "storage" / "quarantine")
    )
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB limit
    ALLOWED_EXTENSIONS: set = {"pdf", "docx", "txt", "rtf"}
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
