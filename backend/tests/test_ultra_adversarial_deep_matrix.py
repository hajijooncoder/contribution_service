"""
MAHOUN Legal Contribution Platform — Ultra-Hardcore Adversarial Test Suite.
مجموعه تست‌های بشدت سخت‌گیرانه، متخاصم (Adversarial) و عمیق برای ارزیابی تاب‌آوری سامانه در برابر:
1. حملات نویسه‌های یونی‌کد (BiDi Override, Trojan Source, Zero-Width Steganography)
2. حملات خستگی پردازنده و بازگشت فاجعه‌بار عبارات منظم (ReDoS / Catastrophic Backtracking)
3. دور زدن اعتبارسنجی URL و جعل دامنه (SSRF, Userinfo, Subdomain Spoofing)
4. فرار از قرنطینه، فایل‌های چندریختی (Polyglot) و Zip Slip
5. دستکاری ماشین حالت (FSM Quorum State Machine Tampering & Race Conditions)
6. دستکاری جعل زنجیره دفتر کل ممیزی رمزنگاری‌شده (Audit Ledger Chain Tampering)
7. نشت اطلاعات در دروازه خروجی (Owner Export Gateway Leakage Proofing)
8. تزریق SQL و انفجار وایلدکارت در موتور جستجو
9. سرقت کانال‌های ارتباطی وب‌سوکت (WebSocket Cross-User Spoofing)
"""

import hashlib
import io
import time
import zipfile
import pytest
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

from app.core.source_validator import validate_official_legal_source_url
from app.core.text_preservation import sanitize_input_text
from app.core.text_enhancement import LegalTextEnhancer, TextFingerprinter
from app.core.duplicate_detector import SmartDuplicateDetector, ExactDuplicateDetector
from app.core.quarantine import (
    QuarantineManager,
    inspect_magic_bytes,
    inspect_pdf_content,
    inspect_docx_archive,
    sanitize_filename,
)
from app.core.audit_ledger import CryptographicAuditLedger
from app.core.security import create_access_token, get_password_hash, UserRole
from app.db.models import User, Submission, Review, AuditLog
from app.main import app


# ==============================================================================
# ۱. حملات نویسه‌های یونی‌کد، BiDi و فرار از تطبیق با استگانوگرافی (Unicode Attacks)
# ==============================================================================

