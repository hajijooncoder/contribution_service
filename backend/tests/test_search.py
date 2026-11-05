import pytest
from fastapi.testclient import TestClient
from app.db.models import Submission, User
from app.core.security import create_access_token

def test_search_unauthorized(client: TestClient):
    """انکار دسترسی به جستجو بدون توکن معتبر."""
    resp = client.get("/api/v1/contribution/search?q=قانون")
    assert resp.status_code == 401

def test_search_empty_database(client: TestClient, db_session):
    """پایگاه داده خالی نتیجه با total=0 برمی‌گرداند."""
    token = create_access_token("user-search-empty", "contributor")
    user = User(
        id="user-search-empty",
        email="empty_search@example.com",
        hashed_password="pw",
        full_name="کاربر جستجو",
        role="contributor",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    resp = client.get(
        "/api/v1/contribution/search",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["skip"] == 0
    assert data["limit"] == 20

def test_search_filters_and_text_match(client: TestClient, db_session):
    """تست فیلترها و جستجوی متنی بر روی عنوان، متن و مرجع تصویب."""
    user = User(
        id="user-search-1",
        email="search1@example.com",
        hashed_password="pw",
        full_name="پژوهشگر حقوقی",
        role="contributor",
        is_active=True
    )
    db_session.add(user)

    sub1 = Submission(
        id="sub-s-1",
        submitter_id=user.id,
        source_title="روزنامه رسمی",
        legal_document_name="قانون تجارت الکترونیکی",
        raw_legal_text="ماده ۱: کلیه اسناد دیجیتال معتبر است...",
        source_url="https://rrk.ir/laws/show/1",
        source_domain="rrk.ir",
        document_type="law",
        issuing_authority="مجلس شورای اسلامی",
        status="submitted",
        quality_score=95,
        awarded_credits=10
    )
    sub2 = Submission(
        id="sub-s-2",
        submitter_id=user.id,
        source_title="پایگاه قوانین",
        legal_document_name="آیین‌نامه اجرایی ثبت شرکت‌ها",
        raw_legal_text="ماده ۵: ثبت شرکت سهامی با امضای دیجیتال ممکن است...",
        source_url="https://qavanin.ir/law/2",
        source_domain="qavanin.ir",
        document_type="regulation",
        issuing_authority="هیئت وزیران",
        status="accepted",
        quality_score=88,
        awarded_credits=25
    )
    sub3 = Submission(
        id="sub-s-3",
        submitter_id=user.id,
        source_title="سامانه آرا",
        legal_document_name="رأی وحدت رویه دیوان عالی کشور",
        raw_legal_text="در خصوص حدود مسئولیت متصدی حمل و نقل دریایی...",
        source_url="https://ara.jri.ac.ir/judgment/3",
        source_domain="ara.jri.ac.ir",
        document_type="judicial_ruling",
        issuing_authority="دیوان عالی کشور",
        status="rejected",
        quality_score=60,
        awarded_credits=0
    )
    db_session.add_all([sub1, sub2, sub3])
    db_session.commit()

    token = create_access_token(user.id, "contributor")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Search by text "تجارت"
    r = client.get("/api/v1/contribution/search?q=تجارت", headers=headers)
    assert r.status_code == 200
    res = r.json()
    assert res["total"] == 1
    assert res["items"][0]["id"] == "sub-s-1"

    # 2. Search by text "دیجیتال" (present in text of sub1 and sub2)
    r = client.get("/api/v1/contribution/search?q=دیجیتال", headers=headers)
    assert r.status_code == 200
    res = r.json()
    assert res["total"] == 2

    # 3. Filter by document_type "regulation"
    r = client.get("/api/v1/contribution/search?document_type=regulation", headers=headers)
    assert r.status_code == 200
    res = r.json()
    assert res["total"] == 1
    assert res["items"][0]["id"] == "sub-s-2"

    # 4. Filter by issuing_authority "دیوان عالی کشور"
    r = client.get("/api/v1/contribution/search?issuing_authority=دیوان", headers=headers)
    assert r.status_code == 200
    res = r.json()
    assert res["total"] == 1
    assert res["items"][0]["id"] == "sub-s-3"

    # 5. Filter by status "accepted"
    r = client.get("/api/v1/contribution/search?status_filter=accepted", headers=headers)
    assert r.status_code == 200
    res = r.json()
    assert res["total"] == 1
    assert res["items"][0]["id"] == "sub-s-2"

def test_search_role_isolation(client: TestClient, db_session):
    """
    کاربر عادی فقط مشارکت‌های خود را می‌بیند.
    داور (Reviewer) یا مدیر (Admin) به تمام مشارکت‌ها دسترسی دارند.
    """
    user_a = User(
        id="user-a",
        email="usera@example.com",
        hashed_password="pw",
        full_name="کاربر الف",
        role="contributor",
        is_active=True
    )
    user_b = User(
        id="user-b",
        email="userb@example.com",
        hashed_password="pw",
        full_name="کاربر ب",
        role="contributor",
        is_active=True
    )
    reviewer = User(
        id="user-rev",
        email="rev@example.com",
        hashed_password="pw",
        full_name="داور ارشد",
        role="reviewer",
        is_active=True
    )
    db_session.add_all([user_a, user_b, reviewer])

    sub_a = Submission(
        id="sub-a",
        submitter_id=user_a.id,
        source_title="مستند الف",
        legal_document_name="قانون مالیات‌های مستقیم",
        raw_legal_text="متن مالیاتی...",
        source_url="https://rc.majlis.ir/law/10",
        source_domain="rc.majlis.ir",
        document_type="law",
        issuing_authority="مجلس شورای اسلامی",
        status="submitted"
    )
    sub_b = Submission(
        id="sub-b",
        submitter_id=user_b.id,
        source_title="مستند ب",
        legal_document_name="قانون کار جمهوری اسلامی",
        raw_legal_text="متن قانون کار...",
        source_url="https://rc.majlis.ir/law/20",
        source_domain="rc.majlis.ir",
        document_type="law",
        issuing_authority="مجلس شورای اسلامی",
        status="submitted"
    )
    db_session.add_all([sub_a, sub_b])
    db_session.commit()

    token_a = create_access_token(user_a.id, "contributor")
    token_rev = create_access_token(reviewer.id, "reviewer")

    # User A searches: sees only sub_a
    r_a = client.get("/api/v1/contribution/search", headers={"Authorization": f"Bearer {token_a}"})
    assert r_a.status_code == 200
    res_a = r_a.json()
    assert res_a["total"] == 1
    assert res_a["items"][0]["id"] == "sub-a"

    # Reviewer searches: sees both sub_a and sub_b (and any other submissions in system)
    r_rev = client.get("/api/v1/contribution/search", headers={"Authorization": f"Bearer {token_rev}"})
    assert r_rev.status_code == 200
    res_rev = r_rev.json()
    assert res_rev["total"] >= 2
    ids = [item["id"] for item in res_rev["items"]]
    assert "sub-a" in ids
    assert "sub-b" in ids

def test_search_pagination(client: TestClient, db_session):
    """تست صفحه‌بندی با پارامترهای skip و limit."""
    user = User(
        id="user-pages",
        email="pages@example.com",
        hashed_password="pw",
        full_name="کاربر تست صفحات",
        role="contributor",
        is_active=True
    )
    db_session.add(user)

    for i in range(5):
        sub = Submission(
            id=f"sub-pg-{i}",
            submitter_id=user.id,
            source_title=f"منبع {i}",
            legal_document_name=f"قانون شماره {i}",
            raw_legal_text=f"متن قانون شماره {i}...",
            source_url=f"https://rrk.ir/law/{i}",
            source_domain="rrk.ir",
            document_type="law",
            issuing_authority="مجلس شورای اسلامی",
            status="submitted"
        )
        db_session.add(sub)
    db_session.commit()

    token = create_access_token(user.id, "contributor")
    headers = {"Authorization": f"Bearer {token}"}

    # First page: limit 2
    r1 = client.get("/api/v1/contribution/search?skip=0&limit=2", headers=headers)
    assert r1.status_code == 200
    res1 = r1.json()
    assert res1["total"] == 5
    assert len(res1["items"]) == 2
    assert res1["skip"] == 0
    assert res1["limit"] == 2

    # Second page: skip 2, limit 2
    r2 = client.get("/api/v1/contribution/search?skip=2&limit=2", headers=headers)
    assert r2.status_code == 200
    res2 = r2.json()
    assert res2["total"] == 5
    assert len(res2["items"]) == 2
    assert res2["items"][0]["id"] != res1["items"][0]["id"]
