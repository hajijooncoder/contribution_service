import os
import tempfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup temp directory for DB and quarantine
temp_dir = tempfile.mkdtemp()
temp_db_path = Path(temp_dir) / "test_staging.db"
temp_quarantine_path = Path(temp_dir) / "quarantine"
temp_quarantine_path.mkdir(parents=True, exist_ok=True)

os.environ["CONTRIBUTION_DATABASE_URL"] = f"sqlite:///{temp_db_path}"
os.environ["CONTRIBUTION_SECRET_KEY"] = "test-secret-key-32-bytes-minimum-length-for-hmac-sha256"
os.environ["EXPORT_GATEWAY_TOKEN"] = "test-export-gateway-token"
os.environ["QUARANTINE_STORAGE_PATH"] = str(temp_quarantine_path)

from app.config import settings
settings.DATABASE_URL = f"sqlite:///{temp_db_path}"
settings.QUARANTINE_STORAGE_PATH = str(temp_quarantine_path)

from app.db import session as db_session_module
from app.db.session import Base
from app.main import app
from app.core.security import create_access_token, get_password_hash, UserRole
from app.db.models import User

# Ensure engine is pointing to our temp sqlite db
test_engine = create_engine(
    f"sqlite:///{temp_db_path}",
    connect_args={"check_same_thread": False}
)
db_session_module.engine = test_engine
db_session_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(autouse=True)
def reset_rate_limiter_each_test():
    from app.core.rate_limiter import global_rate_limiter
    global_rate_limiter.reset()
    yield
    global_rate_limiter.reset()

@pytest.fixture
def db_session():
    session = db_session_module.SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def contributor_user(db_session):
    email = "contributor@example.com"
    existing = db_session.query(User).filter(User.email == email).first()
    if existing:
        return existing
    user = User(
        email=email,
        hashed_password=get_password_hash("password123"),
        full_name="علی محمدی",
        role=UserRole.CONTRIBUTOR,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def reviewer_user(db_session):
    email = "reviewer@example.com"
    existing = db_session.query(User).filter(User.email == email).first()
    if existing:
        return existing
    user = User(
        email=email,
        hashed_password=get_password_hash("reviewer123"),
        full_name="دکتر رضایی (داور ۱)",
        role=UserRole.REVIEWER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def reviewer_user_2(db_session):
    email = "reviewer2@example.com"
    existing = db_session.query(User).filter(User.email == email).first()
    if existing:
        return existing
    user = User(
        email=email,
        hashed_password=get_password_hash("reviewer456"),
        full_name="دکتر سهرابی (داور ۲)",
        role=UserRole.REVIEWER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def contributor_headers(contributor_user):
    token = create_access_token(subject=contributor_user.id, role=contributor_user.role)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def reviewer_headers(reviewer_user):
    token = create_access_token(subject=reviewer_user.id, role=reviewer_user.role)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def reviewer_headers_2(reviewer_user_2):
    token = create_access_token(subject=reviewer_user_2.id, role=reviewer_user_2.role)
    return {"Authorization": f"Bearer {token}"}