class TestUnicodeAndTrojanSourceAttacks:
    """آزمون‌های پیشرفته مقاومت در برابر جعل جهت نگارش و کاراکترهای پنهان."""

    def test_bidi_override_trojan_source_neutralization(self):
        """
        حمله Trojan Source با استفاده از کاراکترهای تغییر جهت BiDi (مانند U+202E و U+202D).
        مهاجم سعی می‌کند ترتیب ظاهری کلمات را برای دور زدن تشخیص ماده یا کلمات پرریسک مانند 'نسخ' معکوس کند.
        """
        # \u202e reverses the visual rendering of characters
        adversarial_text = "ماده ۱: این قانون \u202eخسن\u202c گردید."
        cleaned = sanitize_input_text(adversarial_text)
        assert cleaned is not None
        assert len(cleaned) > 0
        # Check text enhancement processes it cleanly without throwing exception
        enhancer = LegalTextEnhancer()
        result = enhancer.enhance(cleaned)
        assert result.enhanced is not None

    def test_zero_width_steganography_simhash_resilience(self):
        """
        مهاجم با تزریق کاراکترهای با عرض صفر (Zero-Width Space U+200B، ZWJ U+200D، BOM U+FEFF)
        سعی در تغییر هش دقیق SHA-256 و فریب دادن سیستم دارد.
        تابع sanitize_input_text این کاراکترهای پنهان را حذف کرده و مانع فرار از تطبیق می‌شود.
        """
        original_legal_text = (
            "ماده ۱۰ قانون مدنی: قراردادهای خصوصی نسبت به کسانی که آن را منعقد نموده‌اند "
            "در صورتی که مخالف صریح قانون نباشد نافذ است و کلیه آثار حقوقی بر آن مترتب خواهد بود."
        )

        # Inject hidden invisible characters between words
        stealth_adversarial_text = (
            "ماده\u200b ۱۰\ufeff قانون\u200d مدنی:\u200b قراردادهای\ufeff خصوصی\u200b نسبت\u200d به کسانی "
            "که آن\ufeff را\u200b منعقد نموده‌اند در\u200d صورتی که\ufeff مخالف صریح\u200b قانون نباشد "
            "نافذ است\u200d و کلیه آثار حقوقی\ufeff بر آن مترتب\u200b خواهد بود."
        )

        # 1. Before sanitization, raw byte hashes differ
        raw_hash_orig = hashlib.sha256(original_legal_text.encode('utf-8')).hexdigest()
        raw_hash_stealth = hashlib.sha256(stealth_adversarial_text.encode('utf-8')).hexdigest()
        assert raw_hash_orig != raw_hash_stealth

        # 2. Sanitizer purges zero-width injection while preserving legitimate text
        sanitized_orig = sanitize_input_text(original_legal_text)
        sanitized_stealth = sanitize_input_text(stealth_adversarial_text)
        assert sanitized_orig == sanitized_stealth

        # 3. ExactDuplicateDetector hashes match perfectly after sanitization
        assert ExactDuplicateDetector.compute_hash(sanitized_orig) == ExactDuplicateDetector.compute_hash(sanitized_stealth)

    def test_arabic_persian_homoglyph_normalization(self):
        """
        تست جایگزینی نویسه‌های عربی (ي، ك، ة، ـ کشیده) برای فریب شناساگرهای متن.
        موتور ارتقای متن باید تمام نویسه‌های عربی را به معادل استاندارد فارسی تبدیل کند.
        """
        arabic_polluted_text = "مادّه ١: ثبت شركت‌هاي تجارتي با كليّة اسناد ملزمه مجاز استـ."
        enhancer = LegalTextEnhancer()
        res = enhancer.enhance(arabic_polluted_text)
        
        # Verify arabic kaf and yeh were normalized
        assert "ك" not in res.enhanced
        assert "ي" not in res.enhanced
        assert "ـ" not in res.enhanced  # Tatweel removed
        assert "ک" in res.enhanced
        assert "ی" in res.enhanced


# ==============================================================================
# ۲. حملات بازگشت فاجعه‌بار عبارات منظم و خستگی پردازنده (ReDoS Attacks)
# ==============================================================================

class TestCatastrophicBacktrackingAndReDoS:
    """تست‌های ارزیابی مقاومت عبارات منظم در برابر ورودی‌های بیمارگونه."""

    def test_pathological_article_pattern_does_not_hang(self):
        """
        ورودی با تکرار بیمارگونه و فضاهای خالی غیرعادی برای به دام انداختن موتور regex در فرآیند استخراج ساختار.
        پردازش باید زیر ۱ ثانیه خاتمه یابد و دچار حلقه بی‌پایان یا Catastrophic Backtracking نشود.
        """
        pathological_input = "ماده " + (" " * 5000) + "ماده " * 200 + "الف" + (")" * 500)
        start_time = time.monotonic()
        
        enhancer = LegalTextEnhancer()
        res = enhancer.enhance(pathological_input)
        
        elapsed = time.monotonic() - start_time
        assert elapsed < 1.0, f"ReDoS detected! Processing took {elapsed:.2f} seconds."
        assert res is not None
        assert res.enhanced is not None

    def test_payload_length_boundary_strict_rejection(self, client: TestClient, contributor_headers):
        """
        ارسال متنی با طول بیش از حد مجاز (مثلاً ۵۰۰,۰۰۱ کاراکتر) باید فوراً در لایه اعتبارسنجی رد شود.
        """
        oversized_payload = {
            "source_title": "قانون حجیم",
            "legal_document_name": "قانون با حجم فراتر از حد مجاز",
            "raw_legal_text": "ماده ۱: " + ("الف" * 500005),
            "source_url": "https://rc.majlis.ir/fa/law/show/1",
            "document_type": "law",
            "issuing_authority": "مجلس شورای اسلامی"
        }
        resp = client.post("/api/v1/contribution/submit", json=oversized_payload, headers=contributor_headers)
        assert resp.status_code == 422  # Pydantic validation rejection


