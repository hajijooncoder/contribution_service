import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, get_password_hash
from app.db.session import SessionLocal
from app.db.models import User, Submission
from app.core.security import UserRole

client = TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def admin_user(db_session):
    admin = db_session.query(User).filter(User.email == "test-admin@mahoun.local").first()
    if not admin:
        admin = User(
            id="admin-user-001",
            email="test-admin@mahoun.local",
            hashed_password=get_password_hash("admin-pass-123"),
            full_name="مدیر سیستم",
            role=UserRole.ADMIN,
            is_active=True,
            total_credits=500
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
    return admin

@pytest.fixture
def regular_user(db_session):
    user = db_session.query(User).filter(User.email == "test-contributor@mahoun.local").first()
    if not user:
        user = User(
            id="contrib-user-001",
            email="test-contributor@mahoun.local",
            hashed_password=get_password_hash("contrib-pass-123"),
            full_name="مشارکت‌کننده تست",
            role=UserRole.CONTRIBUTOR,
            is_active=True,
            total_credits=50
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

def test_admin_access_forbidden_for_non_admin(regular_user):
    token = create_access_token(regular_user.id, role=regular_user.role)
    response = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "Administrator permissions required" in response.json()["detail"]

def test_admin_access_unauthorized_without_token():
    response = client.get("/api/v1/admin/users")
    assert response.status_code == 401

def test_admin_list_users(admin_user):
    token = create_access_token(admin_user.id, role=admin_user.role)
    response = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "total" in data
    assert data["total"] >= 1
    assert any(u["id"] == admin_user.id for u in data["users"])

def test_admin_toggle_user_activation(admin_user, regular_user):
    token = create_access_token(admin_user.id, role=admin_user.role)
    
    # Deactivate
    resp_deact = client.put(
        f"/api/v1/admin/users/{regular_user.id}/activate",
        headers={"Authorization": f"Bearer {token}"},
        json={"activate": False}
    )
    assert resp_deact.status_code == 200
    assert resp_deact.json()["is_active"] is False
    
    # Reactivate
    resp_act = client.put(
        f"/api/v1/admin/users/{regular_user.id}/activate",
        headers={"Authorization": f"Bearer {token}"},
        json={"activate": True}
    )
    assert resp_act.status_code == 200
    assert resp_act.json()["is_active"] is True

def test_admin_cannot_deactivate_self(admin_user):
    token = create_access_token(admin_user.id, role=admin_user.role)
    response = client.put(
        f"/api/v1/admin/users/{admin_user.id}/activate",
        headers={"Authorization": f"Bearer {token}"},
        json={"activate": False}
    )
    assert response.status_code == 400
    assert "مدیر ارشد نمی‌تواند" in response.json()["detail"]

def test_admin_update_user_role(admin_user, regular_user):
    token = create_access_token(admin_user.id, role=admin_user.role)
    
    # Promote to reviewer
    resp = client.put(
        f"/api/v1/admin/users/{regular_user.id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "reviewer"}
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "reviewer"
    
    # Demote back
    resp_demote = client.put(
        f"/api/v1/admin/users/{regular_user.id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "contributor"}
    )
    assert resp_demote.status_code == 200
    assert resp_demote.json()["role"] == "contributor"

def test_admin_stats_overview(admin_user):
    token = create_access_token(admin_user.id, role=admin_user.role)
    response = client.get(
        "/api/v1/admin/stats/overview",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    stats = response.json()
    assert "total_users" in stats
    assert "total_submissions" in stats
    assert "pending_reviews" in stats
    assert "accepted_submissions" in stats
    assert "total_credits_awarded" in stats
    assert stats["total_users"] >= 1

def test_admin_export_overview(admin_user):
    token = create_access_token(admin_user.id, role=admin_user.role)
    response = client.get(
        "/api/v1/admin/export/overview",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    overview = response.json()
    assert overview["isolation_verified"] is True
    assert overview["schema_version"] == "mahoun-1.0"
    assert "total_export_ready" in overview
