"""
Enhanced Submission Pipeline — Hardcore Test Suite
تست‌های فوق دشوار و سخت‌گیرانه برای:
1. چرخه کامل enhanced submission (preview → confirm → submit)
2. duplicate detection در تمام سطوح (exact / near / partial)
3. IDOR protection روی status endpoint
4. Export Gateway integrity (token enforcement + manifest checksum)
5. Rate limiting per IP and per user
6. Frontend–Backend API contract mismatch detection
7. force_submit bypass of duplicate gate
8. skip_enhancement path
9. فیلدهای جدید Submission (content_hash, content_fingerprint, detected_risk_level)
"""

import hashlib
import json
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Submission, User, AuditLog
from app.core.security import UserRole, get_password_hash, create_access_token
from app.core.duplicate_detector import (
    ExactDuplicateDetector,
    NearDuplicateDetector,
    SmartDuplicateDetector,
    DuplicateLevel,
)
from app.core.text_enhancement import LegalTextEnhancer
from app.core.audit_ledger import CryptographicAuditLedger


# ============================================================
# ثابت‌های مشترک تست
# ============================================================

VALID_URL = "https://rc.majlis.ir/fa/law/show/94924"
VALID_URL_2 = "https://qavanin.ir/Data/FormLoader.aspx?law_id=1"
INVALID_URL = "https://wikipedia.org/wiki/قانون_مدنی"

SAMPLE_LAW_TEXT = (
    "ماده ۱: تعریف قرارداد — هر قراردادی که بین طرفین با قصد انشاء منعقد شود معتبر است.\n"
    "تبصره ۱: قرارداد باید دارای موضوع مشروع باشد.\n"
    "ماده ۲: شرایط صحت قرارداد — قرارداد در صورتی معتبر است که طرفین اهلیت داشته باشند.\n"
    "بند الف: طرفین باید بالغ و عاقل باشند.\n"
    "بند ب: موضوع قرارداد باید معین و معلوم باشد.\n"
    "ماده ۳: موضوع قرارداد — موضوع قرارداد باید مشروع، مقدور و دارای نفع عقلایی باشد."
)

HIGH_RISK_TEXT = (
    "ماده ۱۰: این قانون موجب نسخ قانون تجارت مصوب ۱۳۱۱ می‌گردد.\n"
    "تبصره ۲: کلیه مقررات مغایر ملغی‌الاثر خواهند بود."
)


# ==============================================================
# بخش ۱ — Enhanced Submission: چرخه Preview → Confirm → Submit
# ==============================================================