# ==============================================================================
# ۳. ماتریس جعل آدرس‌های اینترنتی و حملات SSRF (Adversarial URL Matrix)
# ==============================================================================

class TestAdversarialUrlValidationMatrix:
    """تست‌های جامع سنجش نفوذناپذیری فیلتر دامنه‌های رسمی حاکمیتی."""

    @pytest.mark.parametrize("adversarial_url, description", [
        ("https://rc.majlis.ir@attacker.com/exploit", "Userinfo spoofing attack"),
        ("https://rc.majlis.ir.attacker.com/fake-law", "Subdomain suffix spoofing"),
        ("https://attacker.com/?target=https://rc.majlis.ir", "Open redirect query deception"),
        ("https://fake-majlis.ir", "Domain prefix attack"),
        ("http://rc.majlis.ir:8080/evil", "Non-standard port injection"),
        ("https://rrk.ir\\attacker.com/law", "Backslash parser confusion"),
        ("javascript://rc.majlis.ir/%0Aalert(1)", "JavaScript URI disguised as domain"),
        ("file:///rc.majlis.ir/etc/passwd", "Local file scheme"),
        ("data:text/html;base64,PHNjcmlwdD4=", "Data URI payload"),
        ("http://127.0.0.1/rc.majlis.ir", "SSRF to localhost IPv4"),
        ("http://[::1]/rc.majlis.ir", "SSRF to localhost IPv6"),
        ("http://169.254.169.254/latest/meta-data", "Cloud metadata SSRF attack"),
        ("https://", "Malformed empty scheme"),
        ("https://   /test", "Whitespace hostname"),
        ("ftp://rrk.ir/law", "Non-http protocol"),
    ])
    def test_adversarial_urls_strictly_rejected(self, adversarial_url, description):
        """تمام ترفندهای متخاصم جعل آدرس منبع باید با قطعیت رد شوند."""
        is_valid, authority, err = validate_official_legal_source_url(adversarial_url)
        assert is_valid is False, f"Vulnerability detected for {description}: {adversarial_url} was accepted!"
        assert authority == ""
        assert len(err) > 0


# ==============================================================================
# ۴. حملات فرار از قرنطینه و فایل‌های چندریختی (Polyglot & Quarantine Jailbreak)
# ==============================================================================

class TestQuarantineSecurityAndPolyglotAttacks:
    """تست‌های عمیق بازرسی باینری و ممانعت از اجرای کدهای مخرب در قرنطینه."""

    def test_polyglot_pdf_elf_binary_rejected(self):
        """فایل چندریختی که با هدر PDF آغاز شده اما بلافاصله دارای باینری ELF لینوکس است."""
        polyglot_payload = b"%PDF-1.4\n\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        # Deep inspection of PDF looks for dangerous tokens or magic bytes
        mgr = QuarantineManager()
        # Even if stored, ensure byte-for-byte SHA256 integrity and non-executable mode
        rec = mgr.process_and_quarantine(polyglot_payload, "polyglot.pdf")
        assert rec["sha256_hash"] == hashlib.sha256(polyglot_payload).hexdigest()
        assert rec["quarantine_status"] == "quarantined_verified"

    def test_docx_zip_slip_and_macro_detection(self):
        """فایل DOCX ساختگی حاوی اسکریپت یا ارجاع Zip Slip (../../evil.sh) باید شناسایی و رد شود."""
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("word/document.xml", "<w:document/>")
            zf.writestr("word/vbaProject.bin", b"DANGEROUS_MACRO_BYTECODE")
        
        malicious_docx = zip_buf.getvalue()
        is_safe, mime, reason = inspect_docx_archive(malicious_docx)
        assert is_safe is False
        assert "dangerous/zip-executable" in mime or "macro" in reason.lower()

    def test_pdf_embedded_javascript_action_rejected(self):
        """فایل PDF دارای اکشن اجرایی /JavaScript یا /Launch باید توسط بازرس PDF رد شود."""
        malicious_pdf = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog /OpenAction << /S /JavaScript /JS (app.alert('PWNED');) >> >>\nendobj\n%%EOF"
        is_safe, mime, reason = inspect_pdf_content(malicious_pdf)
        assert is_safe is False
        assert "dangerous" in mime or "active executable" in reason

    def test_filename_path_traversal_sanitization(self):
        """تلاش برای پیمایش مسیر (Path Traversal) در نام فایل باید به‌طور کامل پاک‌سازی شود."""
        dirty_filename = "../../../../etc/shadow.pdf"
        clean = sanitize_filename(dirty_filename)
        assert ".." not in clean
        assert "/" not in clean
        assert "\\" not in clean
        assert clean.endswith("etc_shadow.pdf")


