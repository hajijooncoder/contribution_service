"""
Authentication, RBAC Access Control, IDOR Prevention and Export Gateway Hardcore Test Suite.
تست‌های بشدت سخت‌گیرانه برای کنترل دسترسی نقش‌محور (RBAC)، جلوگیری از ترفیع غیرمجاز،
حفاظت در برابر حملات جعل شناسه شیء (IDOR)، توکن‌های دستکاری‌شده، لیمیت‌گذاری و گذرگاه خروجی ایزوله.
"""

from datetime import datetime, timedelta, timezone
import json
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from jose import jwt

from app.db.models import User, Submission, UploadedFile
from app.core.security import UserRole, get_password_hash, create_access_token
from app.config import settings
from app.core.rate_limiter import global_rate_limiter


# ==============================================================================
# ۱. تست‌های امنیت ثبت‌نام و منع ترفیع نقش (Registration & Privilege Escalation)
# ==============================================================================

def test_registration_forbids_extra_fields_including_role(client: TestClient):
    """تلاش برای ارسال فیلدهای غیرمجاز مانند role: admin در بدنه ثبت‌نام باید با خطای ۴۲۲ متوقف شود."""
    hostile_payload = {
        "email": "hacker_admin@example.com",
        "password": "StrongPassword123",
        "full_name": "مهاجم ترفیع نقش",
        "role": "admin",  # فیلد تزریقی غیرمجاز
    }
    resp = client.post("/api/v1/auth/register", json=hostile_payload)
    assert resp.status_code == 422  # Extra fields forbidden via ConfigDict(extra="forbid")


def test_registration_forbids_credits_injection(client: TestClient):
    """تلاش برای دستکاری و تزریق total_credits در زمان ثبت‌نام باید رد شود."""
    hostile_payload = {
        "email": "hacker_credits@example.com",
        "password": "StrongPassword123",
        "full_name": "مهاجم اعتبار",
        "total_credits": 1000000,
    }
    resp = client.post("/api/v1/auth/register", json=hostile_payload)
    assert resp.status_code == 422


def test_registration_duplicate_email_blocked(client: TestClient, db_session: Session):
    """ثبت‌نام با ایمیل تکراری باید خطای ۴۰۰ بازگرداند."""
    email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    payload = {"email": email, "password": "Password123", "full_name": "کاربر اول"}
    resp1 = client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"]


# ==============================================================================
# ۲. تست‌های نفوذ توکن JWT و جعل امضا (JWT Tampering & Signature Attacks)
# ==============================================================================

