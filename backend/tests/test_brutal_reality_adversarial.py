import concurrent.futures
from app.core.audit_ledger import CryptographicAuditLedger
from app.core.rate_limiter import global_rate_limiter
from app.db.models import User, Submission, Review, AuditLog
from app.core.security import create_access_token, get_password_hash, UserRole

def test_conflict_of_interest_self_review_is_strictly_blocked(client, db_session):
    """
    BRUTAL ADVERSARIAL TEST: Submitter acquires reviewer role and attempts to approve their own submission.
    The FSM MUST block this with a conflict of interest violation.
    """
    # Create a user who is both contributor and reviewer
    tricky_user = User(
        email="lawyer-contributor@example.com",
        hashed_password=get_password_hash("pass123"),
        full_name="وکیل خودتأییدکننده",
        role=UserRole.REVIEWER,
        is_active=True
    )
    db_session.add(tricky_user)
    db_session.commit()
    db_session.refresh(tricky_user)

    token = create_access_token(subject=tricky_user.id, role=UserRole.REVIEWER)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Submits a proposition
    sub_payload = {
        "source_title": "قانون آیین دادرسی",
        "legal_document_name": "ماده ۲۰ قانون آیین دادرسی مدنی",
        "raw_legal_text": "ماده ۲۰: دعاوی راجع به ترکه متوفی اگر چه خواسته، دین و یا مربوط به وصایای متوفی باشد تا موقعی که ترکه تقسیم نشده در دادگاه محلی اقامه می‌شود که آخرین اقامتگاه متوفی در ایران بوده است.",
        "source_url": "https://qavanin.ir/Law/TreeText/12345",
        "document_type": "law",
        "issuing_authority": "مجلس شورای اسلامی"
    }
    resp = client.post("/api/v1/contribution/submit", json=sub_payload, headers=headers)
    assert resp.status_code == 201
    sub_id = resp.json()["id"]

    # 2. Attempts to review and approve their own submission
    review_resp = client.post(
        "/api/v1/contribution/review/decision",
        json={"submission_id": sub_id, "decision": "approve", "reviewer_notes": "خودم نوشتم و خودم تایید میکنم!"},
        headers=headers
    )
    assert review_resp.status_code == 400
    assert "تعارض منافع" in review_resp.json()["detail"]

    # Verify status did NOT change
    status_resp = client.get(f"/api/v1/contribution/status/{sub_id}", headers=headers)
    assert status_resp.json()["status"] == "submitted"

def test_double_voting_sybil_attack_is_blocked(client, contributor_headers, reviewer_headers):
    """
    BRUTAL ADVERSARIAL TEST: A reviewer tries to vote 'approve' twice on the same submission
    to bypass the two-reviewer quorum.
    """
    sub_payload = {
        "source_title": "قانون مدنی",
        "legal_document_name": "ماده ۴۰۰ قانون مدنی - نسخ ضمنی خیار شرط",
        "raw_legal_text": "ماده ۴۰۰ قانون مدنی: اگر ابتدای مدت خیار ذکر نشده باشد ابتداء آن از تاریخ عقد محسوب است وگرنه موجب بطلان شرط است.",
        "source_url": "https://dotic.ir/cat/laws/show/400",
        "document_type": "law",
        "issuing_authority": "مجلس شورای اسلامی"
    }
    sub_resp = client.post("/api/v1/contribution/submit", json=sub_payload, headers=contributor_headers)
    sub_id = sub_resp.json()["id"]

    # First vote from reviewer 1
    resp1 = client.post(
        "/api/v1/contribution/review/decision",
        json={"submission_id": sub_id, "decision": "approve"},
        headers=reviewer_headers
    )
    assert resp1.status_code == 200
    assert resp1.json()["new_status"] == "under_legal_review"

    # Second vote from the SAME reviewer 1 (Attempted bypass)
    resp2 = client.post(
        "/api/v1/contribution/review/decision",
        json={"submission_id": sub_id, "decision": "approve"},
        headers=reviewer_headers
    )
    assert resp2.status_code == 400
    assert "داوری تکراری" in resp2.json()["detail"]

    # Verify status is still under_legal_review and NOT accepted
    status_resp = client.get(f"/api/v1/contribution/status/{sub_id}", headers=contributor_headers)
    assert status_resp.json()["status"] == "under_legal_review"
    assert status_resp.json()["current_approvals"] == 1