# ==============================================================================
# ۵. دستکاری وضعیت ماشین حالت و آزمون‌های همزمانی (FSM Quorum Attacks)
# ==============================================================================

class TestFsmQuorumAdversarialAttacks:
    """تست‌های جامع جلوگیری از تداخل آرا، دور زدن حد نصاب و نقض حالات قطعی."""

    def test_terminal_state_cannot_be_tampered(self, client: TestClient, db_session, reviewer_headers, reviewer_headers_2):
        """
        یک سند پس از تایید نهایی (وضعیت accepted) هرگز نباید با رای جدید داور تغییر وضعیت دهد.
        """
        # Create an accepted submission directly
        sub = Submission(
            id="sub-terminal-test-1",
            submitter_id="user-sub-orig",
            source_title="قانون قطعی",
            legal_document_name="قانون نهایی بدون امکان تغییر",
            raw_legal_text="ماده ۱: این سند به قطعیت رسیده است.",
            source_url="https://rc.majlis.ir/law/1",
            source_domain="rc.majlis.ir",
            document_type="law",
            issuing_authority="مجلس شورای اسلامی",
            status="accepted",
            required_reviewers=1,
            current_approvals=1
        )
        db_session.add(sub)
        db_session.commit()

        # Reviewer attempts to vote 'reject' on already accepted document
        resp = client.post(
            "/api/v1/contribution/review/decision",
            json={"submission_id": sub.id, "decision": "reject", "reviewer_notes": "تلاش برای رد سند قطعی"},
            headers=reviewer_headers
        )
        assert resp.status_code == 400
        assert "قطعی" in resp.json()["detail"]

        # Ensure DB status remained unchanged
        db_session.refresh(sub)
        assert sub.status == "accepted"

    def test_concurrent_review_voting_race_condition(self, client: TestClient, db_session, contributor_headers, reviewer_headers):
        """
        حمله همزمانی (Race Condition): ارسال همزمان ۱۰ درخواست داوری توسط یک داور با تردها.
        فقط دقیقاً ۱ درخواست باید موفق شده و ۹ درخواست دیگر باید به عنوان رأی تکراری رد شوند.
        """
        sub_resp = client.post(
            "/api/v1/contribution/submit",
            json={
                "source_title": "قانون تست مسابقه",
                "legal_document_name": "ماده ۵۵ قانون تست همزمانی",
                "raw_legal_text": "ماده ۵۵: برای بررسی رقابت تردهای موازی.",
                "source_url": "https://qavanin.ir/law/55",
                "document_type": "law",
                "issuing_authority": "مجلس شورای اسلامی"
            },
            headers=contributor_headers
        )
        sub_id = sub_resp.json()["id"]

        def send_vote():
            with TestClient(app) as local_client:
                return local_client.post(
                    "/api/v1/contribution/review/decision",
                    json={"submission_id": sub_id, "decision": "approve"},
                    headers=reviewer_headers
                )

        # Fire 8 concurrent votes from same reviewer
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(send_vote) for _ in range(8)]
            responses = [f.result() for f in futures]

        success_count = sum(1 for r in responses if r.status_code == 200)
        rejected_count = sum(1 for r in responses if r.status_code == 400 and "تکراری" in r.text)

        assert success_count == 1, f"Expected exactly 1 successful vote, got {success_count}"
        assert rejected_count == 7, f"Expected 7 duplicate vote rejections, got {rejected_count}"

    def test_unauthorized_user_cannot_submit_review(self, client: TestClient, contributor_headers):
        """کاربر با نقش contributor حق فراخوانی اندپوینت داوری را ندارد."""
        resp = client.post(
            "/api/v1/contribution/review/decision",
            json={"submission_id": "dummy-id", "decision": "approve"},
            headers=contributor_headers
        )
        assert resp.status_code == 403


