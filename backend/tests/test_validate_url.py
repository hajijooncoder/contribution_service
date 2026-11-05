import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_validate_url_valid_official_gazette():
    """Test validating official gazette (rrk.ir)"""
    response = client.post(
        "/api/v1/contribution/validate-url",
        json={"url": "https://rrk.ir/laws/show/12345"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert "روزنامه رسمی" in data["authority"]
    assert data["error"] is None

def test_validate_url_valid_parliament():
    """Test validating Majlis research center (rc.majlis.ir)"""
    response = client.post(
        "/api/v1/contribution/validate-url",
        json={"url": "https://rc.majlis.ir/fa/law/show/9999"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert "مجلس" in data["authority"]
    assert data["error"] is None

def test_validate_url_valid_dotic():
    """Test validating presidential laws portal (dotic.ir)"""
    response = client.post(
        "/api/v1/contribution/validate-url",
        json={"url": "https://dotic.ir/laws/detail/100"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert "قوانین و مقررات" in data["authority"]
    assert data["error"] is None

def test_validate_url_without_scheme():
    """Test auto-prepending scheme when missing"""
    response = client.post(
        "/api/v1/contribution/validate-url",
        json={"url": "qavanin.ir/Law/TreeText/1234"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert "سامانه ملی قوانین" in data["authority"]

def test_validate_url_invalid_domain():
    """Test rejecting unauthorized or foreign domain"""
    response = client.post(
        "/api/v1/contribution/validate-url",
        json={"url": "https://unauthorized-law-site.com/doc/1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["authority"] is None
    assert "مرجع نامعتبر است" in data["error"]

def test_validate_url_empty_string():
    """Test rejecting empty URL"""
    response = client.post(
        "/api/v1/contribution/validate-url",
        json={"url": ""}
    )
    assert response.status_code == 422 or (response.status_code == 200 and response.json()["valid"] is False)