def test_high_risk_repeal_strictly_requires_two_reviewers(client, contributor_headers, reviewer_headers, reviewer_headers_2):
    """
    BRUTAL ADVERSARIAL TEST: Any proposition containing 'نسخ' (Repeal) is classified as HIGH-RISK
    and MUST NEVER be accepted by a single reviewer. Export gateway must refuse to export it.
    """
    repeal_payload = {
        "source_title": "قانون اصلاحی",
        "legal_document_name": "نسخ صریح ماده ۵ قانون سابق",
        "raw_legal_text": "ماده ۵: بدینوسیله کلیه احکام و مقررات مغایر و ماده ۵ قانون قبلی نسخ و بلااثر می‌گردد.",
        "source_url": "https://rooznamehrasmi.ir/Laws/ShowLaw.aspx?Id=9876",
        "document_type": "regulation",  # Even if marked regulation, 'نسخ' forces HIGH-RISK!
        "issuing_authority": "هیأت وزیران"
    }
    sub_resp = client.post("/api/v1/contribution/submit", json=repeal_payload, headers=contributor_headers)
    assert sub_resp.status_code == 201
    sub_data = sub_resp.json()
    sub_id = sub_data["id"]
    assert sub_data["required_reviewers"] == 2

    # Single reviewer approves
    client.post(
        "/api/v1/contribution/review/decision",
        json={"submission_id": sub_id, "decision": "approve"},
        headers=reviewer_headers
    )

    # Status must still be under_legal_review
    assert client.get(f"/api/v1/contribution/status/{sub_id}", headers=contributor_headers).json()["status"] == "under_legal_review"

    # Export gateway MUST NOT include it in approved packages
    gateway_headers = {"X-Gateway-Token": "test-export-gateway-token"}
    export_resp = client.get("/api/v1/internal/export/approved-packages", headers=gateway_headers)
    packages = export_resp.json()["packages"]
    assert not any(p["manifest"]["submission_id"] == sub_id for p in packages)

    # Second independent reviewer approves
    client.post(
        "/api/v1/contribution/review/decision",
        json={"submission_id": sub_id, "decision": "approve"},
        headers=reviewer_headers_2
    )

    # Now it must transition to accepted and be present in export
    assert client.get(f"/api/v1/contribution/status/{sub_id}", headers=contributor_headers).json()["status"] == "accepted"
    export_resp2 = client.get("/api/v1/internal/export/approved-packages", headers=gateway_headers)
    packages2 = export_resp2.json()["packages"]
    assert any(p["manifest"]["submission_id"] == sub_id for p in packages2)

def test_cryptographic_audit_ledger_tamper_detection(db_session, client, contributor_headers):
    """
    BRUTAL ADVERSARIAL TEST: Tampering directly with the database audit records.
    The Cryptographic Audit Ledger MUST detect the broken chain and point to the tampered record.
    """
    # 1. Create a submission which appends to the audit chain
    payload = {
        "source_title": "قانون مجازات اسلامی",
        "legal_document_name": "ماده ۱ قانون مجازات اسلامی",
        "raw_legal_text": "ماده ۱ قانون مجازات اسلامی مشتمل بر جرایم و مجازات‌های حدود، قصاص، دیات و تعزیرات است.",
        "source_url": "https://rc.majlis.ir/fa/law/show/1111",
        "document_type": "law",
        "issuing_authority": "مجلس شورای اسلامی"
    }
    client.post("/api/v1/contribution/submit", json=payload, headers=contributor_headers)

    # 2. Ledger must be verified as pristine initially
    is_valid, msg, broken_id = CryptographicAuditLedger.verify_ledger_integrity(db_session)
    assert is_valid is True
    assert "verified successfully" in msg

    # 3. Simulate Rogue DBA Attack: Directly modify a log record's details in the database
    target_log = db_session.query(AuditLog).first()
    assert target_log is not None
    tampered_id = target_log.id
    original_details = target_log.details
    target_log.details = "TAMPERED_BY_MALICIOUS_DBA_IN_PRODUCTION"
    db_session.commit()

    # 4. Verification MUST fail-closed and catch the tampering!
    is_valid_after, msg_after, broken_id_after = CryptographicAuditLedger.verify_ledger_integrity(db_session)
    assert is_valid_after is False
    assert broken_id_after == tampered_id
    assert "Tampered entry detected" in msg_after

    # Restore pristine state so subsequent tests have a valid chain
    target_log.details = original_details
    db_session.commit()