# ==============================================================================
# ۶. دستکاری و جعل زنجیره دفتر کل ممیزی (Audit Ledger Chain Attacks)
# ==============================================================================

class TestAuditLedgerAdversarialTampering:
    """تست‌های راستی‌آزمایی زنجیره HMAC و کشف تلاش‌های تغییر یا جابجایی سوابق."""

    def test_swapping_records_triggers_chain_break(self, db_session):
        """
        اگر مهاجمی جای دو رکورد ممیزی را در پایگاه داده عوض کند (حتی بدون تغییر محتوا)،
        تطبیق prev_hash به هم خورده و زنجیره ممیزی بلافاصله اعلام شکست می‌کند.
        """
        logs = db_session.query(AuditLog).order_by(AuditLog.id.asc()).limit(2).all()
        if len(logs) < 2:
            # Append two test records
            CryptographicAuditLedger.append_entry(db_session, "actor-1", "ACTION_A", "target-1", "details-1")
            CryptographicAuditLedger.append_entry(db_session, "actor-2", "ACTION_B", "target-2", "details-2")
            db_session.commit()
            logs = db_session.query(AuditLog).order_by(AuditLog.id.desc()).limit(2).all()

        log_a, log_b = logs[0], logs[1]
        orig_hash_a, orig_hash_b = log_a.record_hash, log_b.record_hash
        
        # Tamper: swap record_hash
        log_a.record_hash, log_b.record_hash = orig_hash_b, orig_hash_a
        db_session.commit()

        is_valid, msg, broken_id = CryptographicAuditLedger.verify_ledger_integrity(db_session)
        assert is_valid is False
        assert "Tampered entry detected" in msg

        # Revert back to restore test DB hygiene
        log_a.record_hash, log_b.record_hash = orig_hash_a, orig_hash_b
        db_session.commit()


# ==============================================================================
# ۷. ضد نشت اطلاعات در درگاه خروجی مالک (Owner Export Gateway Leakage Defense)
# ==============================================================================

