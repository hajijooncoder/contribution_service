"""
End-to-End Lifecycle and System Integrity Hardcore Test Suite.
تست‌های بشدت سخت‌گیرانه، جامع و سرتاسری برای راستی‌آزمایی چرخه کامل مشارکت داده‌های حقوقی:
از ثبت کاربر و آپلود فایل قرنطینه تا پیش‌نمایش و ارتقای متن، ثبت در استیجینگ، داوری دومرحله‌ای،
اعتبارسنجی زنجیره دفترکل، کشیدن بسته‌ها توسط گیت‌وی خروجی، بررسی تطابق SHA256 بایت‌به‌بایت و علامت‌گذاری نهایی.
"""

import hashlib
import json
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import User, Submission, UploadedFile, AuditLog
from app.core.security import UserRole, get_password_hash, create_access_token
from app.core.audit_ledger import CryptographicAuditLedger
from app.config import settings


def test_full_end_to_end_contribution_to_export_lifecycle(
    client: TestClient,
    db_session: Session,
):
    """
    سخت‌ترین و جامع‌ترین آزمون چرخه حیات سیستم (E2E):
    ۱. ثبت‌نام مشارکت‌کننده و ورود
    ۲. آپلود سند رسمی در قرنطینه و استخراج هش
    ۳. ثبت سند پرریسک (قانون) با ارجاع به فایل
    ۴. بررسی تاریخچه و آمار کاربری
    ۵. ممانعت از خودداوری
    ۶. داوری داور اول -> مرحله اول تایید
    ۷. عدم خروج سند تا قبل از تکمیل حدنصاب در گیت‌وی
    ۸. داوری داور دوم -> تکمیل حدنصاب، صدور مهر اصالت و تخصیص امتیاز
    ۹. دریافت بسته توسط گیت‌وی خروجی، راستی‌آزمایی هش ترانزیت و امضای چک‌پوینت
    ۱۰. دانلود خروجی‌های JSONL، TXT و استریم فایل پیوست از قرنطینه
    ۱۱. اعلام وصول توسط هسته پردازشی (mark-ingested)
    ۱۲. مسدود شدن داوری مجدد به دلیل وضعیت قطعی
    """
    # ۱. ثبت‌نام و دریافت توکن مشارکت‌کننده
    contributor_email = f"c_e2e_{uuid.uuid4().hex[:6]}@example.com"
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": contributor_email,
        "password": "ContributorPass123",
        "full_name": "پژوهشگر حقوقی نمونه",
    })
    assert reg_resp.status_code == 201
    contributor_id = reg_resp.json()["id"]

    login_resp = client.post("/api/v1/auth/token", json={
        "email": contributor_email,
        "password": "ContributorPass123",
    })
    assert login_resp.status_code == 200
    c_token = login_resp.json()["access_token"]
    c_headers = {"Authorization": f"Bearer {c_token}"}

    # ۲. آپلود فایل در قرنطینه
    legal_pdf_bytes = (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n120\n%%EOF\n"
    )
    upload_resp = client.post(
        "/api/v1/contribution/upload",
        files={"file": ("official_decree.pdf", legal_pdf_bytes, "application/pdf")},
        headers=c_headers,
    )
    assert upload_resp.status_code == 200
    file_id = upload_resp.json()["file_id"]

    # ۳. ثبت سند در استیجینگ با ارجاع رسمی به روزنامه رسمی کشور
    sub_payload = {
        "source_title": "قانون انتشار و دسترسی آزاد به اطلاعات",
        "legal_document_name": "ماده ۲ قانون دسترسی آزاد به اطلاعات - نسخ قوانین مغایر",
        "raw_legal_text": (
            "ماده ۲: هر شخص ایرانی حق دسترسی به اطلاعات عمومی را دارد مگر آن که قانون صریحاً منع کرده باشد. "
            "کلیه قوانین و مقررات مغایر با این حکم صریحاً نسخ و ملغی‌الاثر اعلام می‌گردد."
        ),
        "source_url": "https://rooznamehrasmi.ir/laws/show/access_info_law",
        "document_type": "law",
        "issuing_authority": "مجلس شورای اسلامی",
        "publication_info": "روزنامه رسمی شماره ۱۹۰۰۰",
        "contributor_notes": "تطبیق داده شده با نسخه منتشر شده",
        "file_upload_id": file_id,
    }
    submit_resp = client.post("/api/v1/contribution/submit", json=sub_payload, headers=c_headers)
    assert submit_resp.status_code == 201
    sub_data = submit_resp.json()
    sub_id = sub_data["id"]
    assert sub_data["required_reviewers"] == 2  # چون قانون و دارای کلمه نسخ است
    assert sub_data["status"] == "submitted"
    assert sub_data["quality_score"] > 80

    # ۴. بررسی تاریخچه و آمار کاربری
    history_resp = client.get("/api/v1/contribution/history", headers=c_headers)
    assert history_resp.status_code == 200
    history_items = history_resp.json()
    assert len(history_items) >= 1
    assert any(h["id"] == sub_id for h in history_items)

    stats_resp = client.get("/api/v1/contribution/stats", headers=c_headers)
    assert stats_resp.status_code == 200
    assert stats_resp.json()["pending_submissions"] >= 1

    # ۵. ایجاد دو داور مجزا در دیتابیس
    rev1 = User(
        id=str(uuid.uuid4()),
        email=f"rev1_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password=get_password_hash("rev1pass"),
        full_name="داور حقوقی اول",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    rev2 = User(
        id=str(uuid.uuid4()),
        email=f"rev2_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password=get_password_hash("rev2pass"),
        full_name="داور حقوقی دوم",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    db_session.add_all([rev1, rev2])
    db_session.commit()

    rev1_token = create_access_token(subject=rev1.id, role=rev1.role)
    rev2_token = create_access_token(subject=rev2.id, role=rev2.role)
    rev1_headers = {"Authorization": f"Bearer {rev1_token}"}
    rev2_headers = {"Authorization": f"Bearer {rev2_token}"}

    # مشارکت‌کننده سعی می‌کند به سند خودش نظر بدهد: باید ۴۰۰ شود
    self_review_resp = client.post("/api/v1/contribution/review/decision", json={
        "submission_id": sub_id,
        "decision": "approve",
        "reviewer_notes": "من خودم تایید می‌کنم",
    }, headers=c_headers)
    assert self_review_resp.status_code == 403  # کاربر عادی اصلاً دسترسی داوری ندارد

    # ۶. داور اول تایید می‌کند
    r1_vote_resp = client.post("/api/v1/contribution/review/decision", json={
        "submission_id": sub_id,
        "decision": "approve",
        "reviewer_notes": "تایید انطباق متن با روزنامه رسمی توسط داور اول",
    }, headers=rev1_headers)
    assert r1_vote_resp.status_code == 200
    assert r1_vote_resp.json()["new_status"] == "under_legal_review"

    # ۷. بررسی گیت‌وی خروجی قبل از تکمیل حدنصاب: سند نباید در خروجی باشد!
    gw_headers = {"X-Gateway-Token": settings.EXPORT_GATEWAY_TOKEN}
    gw_early_resp = client.get("/api/v1/internal/export/approved-packages", headers=gw_headers)
    assert gw_early_resp.status_code == 200
    early_pkg_ids = [p["manifest"]["submission_id"] for p in gw_early_resp.json()["packages"]]
    assert sub_id not in early_pkg_ids

    # ۸. داور دوم تایید می‌کند و حدنصاب حاصل می‌شود
    r2_vote_resp = client.post("/api/v1/contribution/review/decision", json={
        "submission_id": sub_id,
        "decision": "approve",
        "reviewer_notes": "تایید نهایی صحت و اعتبار توسط داور دوم",
    }, headers=rev2_headers)
    assert r2_vote_resp.status_code == 200
    assert r2_vote_resp.json()["new_status"] == "accepted"

    # بررسی وضعیت و درج مهر اصالت
    status_resp = client.get(f"/api/v1/contribution/status/{sub_id}", headers=c_headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "accepted"
    assert status_resp.json()["current_approvals"] == 2
    assert status_resp.json()["provenance_stamp"] is not None

    stamp = json.loads(status_resp.json()["provenance_stamp"])
    assert stamp["source_type"] == "COMMUNITY_CONTRIBUTION"
    assert stamp["quorum_size"] == 2
    assert sorted(stamp["verified_by"]) == sorted([rev1.id, rev2.id])

    # ۹. دریافت بسته از گیت‌وی خروجی و راستی‌آزمایی هش ترانزیت
    gw_resp = client.get("/api/v1/internal/export/approved-packages", headers=gw_headers)
    assert gw_resp.status_code == 200
    packages = gw_resp.json()["packages"]
    target_package = next((p for p in packages if p["manifest"]["submission_id"] == sub_id), None)
    assert target_package is not None

    # بررسی راستی‌آزمایی هش ترانزیت
    manifest_bytes = json.dumps(target_package["manifest"], sort_keys=True).encode("utf-8")
    expected_transit_hash = hashlib.sha256(manifest_bytes).hexdigest()
    assert target_package["staging_transit_sha256"] == expected_transit_hash

    # ۱۰. دریافت فایل‌های خروجی دیتاست
    # خروجی JSONL
    jsonl_resp = client.get("/api/v1/internal/export/dataset.jsonl", headers=gw_headers)
    assert jsonl_resp.status_code == 200
    jsonl_lines = [json.loads(line) for line in jsonl_resp.text.strip().split("\n") if line.strip()]
    assert any(item["id"] == sub_id for item in jsonl_lines)

    # خروجی TXT
    txt_resp = client.get("/api/v1/internal/export/dataset.txt", headers=gw_headers)
    assert txt_resp.status_code == 200
    assert sub_id in txt_resp.text
    assert "ماده ۲ قانون دسترسی آزاد به اطلاعات" in txt_resp.text

    # استریم فایل پیوست از قرنطینه
    file_dl_resp = client.get(f"/api/v1/internal/export/package-file/{file_id}", headers=gw_headers)
    assert file_dl_resp.status_code == 200
    assert file_dl_resp.content == legal_pdf_bytes
    assert file_dl_resp.headers["x-content-sha256"] == hashlib.sha256(legal_pdf_bytes).hexdigest()

    # ۱۱. اعلام وصول توسط هسته داخلی (mark-ingested)
    mark_resp = client.post(f"/api/v1/internal/export/mark-ingested/{sub_id}", headers=gw_headers)
    assert mark_resp.status_code == 200
    assert mark_resp.json()["new_status"] == "in_processing"

    # ۱۲. الف) داور اول تلاش می‌کند مجدداً رای دهد -> خطای داوری تکراری
    repeat_review = client.post("/api/v1/contribution/review/decision", json={
        "submission_id": sub_id,
        "decision": "reject",
        "reviewer_notes": "تلاش برای رای دوباره",
    }, headers=rev1_headers)
    assert repeat_review.status_code == 400
    assert "داوری تکراری" in repeat_review.json()["detail"]

    # ۱۲. ب) یک داور سوم (جدید) تلاش می‌کند سند پردازش‌شده را تغییر وضعیت دهد -> خطای وضعیت قطعی
    rev3 = User(
        id=str(uuid.uuid4()),
        email=f"rev3_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password=get_password_hash("rev3pass"),
        full_name="داور حقوقی سوم",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    db_session.add(rev3)
    db_session.commit()
    rev3_token = create_access_token(subject=rev3.id, role=rev3.role)
    rev3_headers = {"Authorization": f"Bearer {rev3_token}"}

    late_review = client.post("/api/v1/contribution/review/decision", json={
        "submission_id": sub_id,
        "decision": "reject",
        "reviewer_notes": "تلاش برای رد بعد از خروج توسط داور جدید",
    }, headers=rev3_headers)
    assert late_review.status_code == 400
    assert "تغییر وضعیت ناممکن است" in late_review.json()["detail"]


def test_enhanced_submission_api_flow(client: TestClient, contributor_headers):
    """
    تست گردش کار ثبت پیشرفته سند (/submit/enhanced):
    ۱. حالت پیش‌نمایش (Preview): بازگرداندن تغییرات املایی، فراداده و نمره کیفیت بدون ثبت نهایی
    ۲. حالت ثبت قطعی با force_submit: ذخیره‌سازی داده‌های استخراج شده در پایگاه‌داده
    """
    rich_legal_text = (
        "ماده ۱۰: قراردادهاي خصوصي نسبت به كساني كه آن را منعقد نموده اند در صورتي كه مخالف صريح قانون نباشد نافذ است.\n"
        "تبصره: طرفين مكلف به ايفاي تعهدات مي‌باشند."
    )
    req_payload = {
        "source_title": "قانون مدنی اصل آزادی قراردادها",
        "legal_document_name": "ماده ۱۰ قانون مدنی",
        "raw_legal_text": rich_legal_text,
        "source_url": "https://rc.majlis.ir/fa/law/show/article10",
        "document_type": "law",
        "issuing_authority": "مجلس شورای اسلامی",
        "skip_enhancement": False,
        "force_submit": False,  # ابتدا در حالت پیش‌نمایش
    }

    # ۱. پیش‌نمایش
    prev_resp = client.post("/api/v1/contribution/submit/enhanced", json=req_payload, headers=contributor_headers)
    assert prev_resp.status_code == 200
    prev_data = prev_resp.json()
    assert prev_data["status"] == "preview"
    assert prev_data["enhanced_preview"] is not None
    assert prev_data["enhanced_preview"]["quality_score"] > 0
    assert prev_data["enhanced_preview"]["changes_count"] > 0

    # ۲. ثبت نهایی
    req_payload["force_submit"] = True
    submit_resp = client.post("/api/v1/contribution/submit/enhanced", json=req_payload, headers=contributor_headers)
    assert submit_resp.status_code == 200
    submit_data = submit_resp.json()
    assert submit_data["status"] == "submitted"
    assert submit_data["submission_id"] is not None


def test_health_check_isolation_verified(client: TestClient):
    """بررسی سلامت سرویس و تأیید ایزولاسیون کامل استیجینگ."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "contribution_service"
    assert data["isolation_verified"] is True