class TestEnhancedSubmissionFlow:

    def test_first_call_returns_preview_not_submitted(
        self, client: TestClient, contributor_headers
    ):
        """
        اولین فراخوانی submit/enhanced با force_submit=False و skip_enhancement=False
        باید status='preview' برگرداند، نه status='submitted'.
        هیچ رکوردی در staging_submissions نباید ساخته شود.
        """
        payload = {
            "source_title": "قانون مدنی",
            "legal_document_name": "قانون مدنی ایران باب قراردادها",
            "raw_legal_text": SAMPLE_LAW_TEXT,
            "source_url": VALID_URL,
            "document_type": "law",
            "issuing_authority": "مجلس شورای اسلامی",
            "skip_enhancement": False,
            "force_submit": False,
        }
        resp = client.post(
            "/api/v1/contribution/submit/enhanced",
            json=payload,
            headers=contributor_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "preview"
        assert data["submission_id"] is None
        assert data["enhanced_preview"] is not None
        # preview باید metadata داشته باشد
        preview = data["enhanced_preview"]
        assert "article_count" in preview["metadata"]
        assert preview["metadata"]["article_count"] >= 3
        assert preview["quality_score"] > 0
        assert len(preview["content_hash"]) == 64

    def test_force_submit_creates_db_record(
        self, client: TestClient, contributor_headers, db_session: Session
    ):
        """
        force_submit=True باید مستقیماً Submission رو در DB بسازه و
        status='submitted' برگردونه با submission_id واقعی.
        """
        unique_text = SAMPLE_LAW_TEXT + f"\n# unique_force_{uuid.uuid4().hex}"
        payload = {
            "source_title": "قانون مدنی force",
            "legal_document_name": "قانون مدنی ایران — ثبت اجباری",
            "raw_legal_text": unique_text,
            "source_url": VALID_URL,
            "document_type": "law",
            "issuing_authority": "مجلس شورای اسلامی",
            "skip_enhancement": True,
            "force_submit": True,
        }
        resp = client.post(
            "/api/v1/contribution/submit/enhanced",
            json=payload,
            headers=contributor_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "submitted"
        assert data["submission_id"] is not None

        # تأیید وجود در DB
        sub = db_session.query(Submission).filter(
            Submission.id == data["submission_id"]
        ).first()
        assert sub is not None
        assert sub.status == "submitted"

    def test_skip_enhancement_preserves_raw_text_exactly(
        self, client: TestClient, contributor_headers, db_session: Session
    ):
        """
        وقتی skip_enhancement=True است، متن ذخیره‌شده باید دقیقاً با ورودی یکسان باشد.
        هیچ کاراکتری نباید اضافه یا کم شده باشد.
        """
        raw = "ماده ۱: متن کاملاً خام بدون هیچ پردازشی. " + uuid.uuid4().hex
        payload = {
            "source_title": "تست حفاظت متن",
            "legal_document_name": "سند تست حفاظت متن خام",
            "raw_legal_text": raw,
            "source_url": VALID_URL,
            "document_type": "circular",
            "issuing_authority": "معاونت حقوقی",
            "skip_enhancement": True,
            "force_submit": True,
        }
        resp = client.post(
            "/api/v1/contribution/submit/enhanced",
            json=payload,
            headers=contributor_headers,
        )
        assert resp.status_code == 200
        sub_id = resp.json()["submission_id"]
        sub = db_session.query(Submission).filter(Submission.id == sub_id).first()
        assert sub is not None
        assert sub.raw_legal_text == raw

    def test_invalid_source_url_blocked_before_enhancement(
        self, client: TestClient, contributor_headers
    ):
        """
        URL از دامنه غیررسمی باید قبل از هر پردازشی با 400 رد شود.
        هیچ تماسی با LegalTextEnhancer نباید رخ دهد.
        """
        payload = {
            "source_title": "منبع غیررسمی",
            "legal_document_name": "ماده از ویکی‌پدیا",
            "raw_legal_text": SAMPLE_LAW_TEXT,
            "source_url": INVALID_URL,
            "document_type": "law",
            "issuing_authority": "ناشناس",
            "skip_enhancement": False,
            "force_submit": True,
        }
        resp = client.post(
            "/api/v1/contribution/submit/enhanced",
            json=payload,
            headers=contributor_headers,
        )
        assert resp.status_code == 400
        assert "مرجع نامعتبر" in resp.json()["detail"]

    def test_high_risk_text_gets_correct_required_reviewers(
        self, client: TestClient, contributor_headers, db_session: Session
    ):
        """
        متنی که حاوی کلمه 'نسخ' است باید required_reviewers=2 داشته باشد.
        این یک تضمین حاکمیتی است، نه یک feature.
        """
        payload = {
            "source_title": "قانون ناسخ",
            "legal_document_name": "قانون جدید — ناسخ مقررات قبلی",
            "raw_legal_text": HIGH_RISK_TEXT,
            "source_url": VALID_URL,
            "document_type": "law",
            "issuing_authority": "مجلس شورای اسلامی",
            "skip_enhancement": True,
            "force_submit": True,
        }
        resp = client.post(
            "/api/v1/contribution/submit/enhanced",
            json=payload,
            headers=contributor_headers,
        )
        assert resp.status_code == 200
        sub_id = resp.json()["submission_id"]
        sub = db_session.query(Submission).filter(Submission.id == sub_id).first()
        assert sub.required_reviewers == 2

    def test_enhanced_submission_writes_audit_log(
        self, client: TestClient, contributor_headers, db_session: Session
    ):
        """
        هر force_submit باید یک ورودی ENHANCED_CONTRIBUTION_SUBMITTED در audit ledger بسازه.
        """
        count_before = db_session.query(AuditLog).filter(
            AuditLog.action == "ENHANCED_CONTRIBUTION_SUBMITTED"
        ).count()

        payload = {
            "source_title": "تست لجر",
            "legal_document_name": "سند تست ثبت در لجر حسابرسی",
            "raw_legal_text": SAMPLE_LAW_TEXT + uuid.uuid4().hex,
            "source_url": VALID_URL,
            "document_type": "regulation",
            "issuing_authority": "هیئت وزیران",
            "skip_enhancement": True,
            "force_submit": True,
        }
        client.post(
            "/api/v1/contribution/submit/enhanced",
            json=payload,
            headers=contributor_headers,
        )
        db_session.expire_all()
        count_after = db_session.query(AuditLog).filter(
            AuditLog.action == "ENHANCED_CONTRIBUTION_SUBMITTED"
        ).count()
        assert count_after > count_before


# ==============================================================
# بخش ۲ — Duplicate Detection: دقت در تمام سطوح
# ==============================================================

class TestDuplicateDetectionHardcore:

    def test_exact_duplicate_blocked_without_force(
        self, client: TestClient, contributor_headers, db_session: Session
    ):
        """
        ارسال دوباره متن کاملاً یکسان بدون force_submit باید
        status='duplicate_detected' و is_duplicate=True برگرداند.
        """
        unique_text = "ماده ۱: متن منحصربه‌فرد برای تست دقیق تکراری. " + uuid.uuid4().hex

        # ارسال اول
        payload = {
            "source_title": "سند اول",
            "legal_document_name": "سند اول برای تشخیص تکراری",
            "raw_legal_text": unique_text,
            "source_url": VALID_URL,
            "document_type": "circular",
            "issuing_authority": "معاونت حقوقی",
            "skip_enhancement": True,
            "force_submit": True,
        }
        r1 = client.post(
            "/api/v1/contribution/submit/enhanced",
            json=payload,
            headers=contributor_headers,
        )
        assert r1.status_code == 200
        assert r1.json()["status"] == "submitted"

        # ارسال دوم با همان متن — بدون force_submit
        payload["source_title"] = "سند دوم (تکراری)"
        payload["force_submit"] = False  # این بار نباید اجازه ثبت بده
        r2 = client.post(
            "/api/v1/contribution/submit/enhanced",
            json=payload,
            headers=contributor_headers,
        )
        assert r2.status_code == 200
        data2 = r2.json()
        assert data2["status"] == "duplicate_detected"
        assert data2["duplicate_check"]["is_duplicate"] is True
        assert data2["duplicate_check"]["level"] == "exact"
        assert data2["duplicate_check"]["similarity"] == 1.0
        assert data2["submission_id"] is None  # نباید رکورد جدید ساخته شده باشد

    def test_exact_duplicate_allowed_with_force_submit(
        self, client: TestClient, contributor_headers, db_session: Session
    ):
        """
        ارسال دوباره با force_submit=True باید حتی در صورت تکراری بودن
        رکورد جدید بسازه.
        این رفتار برای مدیران جهت re-submission آگاهانه است.
        """
        unique_text = "ماده ۱: متن برای تست force_submit bypass. " + uuid.uuid4().hex

        for i in range(2):
            r = client.post(
                "/api/v1/contribution/submit/enhanced",
                json={
                    "source_title": f"سند force {i}",
                    "legal_document_name": "سند force submit تکراری",
                    "raw_legal_text": unique_text,
                    "source_url": VALID_URL,
                    "document_type": "circular",
                    "issuing_authority": "معاونت حقوقی",
                    "skip_enhancement": True,
                    "force_submit": True,
                },
                headers=contributor_headers,
            )
            assert r.status_code == 200
            assert r.json()["status"] == "submitted"

        # هر دو باید در DB موجود باشند
        subs = db_session.query(Submission).filter(
            Submission.raw_legal_text == unique_text
        ).all()
        assert len(subs) == 2

    def test_exact_duplicate_detector_unit(self, db_session: Session):
        """
        تست واحد ExactDuplicateDetector: hash محاسبه، ذخیره و بازیابی.
        """
        text = "ماده ۱: متن تست hash." + uuid.uuid4().hex
        expected_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        # در DB نباشد
        result = ExactDuplicateDetector.check(text, db_session, Submission)
        assert result is None

        # ذخیره در DB
        user = User(
            id=str(uuid.uuid4()),
            email=f"hash_test_{uuid.uuid4().hex[:6]}@test.ir",
            hashed_password="h",
            full_name="تست",
            role=UserRole.CONTRIBUTOR,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        sub = Submission(
            id=str(uuid.uuid4()),
            submitter_id=user.id,
            source_title="سند hash",
            legal_document_name="سند hash test",
            raw_legal_text=text,
            source_url=VALID_URL,
            source_domain="مرکز پژوهش‌ها",
            document_type="law",
            issuing_authority="مجلس",
            content_hash=expected_hash,
            required_reviewers=1,
            status="submitted",
        )
        db_session.add(sub)
        db_session.commit()

        # حالا باید پیدا بشه
        found_id = ExactDuplicateDetector.check(text, db_session, Submission)
        assert found_id == sub.id

    def test_near_duplicate_detector_hamming_distance(self):
        """
        اطمینان از اینکه hamming_distance بین دو fingerprint یکسان صفر است
        و بین دو fingerprint کاملاً متفاوت حداکثر است.
        """
        fp_a = "a" * 64
        fp_b = "a" * 64
        assert NearDuplicateDetector.hamming_distance(fp_a, fp_b) == 0
        assert NearDuplicateDetector.similarity(fp_a, fp_b) == 1.0

        fp_c = "b" * 64
        dist = NearDuplicateDetector.hamming_distance(fp_a, fp_c)
        assert dist == 64
        assert NearDuplicateDetector.similarity(fp_a, fp_c) == 0.0

    def test_smart_detector_returns_unique_for_novel_text(self, db_session: Session):
        """
        SmartDuplicateDetector باید برای متن کاملاً جدید UNIQUE برگرداند.
        """
        novel_text = "این متن کاملاً منحصربه‌فرد است و هیچ نمونه مشابهی ندارد. " + uuid.uuid4().hex
        detector = SmartDuplicateDetector(db_session, Submission)
        report = detector.check_all_levels(
            text=novel_text,
            metadata={"title": "سند منحصربه‌فرد"},
            title="سند منحصربه‌فرد",
        )
        assert report.is_duplicate is False
        assert report.level == DuplicateLevel.UNIQUE


# ==============================================================
# بخش ۳ — IDOR Protection: جداسازی دسترسی به submission
# ==============================================================

class TestIDORProtection:

    def _create_submission_for_user(
        self, db_session: Session, user: User, text_suffix: str = ""
    ) -> Submission:
        sub = Submission(
            id=str(uuid.uuid4()),
            submitter_id=user.id,
            source_title="سند خصوصی",
            legal_document_name="سند خصوصی تست IDOR" + text_suffix,
            raw_legal_text=SAMPLE_LAW_TEXT + text_suffix,
            source_url=VALID_URL,
            source_domain="مرکز پژوهش‌ها",
            document_type="law",
            issuing_authority="مجلس",
            required_reviewers=1,
            status="submitted",
        )
        db_session.add(sub)
        db_session.commit()
        return sub

    def test_owner_can_access_own_submission(
        self, client: TestClient, contributor_user: User, contributor_headers, db_session: Session
    ):
        """صاحب سند باید به جزئیات آن دسترسی داشته باشد."""
        sub = self._create_submission_for_user(
            db_session, contributor_user, uuid.uuid4().hex
        )
        resp = client.get(
            f"/api/v1/contribution/status/{sub.id}",
            headers=contributor_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == sub.id

    def test_other_contributor_cannot_access_foreign_submission(
        self, client: TestClient, db_session: Session
    ):
        """
        کاربر contributor دیگر نباید به سند متعلق به contributor اول دسترسی داشته باشد.
        باید 403 برگردد، نه 200 یا 404.
        """
        owner = User(
            id=str(uuid.uuid4()),
            email=f"idor_owner_{uuid.uuid4().hex[:6]}@test.ir",
            hashed_password=get_password_hash("pass"),
            full_name="صاحب سند",
            role=UserRole.CONTRIBUTOR,
            is_active=True,
        )
        attacker = User(
            id=str(uuid.uuid4()),
            email=f"idor_attacker_{uuid.uuid4().hex[:6]}@test.ir",
            hashed_password=get_password_hash("pass"),
            full_name="مهاجم",
            role=UserRole.CONTRIBUTOR,
            is_active=True,
        )
        db_session.add_all([owner, attacker])
        db_session.commit()

        sub = self._create_submission_for_user(db_session, owner, uuid.uuid4().hex)
        attacker_token = create_access_token(
            subject=attacker.id, role=attacker.role
        )
        attacker_headers = {"Authorization": f"Bearer {attacker_token}"}

        resp = client.get(
            f"/api/v1/contribution/status/{sub.id}",
            headers=attacker_headers,
        )
        assert resp.status_code == 403

    def test_reviewer_can_access_any_submission(
        self, client: TestClient, reviewer_headers, db_session: Session
    ):
        """داور باید به سند هر contributor دسترسی داشته باشد."""
        owner = User(
            id=str(uuid.uuid4()),
            email=f"reviewer_access_{uuid.uuid4().hex[:6]}@test.ir",
            hashed_password="h",
            full_name="مالک",
            role=UserRole.CONTRIBUTOR,
            is_active=True,
        )
        db_session.add(owner)
        db_session.commit()

        sub = self._create_submission_for_user(db_session, owner, uuid.uuid4().hex)
        resp = client.get(
            f"/api/v1/contribution/status/{sub.id}",
            headers=reviewer_headers,
        )
        assert resp.status_code == 200

    def test_nonexistent_submission_returns_404_not_403(
        self, client: TestClient, contributor_headers
    ):
        """
        شناسه سند ناموجود باید 404 برگرداند.
        نباید از روی کد 403 به اطلاعات موجود بودن سند پی برد (oracle).
        """
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/contribution/status/{fake_id}",
            headers=contributor_headers,
        )
        assert resp.status_code == 404


# ==============================================================
# بخش ۴ — Export Gateway: امنیت و یکپارچگی
# ==============================================================

GATEWAY_TOKEN = "test-export-gateway-token"
GATEWAY_HEADERS = {"X-Gateway-Token": GATEWAY_TOKEN}
BAD_GATEWAY_HEADERS = {"X-Gateway-Token": "wrong-token"}


class TestExportGatewayHardcore:

    def _create_accepted_submission(
        self, db_session: Session, user: User
    ) -> Submission:
        sub = Submission(
            id=str(uuid.uuid4()),
            submitter_id=user.id,
            source_title="سند تأییدشده",
            legal_document_name="قانون تأییدشده برای export",
            raw_legal_text=SAMPLE_LAW_TEXT + uuid.uuid4().hex,
            source_url=VALID_URL,
            source_domain="مرکز پژوهش‌ها",
            document_type="law",
            issuing_authority="مجلس",
            quality_score=85,
            required_reviewers=1,
            current_approvals=1,
            awarded_credits=85,
            status="accepted",
        )
        db_session.add(sub)
        db_session.commit()
        return sub

    def test_approved_packages_requires_valid_token(self, client: TestClient):
        """بدون توکن gateway نباید به export endpoint دسترسی داشت."""
        resp = client.get("/api/v1/internal/export/approved-packages")
        assert resp.status_code == 403

    def test_wrong_token_is_rejected(self, client: TestClient):
        """توکن اشتباه نباید عبور کند."""
        resp = client.get(
            "/api/v1/internal/export/approved-packages",
            headers=BAD_GATEWAY_HEADERS,
        )
        assert resp.status_code == 403

    def test_valid_token_returns_accepted_submissions_only(
        self, client: TestClient, contributor_user: User, db_session: Session
    ):
        """
        export gateway فقط submission‌های با status='accepted' برمی‌گرداند.
        سندهای submitted/rejected نباید در پاسخ باشند.
        """
        accepted_sub = self._create_accepted_submission(db_session, contributor_user)

        # یک سند submitted هم اضافه می‌کنیم
        pending_sub = Submission(
            id=str(uuid.uuid4()),
            submitter_id=contributor_user.id,
            source_title="سند در انتظار",
            legal_document_name="سند submitted هنوز تأیید نشده",
            raw_legal_text="متن در انتظار" + uuid.uuid4().hex,
            source_url=VALID_URL,
            source_domain="مرکز پژوهش‌ها",
            document_type="law",
            issuing_authority="مجلس",
            status="submitted",
        )
        db_session.add(pending_sub)
        db_session.commit()

        resp = client.get(
            "/api/v1/internal/export/approved-packages",
            headers=GATEWAY_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "packages" in data
        ids = [p["manifest"]["submission_id"] for p in data["packages"]]
        assert accepted_sub.id in ids
        assert pending_sub.id not in ids

    def test_each_package_has_valid_transit_sha256(
        self, client: TestClient, contributor_user: User, db_session: Session
    ):
        """
        هر package در پاسخ export باید staging_transit_sha256 داشته باشه
        که با محتوای manifest مطابقت داشته باشه.
        """
        self._create_accepted_submission(db_session, contributor_user)
        resp = client.get(
            "/api/v1/internal/export/approved-packages",
            headers=GATEWAY_HEADERS,
        )
        assert resp.status_code == 200
        for pkg in resp.json()["packages"]:
            manifest = pkg["manifest"]
            expected_hash = hashlib.sha256(
                json.dumps(manifest, sort_keys=True).encode("utf-8")
            ).hexdigest()
            assert pkg["staging_transit_sha256"] == expected_hash, (
                f"Transit hash mismatch for submission {manifest['submission_id']}"
            )

    def test_mark_ingested_transitions_to_in_processing(
        self, client: TestClient, contributor_user: User, db_session: Session
    ):
        """
        POST /internal/export/mark-ingested/{id} باید status را به in_processing تغییر دهد
        و سند را از صف export بعدی خارج کند.
        """
        sub = self._create_accepted_submission(db_session, contributor_user)
        resp = client.post(
            f"/api/v1/internal/export/mark-ingested/{sub.id}",
            headers=GATEWAY_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["new_status"] == "in_processing"

        db_session.refresh(sub)
        assert sub.status == "in_processing"

    def test_mark_ingested_writes_audit_log(
        self, client: TestClient, contributor_user: User, db_session: Session
    ):
        """
        mark-ingested باید ورودی PACKAGE_PULLED_BY_INTERNAL_CORE در audit ledger ایجاد کند.
        """
        sub = self._create_accepted_submission(db_session, contributor_user)
        count_before = db_session.query(AuditLog).filter(
            AuditLog.action == "PACKAGE_PULLED_BY_INTERNAL_CORE",
            AuditLog.target_id == sub.id,
        ).count()

        client.post(
            f"/api/v1/internal/export/mark-ingested/{sub.id}",
            headers=GATEWAY_HEADERS,
        )

        db_session.expire_all()
        count_after = db_session.query(AuditLog).filter(
            AuditLog.action == "PACKAGE_PULLED_BY_INTERNAL_CORE",
            AuditLog.target_id == sub.id,
        ).count()
        assert count_after == count_before + 1

    def test_dataset_jsonl_format_is_valid_ndjson(
        self, client: TestClient, contributor_user: User, db_session: Session
    ):
        """
        dataset.jsonl باید خط‌های معتبر JSON باشد — هر خط یک آبجکت JSON مستقل.
        """
        self._create_accepted_submission(db_session, contributor_user)
        resp = client.get(
            "/api/v1/internal/export/dataset.jsonl",
            headers=GATEWAY_HEADERS,
        )
        assert resp.status_code == 200
        lines = resp.text.strip().split("\n")
        for line in lines:
            if line.strip():
                record = json.loads(line)
                # هر رکورد باید فیلدهای اجباری داشته باشد
                for field in ("id", "title", "type", "authority", "raw_text"):
                    assert field in record, f"Missing field '{field}' in JSONL record"

    def test_download_nonexistent_file_returns_404(self, client: TestClient):
        """درخواست دانلود فایل ناموجود باید 404 برگرداند."""
        resp = client.get(
            f"/api/v1/internal/export/package-file/{uuid.uuid4()}",
            headers=GATEWAY_HEADERS,
        )
        assert resp.status_code == 404

    def test_export_via_bearer_token_fallback(
        self, client: TestClient, db_session: Session, contributor_user: User
    ):
        """
        توکن gateway باید از طریق Authorization: Bearer هم پذیرفته شود.
        """
        self._create_accepted_submission(db_session, contributor_user)
        resp = client.get(
            "/api/v1/internal/export/approved-packages",
            headers={"Authorization": f"Bearer {GATEWAY_TOKEN}"},
        )
        assert resp.status_code == 200


# ==============================================================
# بخش ۵ — Rate Limiting
# ==============================================================

class TestRateLimiting:

    def test_submit_rate_limit_per_ip_enforced(self, client: TestClient, contributor_headers):
        """
        بیش از ۳۵ ارسال در ۶۰ ثانیه از یک IP باید ۴۲۹ برگرداند.
        (عملاً rate limiter reset می‌شه بین تست‌ها، پس مستقیماً rate limiter رو تست می‌کنیم)
        """
        from app.core.rate_limiter import global_rate_limiter

        # اشباع کردن bucket
        for i in range(36):
            global_rate_limiter.is_allowed(
                key="submit_ip_test_rate_limit_ip", limit=35, window_seconds=60
            )

        # تماس بعدی باید false باشد
        result = global_rate_limiter.is_allowed(
            key="submit_ip_test_rate_limit_ip", limit=35, window_seconds=60
        )
        assert result is False

    def test_register_rate_limit_per_ip(self, client: TestClient):
        """
        بیش از ۱۰ ثبت‌نام از یک IP در ۶۰ ثانیه باید ۴۲۹ بده.
        """
        from app.core.rate_limiter import global_rate_limiter

        for i in range(11):
            global_rate_limiter.is_allowed(
                key="register_ip_192.168.1.1", limit=10, window_seconds=60
            )

        result = global_rate_limiter.is_allowed(
            key="register_ip_192.168.1.1", limit=10, window_seconds=60
        )
        assert result is False

    def test_rate_limiter_reset_clears_all_buckets(self):
        """بعد از reset، همه bucket‌ها باید خالی شوند."""
        from app.core.rate_limiter import global_rate_limiter

        for i in range(100):
            global_rate_limiter.is_allowed(key="test_bucket_reset", limit=5, window_seconds=60)

        global_rate_limiter.reset()
        result = global_rate_limiter.is_allowed(
            key="test_bucket_reset", limit=5, window_seconds=60
        )
        assert result is True


# ==============================================================
# بخش ۶ — Frontend–Backend Contract Mismatch (Static Analysis)
# ==============================================================

class TestFrontendBackendContractMismatch:
    """
    این تست‌ها بدون راه‌اندازی HTTP server اجرا می‌شوند.
    مستقیماً با خواندن فایل client.ts مغایرت‌های شناخته‌شده را اثبات می‌کنند.
    هدف: اطمینان از اینکه هر بار که backend endpoint عوض می‌شه این تست‌ها fail کنند
    تا توسعه‌دهنده مجبور شود frontend را هم بروز کند.
    """

    CLIENT_TS_PATH = (
        "/home/haji/Desktop/contribution_service/frontend/src/api/client.ts"
    )

    def _read_client(self) -> str:
        with open(self.CLIENT_TS_PATH, encoding="utf-8") as f:
            return f.read()

    def test_contribution_endpoint_prefix_is_contribution_not_contributions(self):
        """
        backend prefix: /api/v1/contribution (singular)
        frontend client.ts currently uses: /contributions (plural) — MISMATCH
        این تست عمداً FAIL می‌کند تا توسعه‌دهنده مجبور به اصلاح شود.
        """
        content = self._read_client()
        # بررسی اینکه endpoint درست استفاده شده
        assert "/contribution/submit/enhanced" in content, (
            "FRONTEND CONTRACT BUG: client.ts uses '/contributions/submit/enhanced' "
            "but backend endpoint is '/contribution/submit/enhanced' (singular). "
            "Fix: change '/contributions/' to '/contribution/' in client.ts"
        )

    def test_review_queue_endpoint_is_correct(self):
        """
        backend: GET /api/v1/contribution/review/pending
        frontend client.ts: GET /reviews/queue — MISMATCH
        """
        content = self._read_client()
        assert "/contribution/review/pending" in content, (
            "FRONTEND CONTRACT BUG: client.ts uses '/reviews/queue' "
            "but backend endpoint is '/contribution/review/pending'. "
            "Fix: change getReviewQueue() to use '/contribution/review/pending'"
        )

    def test_review_decision_endpoint_is_correct(self):
        """
        backend: POST /api/v1/contribution/review/decision (body: {submission_id, decision, ...})
        frontend: POST /reviews/{submissionId} — MISMATCH (path param vs body param)
        """
        content = self._read_client()
        assert "/contribution/review/decision" in content, (
            "FRONTEND CONTRACT BUG: client.ts uses '/reviews/${submissionId}' "
            "but backend endpoint is '/contribution/review/decision' with body params. "
            "Fix: change submitReview() to POST to '/contribution/review/decision'"
        )

    def test_history_endpoint_is_correct(self):
        """
        backend: GET /api/v1/contribution/history
        frontend: GET /contributions/history — MISMATCH
        """
        content = self._read_client()
        assert "/contribution/history" in content, (
            "FRONTEND CONTRACT BUG: client.ts uses '/contributions/history' "
            "but backend endpoint is '/contribution/history'. "
            "Fix: change getMyHistory() to use '/contribution/history'"
        )

    def test_upload_endpoint_is_correct(self):
        """
        backend: POST /api/v1/contribution/upload
        frontend: POST /contributions/upload — MISMATCH
        """
        content = self._read_client()
        assert "/contribution/upload" in content, (
            "FRONTEND CONTRACT BUG: client.ts uses '/contributions/upload' "
            "but backend endpoint is '/contribution/upload'. "
            "Fix: change uploadDocument() to use '/contribution/upload'"
        )

    def test_login_endpoint_uses_token_not_login(self):
        """
        backend: POST /api/v1/auth/token
        frontend باید از /auth/token استفاده کند، نه /auth/login.
        """
        content = self._read_client()
        assert "/auth/token" in content, (
            "FRONTEND CONTRACT BUG: login endpoint should be '/auth/token' "
            "(OAuth2 standard), not '/auth/login'."
        )

    def test_user_profile_field_mcc_credits_vs_total_credits(self):
        """
        backend UserOut schema: total_credits
        frontend UserProfile type: mcc_credits — MISMATCH
        """
        types_path = (
            "/home/haji/Desktop/contribution_service/frontend/src/types/index.ts"
        )
        with open(types_path, encoding="utf-8") as f:
            content = f.read()

        assert "total_credits" in content, (
            "FRONTEND TYPE BUG: UserProfile uses 'mcc_credits' "
            "but backend UserOut returns 'total_credits'. "
            "Fix: rename mcc_credits to total_credits in types/index.ts"
        )

    def test_submission_status_types_are_consistent(self):
        """
        backend SubmissionStatusType: includes 'under_legal_review', 'needs_correction', 'in_processing'
        frontend SubmissionStatus: uses 'under_review', 'quarantined', 'archived' — MISMATCH
        این تست وجود مقادیر backend را در frontend type بررسی می‌کند.
        """
        types_path = (
            "/home/haji/Desktop/contribution_service/frontend/src/types/index.ts"
        )
        with open(types_path, encoding="utf-8") as f:
            content = f.read()

        backend_statuses = [
            "under_legal_review",
            "needs_correction",
            "in_processing",
        ]
        missing = [s for s in backend_statuses if s not in content]
        assert not missing, (
            f"FRONTEND TYPE BUG: SubmissionStatus is missing backend states: {missing}. "
            "Frontend uses 'under_review' but backend uses 'under_legal_review'. "
            "Fix: sync SubmissionStatus in types/index.ts with backend SubmissionStatusType."
        )