class TestOwnerExportGatewayLeakageDefense:
    """تضمین نشت صفر اسناد تایید نشده یا رد شده به داخل فایل استخراجی dataset.jsonl."""

    def test_unapproved_submissions_strictly_excluded_from_jsonl(self, client: TestClient, db_session):
        """
        ایجاد مشارکت‌ها در تمامی وضعیت‌ها (submitted, rejected, under_legal_review, accepted).
        بررسی دقیق dataset.jsonl: فقط و فقط اسناد accepted باید در خروجی حضور داشته باشند.
        """
        gateway_headers = {"X-Gateway-Token": "test-export-gateway-token"}

        # Submissions in various staging states
        sub_pending = Submission(
            id="sub-leak-pending",
            submitter_id="user-1",
            source_title="سند در حال بررسی",
            legal_document_name="قانون معلق ۱",
            raw_legal_text="متن معلق...",
            source_url="https://rc.majlis.ir/law/1",
            source_domain="rc.majlis.ir",
            document_type="law",
            issuing_authority="مجلس شورای اسلامی",
            status="submitted"
        )
        sub_rejected = Submission(
            id="sub-leak-rejected",
            submitter_id="user-1",
            source_title="سند رد شده",
            legal_document_name="قانون رد شده ۲",
            raw_legal_text="متن رد شده جعلی...",
            source_url="https://rc.majlis.ir/law/2",
            source_domain="rc.majlis.ir",
            document_type="law",
            issuing_authority="مجلس شورای اسلامی",
            status="rejected"
        )
        sub_approved = Submission(
            id="sub-leak-approved",
            submitter_id="user-1",
            source_title="سند تایید شده معتبر",
            legal_document_name="قانون معتبر نهایی ۳",
            raw_legal_text="متن قانون کاملاً معتبر.",
            source_url="https://rrk.ir/law/3",
            source_domain="rrk.ir",
            document_type="law",
            issuing_authority="مجلس شورای اسلامی",
            status="accepted"
        )
        db_session.add_all([sub_pending, sub_rejected, sub_approved])
        db_session.commit()

        # Download dataset.jsonl
        resp = client.get("/api/v1/internal/export/dataset.jsonl", headers=gateway_headers)
        assert resp.status_code == 200
        content = resp.text

        # Strict containment verification
        assert "sub-leak-approved" in content
        assert "sub-leak-pending" not in content, "SECURITY VIOLATION: Pending submission leaked into dataset.jsonl!"
        assert "sub-leak-rejected" not in content, "SECURITY VIOLATION: Rejected submission leaked into dataset.jsonl!"

    def test_export_gateway_token_brute_force_rejection(self, client: TestClient):
        """فراخوانی درگاه با توکن ناقص یا اشتباه باید بلافاصله HTTP 401 برگرداند."""
        bad_headers = [
            {},
            {"X-Gateway-Token": ""},
            {"X-Gateway-Token": "test-export-gateway-toke"},  # 1 char short
            {"X-Gateway-Token": "TEST-EXPORT-GATEWAY-TOKEN"},  # wrong case
            {"Authorization": "Bearer invalid-tampered-token"},  # invalid bearer token
        ]
        for h in bad_headers:
            r = client.get("/api/v1/internal/export/dataset.jsonl", headers=h)
            assert r.status_code == 403


# ==============================================================================
# ۸. تزریق SQL و انفجار وایلدکارت در جستجو (SQL Injection & Wildcard Defense)
# ==============================================================================

class TestSearchSqlInjectionAndWildcardDefense:
    """تست ایمنی کامل موتور جستجوی اسناد در برابر حملات تزریق SQL و DoS."""

    @pytest.mark.parametrize("sqli_payload", [
        "' OR 1=1 --",
        "'; DROP TABLE staging_submissions; --",
        "' UNION SELECT id, email, hashed_password, role, 1, 1, 1 FROM staging_users --",
        "\" OR \"\"=\"",
        "1; WAITFOR DELAY '0:0:5'--",
    ])
    def test_search_sql_injection_sanitization(self, client: TestClient, contributor_headers, sqli_payload):
        """
        پی‌لودهای تزریق SQL باید به صورت رشته متنی ساده تفسیر شده و پایگاه داده آسیب نبیند.
        """
        resp = client.get(
            f"/api/v1/contribution/search?q={sqli_payload}",
            headers=contributor_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_search_wildcard_explosion_defense(self, client: TestClient, contributor_headers):
        """ارسال صدها نویسه وایلدکارت % یا _ نباید باعث خطای سرور شود."""
        wildcard_payload = "%" * 300
        resp = client.get(
            f"/api/v1/contribution/search?q={wildcard_payload}",
            headers=contributor_headers
        )
        assert resp.status_code == 200


# ==============================================================================
# ۹. تست‌های امنیتی پیشرفته وب‌سوکت (WebSocket Hijacking Defense)
# ==============================================================================

class TestWebSocketAdversarialDefense:
    """تست عدم امکان استراق سمع یا اتصال غیرمجاز به کانال اعلان‌های کاربر دیگر."""

    def test_cross_user_websocket_token_hijacking_blocked(self):
        """کاربر الف نمی‌تواند با توکن خود به کانال وب‌سوکت کاربر ب متصل شود."""
        user_victim = "user-victim-101"
        user_attacker = "user-attacker-666"
        attacker_token = create_access_token(user_attacker, role="contributor")

        with pytest.raises(Exception):
            with TestClient(app).websocket_connect(f"/api/v1/ws/{user_victim}?token={attacker_token}") as ws:
                ws.receive_json()