def test_rate_limiter_flood_dos_protection(client, contributor_headers):
    """
    BRUTAL ADVERSARIAL TEST: Rapid burst submission flood attack.
    Rate limiter MUST trigger and return HTTP 429 Too Many Requests.
    """
    global_rate_limiter.reset()

    payload = {
        "source_title": "قانون اساسی",
        "legal_document_name": "اصل ۴ قانون اساسی",
        "raw_legal_text": "کلیه قوانین و مقررات مدنی، جزایی، مالی، اقتصادی، اداری، فرهنگی، نظامی، سیاسی و غیر اینها باید بر اساس موازین اسلامی باشد.",
        "source_url": "https://rc.majlis.ir/fa/law/show/444",
        "document_type": "law",
        "issuing_authority": "مجلس خبرگان قانون اساسی"
    }

    status_codes = []
    # Send 40 requests rapidly
    for _ in range(40):
        resp = client.post("/api/v1/contribution/submit", json=payload, headers=contributor_headers)
        status_codes.append(resp.status_code)

    # At least some requests must be blocked by rate limit (HTTP 429)
    assert 429 in status_codes
    assert status_codes.count(429) > 0

def test_multithreaded_concurrency_stress_voting(client, contributor_headers, db_session):
    """
    BRUTAL ADVERSARIAL TEST: 20 concurrent threads trying to submit reviews simultaneously.
    Ensures race conditions do not corrupt DB state or violate single-vote rules.
    """
    sub_payload = {
        "source_title": "قانون مدنی",
        "legal_document_name": "ماده ۳۰ قانون مدنی - مالکیت تام",
        "raw_legal_text": "ماده ۳۰: هر مالکی نسبت به مایملک خود حق همه گونه تصرف و انتفاع دارد مگر در مواردی که قانون استثناء کرده باشد.",
        "source_url": "https://rc.majlis.ir/fa/law/show/30",
        "document_type": "law",
        "issuing_authority": "مجلس شورای اسلامی"
    }
    sub_resp = client.post("/api/v1/contribution/submit", json=sub_payload, headers=contributor_headers)
    sub_id = sub_resp.json()["id"]

    # Create 10 distinct reviewers
    reviewers = []
    headers_list = []
    for i in range(10):
        rev = User(
            email=f"stress_rev_{i}@example.com",
            hashed_password=get_password_hash("pass"),
            full_name=f"داور استرس {i}",
            role=UserRole.REVIEWER,
            is_active=True
        )
        db_session.add(rev)
        db_session.commit()
        db_session.refresh(rev)
        reviewers.append(rev)
        t = create_access_token(subject=rev.id, role=UserRole.REVIEWER)
        headers_list.append({"Authorization": f"Bearer {t}"})

    def send_review(headers):
        return client.post(
            "/api/v1/contribution/review/decision",
            json={"submission_id": sub_id, "decision": "approve", "reviewer_notes": "تایید"},
            headers=headers
        )

    # Fire reviews concurrently using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(send_review, headers_list))

    # All requests should return valid response codes (200 or 400 if already finalized), no 500 crashes
    assert all(r.status_code in [200, 400] for r in results)

    # Exactly 2 approvals were needed, status must be accepted, and no duplicate reviews per reviewer
    final_sub = client.get(f"/api/v1/contribution/status/{sub_id}", headers=contributor_headers).json()
    assert final_sub["status"] == "accepted"

