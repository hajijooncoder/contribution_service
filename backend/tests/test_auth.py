from app.core.security import create_access_token, UserRole
from app.db.models import User

def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepassword",
            "full_name": "سارا حسینی"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "contributor"
    assert "id" in data

def test_register_strictly_forbids_role_escalation(client):
    """
    CRITICAL SECURITY TEST: Ensure an attacker cannot inject 'role': 'admin' or 'reviewer'
    during registration. Must be rejected with HTTP 422 Unprocessable Entity.
    """
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "hacker@example.com",
            "password": "hackerpassword",
            "full_name": "هکر نامعتبر",
            "role": "admin"
        }
    )
    assert response.status_code == 422

def test_admin_role_promotion(client, db_session):
    """
    Verifies that role promotion can only be performed by an authenticated administrator.
    """
    # 1. Create a regular user
    user = User(
        email="promoteme@example.com",
        hashed_password="hash",
        full_name="کاربر ارتقایی",
        role=UserRole.CONTRIBUTOR,
        is_active=True
    )
    admin = User(
        email="rootadmin@example.com",
        hashed_password="hash",
        full_name="مدیر سیستم",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    db_session.add(admin)
    db_session.commit()

    admin_token = create_access_token(subject=admin.id, role=UserRole.ADMIN)
    contributor_token = create_access_token(subject=user.id, role=UserRole.CONTRIBUTOR)

    # Contributor cannot promote themselves (403 Forbidden)
    forbidden_resp = client.put(
        f"/api/v1/auth/users/{user.id}/role",
        json={"role": "reviewer"},
        headers={"Authorization": f"Bearer {contributor_token}"}
    )
    assert forbidden_resp.status_code == 403

    # Admin can promote contributor to reviewer
    success_resp = client.put(
        f"/api/v1/auth/users/{user.id}/role",
        json={"role": "reviewer"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert success_resp.status_code == 200
    assert success_resp.json()["role"] == "reviewer"

def test_login_success(client, contributor_user):
    response = client.post(
        "/api/v1/auth/token",
        json={
            "email": "contributor@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "contributor"

def test_login_wrong_password(client, contributor_user):
    response = client.post(
        "/api/v1/auth/token",
        json={
            "email": "contributor@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401

def test_get_me(client, contributor_headers):
    response = client.get("/api/v1/auth/me", headers=contributor_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "contributor@example.com"