def test_tampered_jwt_signature_rejected(client: TestClient):
    """توکن امضا شده با کلید نامعتبر یا تغییر داده شده باید خطای ۴۰۱ دریافت کند."""
    # جعل توکن با کلید مخرب
    fake_token = jwt.encode(
        {"sub": str(uuid.uuid4()), "role": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "stolen-or-fake-secret-key-123456789",
        algorithm="HS256"
    )
    headers = {"Authorization": f"Bearer {fake_token}"}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401
    assert "Invalid or expired" in resp.json()["detail"]


def test_expired_jwt_token_rejected(client: TestClient, contributor_user):
    """توکن منقضی شده (Expired) باید بلافاصله رد شود."""
    expired_token = create_access_token(
        subject=contributor_user.id,
        role=contributor_user.role,
        expires_delta=timedelta(seconds=-30)  # منقضی در گذشته
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401


def test_token_missing_subject_claim(client: TestClient):
    """توکنی که کلیم sub (شناسه کاربر) ندارد نامعتبر است."""
    bad_token = jwt.encode(
        {"role": "contributor", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    headers = {"Authorization": f"Bearer {bad_token}"}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401


def test_deactivated_user_token_blocked(client: TestClient, db_session: Session):
    """اگر حساب کاربر غیرفعال شود (is_active=False)، توکن قبلی او باید بی‌اثر و مسدود گردد."""
    user = User(
        id=str(uuid.uuid4()),
        email=f"deact_{uuid.uuid4().hex[:6]}@test.com",
        hashed_password=get_password_hash("pass123"),
        full_name="کاربر معلق",
        role=UserRole.CONTRIBUTOR,
        is_active=False,  # حساب غیرفعال
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(subject=user.id, role=user.role)
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401


# ==============================================================================
# ۳. تست‌های کنترل دسترسی نقش‌محور (RBAC & Administrative Promotion)
# ==============================================================================

def test_only_admin_can_promote_roles(client: TestClient, db_session: Session, contributor_headers, reviewer_headers):
    """تغییر نقش کاربران صرفاً در انحصار کاربر Admin است؛ مشارکت‌کننده و داور رد می‌شوند."""
    target_user = User(
        id=str(uuid.uuid4()),
        email=f"target_{uuid.uuid4().hex[:6]}@test.com",
        hashed_password=get_password_hash("pass"),
        full_name="کاربر هدف",
        role=UserRole.CONTRIBUTOR,
        is_active=True,
    )
    db_session.add(target_user)
    db_session.commit()

    # ۱. مشارکت‌کننده تلاش می‌کند: ۴۰۳
    resp_c = client.put(
        f"/api/v1/auth/users/{target_user.id}/role",
        json={"role": "reviewer"},
        headers=contributor_headers
    )
    assert resp_c.status_code == 403

    # ۲. داور تلاش می‌کند: ۴۰۳
    resp_r = client.put(
        f"/api/v1/auth/users/{target_user.id}/role",
        json={"role": "admin"},
        headers=reviewer_headers
    )
    assert resp_r.status_code == 403

    # ۳. ادمین واقعی تغییر می‌دهد: ۲۰۰
    admin_user = User(
        id=str(uuid.uuid4()),
        email=f"admin_{uuid.uuid4().hex[:6]}@test.com",
        hashed_password=get_password_hash("adminPass"),
        full_name="مدیر سیستم",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin_user)
    db_session.commit()

    admin_token = create_access_token(subject=admin_user.id, role=admin_user.role)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    resp_a = client.put(
        f"/api/v1/auth/users/{target_user.id}/role",
        json={"role": "reviewer"},
        headers=admin_headers
    )
    assert resp_a.status_code == 200
    assert resp_a.json()["role"] == "reviewer"


def test_admin_cannot_assign_invalid_role(client: TestClient, db_session: Session):
    """ادمین هم نمی‌تواند نقشی خارج از لیست مجاز (contributor/reviewer/admin) انتساب دهد."""
    admin = User(
        id=str(uuid.uuid4()),
        email=f"adm_{uuid.uuid4().hex[:6]}@test.com",
        hashed_password="p",
        full_name="ادمین",
        role=UserRole.ADMIN,
        is_active=True,
    )
    target = User(
        id=str(uuid.uuid4()),
        email=f"tgt_{uuid.uuid4().hex[:6]}@test.com",
        hashed_password="p",
        full_name="هدف",
        role=UserRole.CONTRIBUTOR,
        is_active=True,
    )
    db_session.add_all([admin, target])
    db_session.commit()

    adm_token = create_access_token(subject=admin.id, role=admin.role)
    resp = client.put(
        f"/api/v1/auth/users/{target.id}/role",
        json={"role": "super_root_overlord"},
        headers={"Authorization": f"Bearer {adm_token}"}
    )
    assert resp.status_code == 400
    assert "نقش نامعتبر است" in resp.json()["detail"]


# ==============================================================================
# ۴. تست‌های ایزولاسیون و جلوگیری از نشت داده بین کاربران (IDOR Prevention)
# ==============================================================================

def test_idor_submission_status_isolation(client: TestClient, db_session: Session):
    """
    بررسی عدم نشت اطلاعات سند به سایر مشارکت‌کنندگان (IDOR):
    تنها خود نویسنده، داوران و ادمین حق دیدن جزییات سند را دارند.
    سایر کاربران عادی باید خطای ۴۰۳ دریافت کنند.
    """
    user_alice = User(id=str(uuid.uuid4()), email="alice@test.ir", hashed_password="h", full_name="آلیس", role=UserRole.CONTRIBUTOR, is_active=True)
    user_bob = User(id=str(uuid.uuid4()), email="bob@test.ir", hashed_password="h", full_name="باب", role=UserRole.CONTRIBUTOR, is_active=True)
    db_session.add_all([user_alice, user_bob])
    db_session.commit()

    sub_alice = Submission(
        id=str(uuid.uuid4()),
        submitter_id=user_alice.id,
        source_title="سند شخصی آلیس",
        legal_document_name="ماده اختصاصی آلیس",
        raw_legal_text="متن محرمانه مشارکت آلیس",
        source_url="https://rooznamehrasmi.ir/test",
        source_domain="روزنامه رسمی",
        document_type="law",
        issuing_authority="مجلس",
        status="submitted",
    )
    db_session.add(sub_alice)
    db_session.commit()

    bob_token = create_access_token(subject=user_bob.id, role=user_bob.role)
    alice_token = create_access_token(subject=user_alice.id, role=user_alice.role)

    # ۱. باب تلاش می‌کند سند آلیس را بخواند: ۴۰۳
    resp_bob = client.get(f"/api/v1/contribution/status/{sub_alice.id}", headers={"Authorization": f"Bearer {bob_token}"})
    assert resp_bob.status_code == 403
    assert "مجاز به مشاهده جزئیات این مشارکت نیستید" in resp_bob.json()["detail"]

    # ۲. آلیس خودش می‌خواند: ۲۰۰
    resp_alice = client.get(f"/api/v1/contribution/status/{sub_alice.id}", headers={"Authorization": f"Bearer {alice_token}"})
    assert resp_alice.status_code == 200
    assert resp_alice.json()["id"] == sub_alice.id


def test_history_strictly_isolates_records(client: TestClient, db_session: Session):
    """تاریخچه ارسالی‌ها (/contribution/history) فقط اسناد خود کاربر احراز هویت شده را بازمی‌گرداند."""
    u1 = User(id=str(uuid.uuid4()), email="hist_u1@test.com", hashed_password="h", full_name="کاربر یک", role=UserRole.CONTRIBUTOR, is_active=True)
    u2 = User(id=str(uuid.uuid4()), email="hist_u2@test.com", hashed_password="h", full_name="کاربر دو", role=UserRole.CONTRIBUTOR, is_active=True)
    db_session.add_all([u1, u2])
    db_session.commit()

    for i in range(3):
        db_session.add(Submission(
            id=str(uuid.uuid4()),
            submitter_id=u1.id,
            source_title=f"سند کاربر ۱ - {i}",
            legal_document_name=f"قانون ۱-{i}",
            raw_legal_text="متن",
            source_url="https://qavanin.ir/1",
            source_domain="قوانین",
            issuing_authority="مجلس",
            status="submitted",
        ))

    db_session.add(Submission(
        id=str(uuid.uuid4()),
        submitter_id=u2.id,
        source_title="سند کاربر ۲",
        legal_document_name="قانون ۲",
        raw_legal_text="متن",
        source_url="https://qavanin.ir/2",
        source_domain="قوانین",
        issuing_authority="مجلس",
        status="submitted",
    ))
    db_session.commit()

    t1 = create_access_token(subject=u1.id, role=u1.role)
    t2 = create_access_token(subject=u2.id, role=u2.role)

    resp1 = client.get("/api/v1/contribution/history", headers={"Authorization": f"Bearer {t1}"})
    assert resp1.status_code == 200
    assert len(resp1.json()) == 3

    resp2 = client.get("/api/v1/contribution/history", headers={"Authorization": f"Bearer {t2}"})
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1


# ==============================================================================
# ۵. تست‌های گذرگاه خروجی ایزوله (Pull Export Gateway Security)
# ==============================================================================

def test_export_pull_gateway_strictly_rejects_unauthorized_token(client: TestClient):
    """گذرگاه خروج داده (/internal/export/...) دسترسی بدون توکن اختصاصی گیت‌وی را اکیداً رد می‌کند."""
    # بدون هیچ هدر
    resp1 = client.get("/api/v1/internal/export/approved-packages")
    assert resp1.status_code == 403

    # با هدر توکن اشتباه
    resp2 = client.get(
        "/api/v1/internal/export/approved-packages",
        headers={"X-Gateway-Token": "completely-wrong-gateway-token"}
    )
    assert resp2.status_code == 403
    assert "Invalid export gateway token" in resp2.json()["detail"]


def test_export_pull_gateway_accepts_valid_header_or_bearer(client: TestClient):
    """پشتیبانی از هر دو فرمت X-Gateway-Token و Authorization: Bearer <GATEWAY_TOKEN>."""
    valid_token = settings.EXPORT_GATEWAY_TOKEN

    # با هدر اختصاصی
    resp1 = client.get(
        "/api/v1/internal/export/approved-packages",
        headers={"X-Gateway-Token": valid_token}
    )
    assert resp1.status_code == 200

    # با بیرر توکن استاندارد
    resp2 = client.get(
        "/api/v1/internal/export/approved-packages",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert resp2.status_code == 200


def test_mark_ingested_transitions_submission_status(client: TestClient, db_session: Session):
    """فراخوانی mark-ingested توسط هسته پردازشی، وضعیت سند را به in_processing ارتقا می‌دهد."""
    sub = Submission(
        id=str(uuid.uuid4()),
        submitter_id=str(uuid.uuid4()),
        source_title="سند برای انتقال به هسته مرکزی",
        legal_document_name="قانون نهایی",
        raw_legal_text="متن تایید شده",
        source_url="https://rooznamehrasmi.ir/final",
        source_domain="روزنامه رسمی",
        document_type="law",
        issuing_authority="مجلس",
        status="accepted",
    )
    db_session.add(sub)
    db_session.commit()

    headers = {"X-Gateway-Token": settings.EXPORT_GATEWAY_TOKEN}
    resp = client.post(f"/api/v1/internal/export/mark-ingested/{sub.id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["new_status"] == "in_processing"

    db_session.refresh(sub)
    assert sub.status == "in_processing"


def test_download_quarantined_file_via_gateway(client: TestClient, db_session: Session, tmp_path):
    """دانلود مستقیم فایل قرنطینه شده توسط گیت‌وی به همراه هدرهای اعتبارسنجی SHA-256."""
    fake_file_path = tmp_path / "quarantined_doc.txt"
    file_bytes = "متن قانونی رسمی داخل فایل پیوست".encode("utf-8")
    fake_file_path.write_bytes(file_bytes)
    import hashlib
    sha = hashlib.sha256(file_bytes).hexdigest()

    uploaded = UploadedFile(
        id=str(uuid.uuid4()),
        submitter_id=str(uuid.uuid4()),
        original_filename="official_doc.txt",
        stored_filename="stored_doc.txt",
        storage_path=str(fake_file_path),
        file_size=len(file_bytes),
        sha256_hash=sha,
        detected_mime="text/plain",
        quarantine_status="quarantined_verified",
    )
    db_session.add(uploaded)
    db_session.commit()

    headers = {"X-Gateway-Token": settings.EXPORT_GATEWAY_TOKEN}
    resp = client.get(f"/api/v1/internal/export/package-file/{uploaded.id}", headers=headers)
    assert resp.status_code == 200
    assert resp.content == file_bytes
    assert resp.headers["x-content-sha256"] == sha
    assert resp.headers["x-original-filename"] == "official_doc.txt"