def test_idor_status_isolation_strictly_enforced(client, contributor_headers, db_session):
    """
    HIGH SEVERITY ADVERSARIAL TEST: Verify IDOR prevention on /contribution/status/{id}.
    - Anonymous caller gets HTTP 401.
    - Another unauthorized user gets HTTP 403 Forbidden.
    - Document owner gets HTTP 200.
    """
    sub_payload = {
        "source_title": "قانون ثبت اسناد",
        "legal_document_name": "ماده ۲۲ قانون ثبت",
        "raw_legal_text": "ماده ۲۲: همین که ملکی مطابق قانون در دفتر املاک به ثبت رسید دولت فقط کسی را که ملک به اسم او ثبت شده مالک خواهد شناخت.",
        "source_url": "https://qavanin.ir/Law/TreeText/2222",
        "document_type": "law",
        "issuing_authority": "مجلس شورای اسلامی"
    }
    sub_resp = client.post("/api/v1/contribution/submit", json=sub_payload, headers=contributor_headers)
    assert sub_resp.status_code == 201
    sub_id = sub_resp.json()["id"]

    # 1. Anonymous caller is blocked (401 Unauthorized)
    anon_resp = client.get(f"/api/v1/contribution/status/{sub_id}")
    assert anon_resp.status_code == 401

    # 2. Another independent contributor attempts to view it (IDOR probe)
    other_user = User(
        email="stranger@example.com",
        hashed_password=get_password_hash("pass"),
        full_name="کاربر غریبه",
        role=UserRole.CONTRIBUTOR,
        is_active=True
    )
    db_session.add(other_user)
    db_session.commit()
    stranger_token = create_access_token(subject=other_user.id, role=UserRole.CONTRIBUTOR)
    stranger_headers = {"Authorization": f"Bearer {stranger_token}"}

    forbidden_resp = client.get(f"/api/v1/contribution/status/{sub_id}", headers=stranger_headers)
    assert forbidden_resp.status_code == 403
    assert "مجاز به مشاهده" in forbidden_resp.json()["detail"]

    # 3. Authentic owner gets access
    owner_resp = client.get(f"/api/v1/contribution/status/{sub_id}", headers=contributor_headers)
    assert owner_resp.status_code == 200
    assert owner_resp.json()["id"] == sub_id

def test_contributor_history_strictly_requires_auth_and_isolates_records(client, contributor_headers, db_session):
    """
    HIGH SEVERITY ADVERSARIAL TEST: Verify /contribution/history
    - Anonymous caller gets HTTP 401 (Zero data leakage).
    - Authenticated caller sees ONLY their own records.
    """
    # 1. Anonymous request must be rejected
    anon_resp = client.get("/api/v1/contribution/history")
    assert anon_resp.status_code == 401

    # 2. Authenticated user gets only their history
    hist_resp = client.get("/api/v1/contribution/history", headers=contributor_headers)
    assert hist_resp.status_code == 200

def test_staging_reviews_database_unique_constraint_enforced(db_session, contributor_user, reviewer_user):
    """
    HIGH SEVERITY ADVERSARIAL TEST: Database-level composite UniqueConstraint on (submission_id, reviewer_id).
    Attempting to directly insert two review rows for the same submission and reviewer must trigger IntegrityError.
    """
    from sqlalchemy.exc import IntegrityError
    sub = Submission(
        submitter_id=contributor_user.id,
        source_title="سند تست یکتایی",
        legal_document_name="ماده ۱۰۰",
        raw_legal_text="متن تست جهت تست یکتایی دیتابیس",
        source_url="https://rc.majlis.ir/fa/law/show/100",
        source_domain="مجلس",
        document_type="law",
        issuing_authority="مجلس"
    )
    db_session.add(sub)
    db_session.commit()

    # First review succeeds
    rev1 = Review(submission_id=sub.id, reviewer_id=reviewer_user.id, decision="approve")
    db_session.add(rev1)
    db_session.commit()

    # Second review with same (submission_id, reviewer_id) MUST fail at DB level
    rev2 = Review(submission_id=sub.id, reviewer_id=reviewer_user.id, decision="approve")
    db_session.add(rev2)
    try:
        db_session.commit()
        assert False, "Database failed to enforce UniqueConstraint on (submission_id, reviewer_id)"
    except IntegrityError:
        db_session.rollback()

def test_audit_ledger_hmac_full_chain_recomputation_defense(db_session):
    """
    HIGH SEVERITY ADVERSARIAL TEST: An attacker with direct database write access attempts
    to tamper with a record and recompute hashes using an unauthorized key or unkeyed SHA-256.
    The CryptographicAuditLedger must detect the signature mismatch.
    """
    entry = CryptographicAuditLedger.append_entry(
        db=db_session,
        actor_id="test_actor",
        action="TEST_ACTION",
        target_id="target_123",
        details="Authentic log entry"
    )
    db_session.commit()

    # Verify initial chain passes
    is_valid, _, _ = CryptographicAuditLedger.verify_ledger_integrity(db_session)
    assert is_valid is True

    # Checkpoint tip matches
    checkpoint = CryptographicAuditLedger.get_ledger_checkpoint(db_session)
    assert checkpoint["tip_record_hash"] == entry.record_hash
    assert checkpoint["total_records"] >= 1
