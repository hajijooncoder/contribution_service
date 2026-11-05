import pytest
from fastapi.testclient import TestClient
from app.db.models import Submission, User
from app.core.security import create_access_token

def test_recent_activity_unauthorized(client: TestClient):
    """انکار دسترسی به فعالیت‌های اخیر بدون احراز هویت."""
    resp = client.get("/api/v1/contribution/recent-activity")
    assert resp.status_code == 401

def test_recent_activity_empty_for_new_user(client: TestClient, db_session):
    """کاربر جدید بدون مشارکت، لیست خالی دریافت می‌کند."""
    token = create_access_token("user-recent-empty", "contributor")
    user = User(
        id="user-recent-empty",
        email="recent_empty@example.com",
        hashed_password="pw",
        full_name="کاربر بدون مشارکت",
        role="contributor",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    resp = client.get(
        "/api/v1/contribution/recent-activity",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json() == []

def test_recent_activity_returns_user_items_ordered(client: TestClient, db_session):
    """تأیید دریافت آخرین فعالیت‌های کاربر با مرتب‌سازی نزولی."""
    token = create_access_token("user-recent-active", "contributor")
    user = User(
        id="user-recent-active",
        email="recent_active@example.com",
        hashed_password="pw",
        full_name="کاربر فعال",
        role="contributor",
        is_active=True
    )
    db_session.add(user)

    # Add 3 submissions for this user
    sub1 = Submission(
        id="sub-act-1",
        submitter_id=user.id,
        source_title="منبع ۱",
        legal_document_name="قانون مدنی ماده ۱",
        raw_legal_text="متن تستی اول ماده قانون برای ثبت...",
        source_url="https://rc.majlis.ir/fa/law/show/1",
        source_domain="rc.majlis.ir",
        document_type="law",
        issuing_authority="مجلس شورای اسلامی",
        status="submitted",
        quality_score=90,
        awarded_credits=0
    )
    sub2 = Submission(
        id="sub-act-2",
        submitter_id=user.id,
        source_title="منبع ۲",
        legal_document_name="قانون تجارت ماده ۲",
        raw_legal_text="متن تستی دوم ماده قانون برای ثبت...",
        source_url="https://rc.majlis.ir/fa/law/show/2",
        source_domain="rc.majlis.ir",
        document_type="law",
        issuing_authority="مجلس شورای اسلامی",
        status="accepted",
        quality_score=95,
        awarded_credits=95
    )
    db_session.add_all([sub1, sub2])
    db_session.commit()

    resp = client.get(
        "/api/v1/contribution/recent-activity?limit=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    titles = [item["title"] for item in data]
    assert "قانون مدنی ماده ۱" in titles
    assert "قانون تجارت ماده ۲" in titles
    accepted_item = next(item for item in data if item["id"] == "sub-act-2")
    assert accepted_item["status"] == "accepted"
    assert accepted_item["awarded_credits"] == 95
