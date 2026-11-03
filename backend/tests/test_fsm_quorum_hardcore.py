"""
FSM Consensus Quorum and Provenance Integrity Hardcore Test Suite.
تست‌های بشدت دقیق و سخت‌گیرانه برای ماشین حالات متناهی (FSM)، حدنصاب داوری متناسب با ریسک حقوقی،
جلوگیری از تعارض منافع، ممانعت از رأی مضاعف، محاسبه امتیازات و مهر اصالت سه‌جانبه (Tri-Party Provenance).
"""

import json
import hashlib
import uuid
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi.testclient import TestClient

from app.core.fsm_quorum import (
    QuorumReviewFSM,
    evaluate_proposition_risk,
    generate_tri_party_provenance_stamp,
    HIGH_RISK_KEYWORDS,
)
from app.db.models import Submission, Review, User
from app.core.security import UserRole, get_password_hash, create_access_token


# ==============================================================================
# ۱. تست‌های دقیق طبقه‌بندی ریسک حقوقی اسناد (Proposition Risk)
# ==============================================================================

def test_law_and_treaty_are_always_high_risk():
    """قوانین و معاهدات بین‌المللی ذاتاً ریسک بالا دارند و نیازمند ۲ داور مستقل هستند."""
    risk1, quorum1 = evaluate_proposition_risk(
        document_type="law",
        legal_document_name="قانون بهبود مستمر محیط کسب و کار",
        raw_legal_text="ماده ۱: تعاریف و اصطلاحات..."
    )
    assert risk1 == "HIGH"
    assert quorum1 == 2

    risk2, quorum2 = evaluate_proposition_risk(
        document_type="treaty",
        legal_document_name="کنوانسیون بین‌المللی مبارزه با دوپینگ",
        raw_legal_text="ماده ۱: تعهدات دول عضو..."
    )
    assert risk2 == "HIGH"
    assert quorum2 == 2


@pytest.mark.parametrize("doc_type", ["regulation", "bylaw", "circular", "verdict", "other"])
def test_minor_documents_without_repeal_are_low_risk(doc_type):
    """مقررات، آیین‌نامه‌ها و بخشنامه‌های عادی بدون کلمات تغییردهنده یا ناسخ، تک‌داوره هستند."""
    risk, quorum = evaluate_proposition_risk(
        document_type=doc_type,
        legal_document_name="دستورالعمل اداری نحوه حضور و غیاب کارکنان",
        raw_legal_text="ماده ۱: تمامی کارکنان موظف به ثبت ساعت ورود و خروج هستند."
    )
    assert risk == "LOW"
    assert quorum == 1


@pytest.mark.parametrize("kw", HIGH_RISK_KEYWORDS)
def test_high_risk_keywords_elevate_quorum(kw):
    """وجود کلمات کلیدی پرخطر حقوقی (مانند نسخ، ابطال، اصلاح، تخصیص) حدنصاب را به ۲ داور ارتقا می‌دهد."""
    # حتی اگر سند آیین‌نامه باشد، با داشتن کلمه کلیدی پرخطر در متن، ریسک بالا می‌شود
    risk, quorum = evaluate_proposition_risk(
        document_type="regulation",
        legal_document_name="تصویب‌نامه شماره ۴۰۵",
        raw_legal_text=f"ماده ۱۰: این آیین‌نامه موجب {kw} مصوبه قبلی هیأت وزیران می‌گردد."
    )
    assert risk == "HIGH"
    assert quorum == 2


def test_high_risk_keyword_in_title_elevates_risk():
    """اگر کلمه پرخطر (مثلاً ابطال یا اصلاح) در عنوان سند باشد نیز ریسک باید HIGH شود."""
    risk, quorum = evaluate_proposition_risk(
        document_type="bylaw",
        legal_document_name="آیین‌نامه اصلاح ساختار نظام بانکی کشور",
        raw_legal_text="ماده ۱: متن عادی و غیرحساس."
    )
    assert risk == "HIGH"
    assert quorum == 2


# ==============================================================================
# ۲. تست‌های جلوگیری از تعارض منافع و رأی مضاعف (Conflict of Interest & Sybil)
# ==============================================================================

def test_submitter_cannot_review_own_submission(db_session: Session):
    """مشارکت‌کننده تحت هیچ شرایطی نمی‌تواند به ارسال خود رأی مثبت، منفی یا اصلاحیه بدهد."""
    submitter = User(
        id=str(uuid.uuid4()),
        email="submitter_author@example.com",
        hashed_password="hash",
        full_name="نویسنده سند",
        role=UserRole.REVIEWER,  # حتی اگر نقش کاربر داور باشد!
        is_active=True,
    )
    db_session.add(submitter)
    db_session.commit()

    sub = Submission(
        id=str(uuid.uuid4()),
        submitter_id=submitter.id,
        source_title="سند تستی",
        legal_document_name="ماده ۱ قانون تستی",
        raw_legal_text="متن تستی ماده یک",
        source_url="https://rooznamehrasmi.ir/test",
        source_domain="روزنامه رسمی",
        document_type="law",
        issuing_authority="مجلس",
        required_reviewers=2,
        status="submitted",
    )
    db_session.add(sub)
    db_session.commit()

    # ۱. تلاش برای تایید
    ok, status, msg = QuorumReviewFSM.process_review_decision(
        db=db_session,
        submission=sub,
        reviewer=submitter,
        decision="approve",
    )
    assert ok is False
    assert status == "submitted"
    assert "تعارض منافع" in msg

    # ۲. تلاش برای رد
    ok2, status2, msg2 = QuorumReviewFSM.process_review_decision(
        db=db_session,
        submission=sub,
        reviewer=submitter,
        decision="reject",
    )
    assert ok2 is False
    assert status2 == "submitted"
    assert "تعارض منافع" in msg2


def test_reviewer_cannot_vote_twice(db_session: Session):
    """داور مجاز به ثبت بیش از یک رأی روی یک سند واحد نیست (Double Voting Prevention)."""
    submitter = User(
        id=str(uuid.uuid4()),
        email="sub_user_unique@example.com",
        hashed_password="hash",
        full_name="مشارکت‌کننده",
        role=UserRole.CONTRIBUTOR,
        is_active=True,
    )
    reviewer = User(
        id=str(uuid.uuid4()),
        email="single_reviewer@example.com",
        hashed_password="hash",
        full_name="داور شماره ۱",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    db_session.add_all([submitter, reviewer])
    db_session.commit()

    sub = Submission(
        id=str(uuid.uuid4()),
        submitter_id=submitter.id,
        source_title="سند داوری",
        legal_document_name="ماده ۵",
        raw_legal_text="متن ماده ۵ قانون",
        source_url="https://rc.majlis.ir/test",
        source_domain="مجلس",
        document_type="law",
        issuing_authority="مجلس",
        required_reviewers=2,
        status="submitted",
    )
    db_session.add(sub)
    db_session.commit()

    # رأی اول: باید با موفقیت ثبت شود
    ok1, status1, _ = QuorumReviewFSM.process_review_decision(
        db=db_session,
        submission=sub,
        reviewer=reviewer,
        decision="approve",
        reviewer_notes="تایید اولیه",
    )
    assert ok1 is True
    assert status1 == "under_legal_review"
    db_session.commit()

    # رأی دوم با همان داور: باید رد شود
    ok2, status2, msg2 = QuorumReviewFSM.process_review_decision(
        db=db_session,
        submission=sub,
        reviewer=reviewer,
        decision="approve",
        reviewer_notes="تلاش برای رأی دوباره",
    )
    assert ok2 is False
    assert status2 == "under_legal_review"
    assert "داوری تکراری" in msg2


def test_database_unique_constraint_blocks_duplicate_review(db_session: Session):
    """بررسی اینکه قید یکتایی دیتابیس (uq_submission_reviewer) از درج همزمان جلوگیری می‌کند."""
    sub_id = str(uuid.uuid4())
    rev_id = str(uuid.uuid4())

    r1 = Review(
        id=str(uuid.uuid4()),
        submission_id=sub_id,
        reviewer_id=rev_id,
        decision="approve",
    )
    db_session.add(r1)
    db_session.commit()

    r2 = Review(
        id=str(uuid.uuid4()),
        submission_id=sub_id,
        reviewer_id=rev_id,
        decision="reject",
    )
    db_session.add(r2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ==============================================================================
# ۳. تست‌های حدنصاب اسناد کم‌ریسک (Low-Risk Quorum: 1 Reviewer)
# ==============================================================================

def test_low_risk_single_approval_flow(db_session: Session):
    """سند تک‌داوره با یک تأیید مستقیماً به وضعیت accepted می‌رود و امتیاز تخصیص می‌یابد."""
    submitter = User(
        id=str(uuid.uuid4()),
        email="contributor_low@example.com",
        hashed_password="hash",
        full_name="مشارکت‌کننده کم‌ریسک",
        role=UserRole.CONTRIBUTOR,
        total_credits=10,
        is_active=True,
    )
    reviewer = User(
        id=str(uuid.uuid4()),
        email="reviewer_low@example.com",
        hashed_password="hash",
        full_name="داور مقررات",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    db_session.add_all([submitter, reviewer])
    db_session.commit()

    sub = Submission(
        id=str(uuid.uuid4()),
        submitter_id=submitter.id,
        source_title="بخشنامه اجرایی",
        legal_document_name="بخشنامه شماره ۱۰ امور مالی",
        raw_legal_text="متن بخشنامه مالی بدون ریسک",
        source_url="https://dotic.ir/test",
        source_domain="داتیک",
        document_type="circular",
        issuing_authority="معاونت حقوقی",
        quality_score=85,
        required_reviewers=1,
        current_approvals=0,
        status="submitted",
    )
    db_session.add(sub)
    db_session.commit()

    ok, new_status, msg = QuorumReviewFSM.process_review_decision(
        db=db_session,
        submission=sub,
        reviewer=reviewer,
        decision="approve",
        reviewer_notes="بسیار عالی و منطبق با منبع",
    )
    db_session.commit()

    assert ok is True
    assert new_status == "accepted"
    assert sub.status == "accepted"
    assert sub.awarded_credits == 85
    assert submitter.total_credits == 95  # 10 + 85
    assert sub.provenance_stamp is not None

    # بررسی ساختار مهر اصالت
    stamp = json.loads(sub.provenance_stamp)
    assert stamp["source_type"] == "COMMUNITY_CONTRIBUTION"
    assert stamp["submission_id"] == sub.id
    assert stamp["contributor_id"] == submitter.id
    assert stamp["verified_by"] == [reviewer.id]
    assert stamp["quorum_size"] == 1
    assert len(stamp["staging_provenance_sha256"]) == 64


# ==============================================================================
# ۴. تست‌های حدنصاب اسناد پرریسک (High-Risk Quorum: 2 Independent Reviewers)
# ==============================================================================

def test_high_risk_two_stage_quorum_lifecycle(db_session: Session):
    """
    چرخه حیات کامل سند پرریسک (قانون با نسخ):
    داور اول تأیید می‌کند -> وضعیت under_legal_review (امتیاز داده نمی‌شود)
    داور دوم تأیید می‌کند -> حدنصاب کامل، وضعیت accepted، تخصیص اعتبار و درج مهر اصالت
    """
    sub_user = User(
        id=str(uuid.uuid4()),
        email="sub_lawyer@example.com",
        hashed_password="hash",
        full_name="وکیل مشارکت‌کننده",
        role=UserRole.CONTRIBUTOR,
        total_credits=0,
        is_active=True,
    )
    rev1 = User(
        id=str(uuid.uuid4()),
        email="rev_first@example.com",
        hashed_password="hash",
        full_name="داور ارشد ۱",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    rev2 = User(
        id=str(uuid.uuid4()),
        email="rev_second@example.com",
        hashed_password="hash",
        full_name="داور ارشد ۲",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    db_session.add_all([sub_user, rev1, rev2])
    db_session.commit()

    sub = Submission(
        id=str(uuid.uuid4()),
        submitter_id=sub_user.id,
        source_title="قانون مبارزه با قاچاق کالا",
        legal_document_name="ماده ۵۵ قانون قاچاق (موجب نسخ قانون قبلی)",
        raw_legal_text="ماده ۵۵: با تصویب این قانون کلیه احکام مغایر در قانون سال ۱۳۱۲ ملغی‌الاثر می‌گردد.",
        source_url="https://rc.majlis.ir/law/show/55",
        source_domain="مرکز پژوهش‌ها",
        document_type="law",
        issuing_authority="مجلس شورای اسلامی",
        quality_score=90,
        required_reviewers=2,
        current_approvals=0,
        status="submitted",
    )
    db_session.add(sub)
    db_session.commit()

    # مرحله ۱: داوری داور اول
    ok1, status1, _ = QuorumReviewFSM.process_review_decision(
        db=db_session,
        submission=sub,
        reviewer=rev1,
        decision="approve",
        reviewer_notes="تایید صحت توسط داور ۱",
    )
    db_session.commit()

    assert ok1 is True
    assert status1 == "under_legal_review"
    assert sub.status == "under_legal_review"
    assert sub.current_approvals == 1
    assert sub.awarded_credits == 0  # نباید هنوز اعتباری دریافت شده باشد
    assert sub_user.total_credits == 0
    assert sub.provenance_stamp is None

    # مرحله ۲: داوری داور دوم
    ok2, status2, _ = QuorumReviewFSM.process_review_decision(
        db=db_session,
        submission=sub,
        reviewer=rev2,
        decision="approve",
        reviewer_notes="تایید دوم و نهایی‌سازی حدنصاب",
    )
    db_session.commit()

    assert ok2 is True
    assert status2 == "accepted"
    assert sub.status == "accepted"
    assert sub.current_approvals == 2
    assert sub.awarded_credits == 90
    assert sub_user.total_credits == 90
    assert sub.provenance_stamp is not None

    stamp = json.loads(sub.provenance_stamp)
    assert stamp["quorum_size"] == 2
    assert sorted(stamp["verified_by"]) == sorted([rev1.id, rev2.id])


def test_rejection_after_partial_approval(db_session: Session):
    """اگر داور اول تایید کند ولی داور دوم رد کند، سند قطعا رد (rejected) می‌شود."""
    sub_user = User(id=str(uuid.uuid4()), email="sub_u@test.ir", hashed_password="h", full_name="کاربر", role=UserRole.CONTRIBUTOR, is_active=True)
    rev1 = User(id=str(uuid.uuid4()), email="r1@test.ir", hashed_password="h", full_name="داور۱", role=UserRole.REVIEWER, is_active=True)
    rev2 = User(id=str(uuid.uuid4()), email="r2@test.ir", hashed_password="h", full_name="داور۲", role=UserRole.REVIEWER, is_active=True)
    db_session.add_all([sub_user, rev1, rev2])
    db_session.commit()

    sub = Submission(
        id=str(uuid.uuid4()),
        submitter_id=sub_user.id,
        source_title="سند قانون",
        legal_document_name="ماده رد شدنی",
        raw_legal_text="متن",
        source_url="https://qavanin.ir/t",
        source_domain="قوانین",
        document_type="law",
        issuing_authority="مجلس",
        required_reviewers=2,
        status="submitted",
    )
    db_session.add(sub)
    db_session.commit()

    # رأی داور ۱: تایید
    QuorumReviewFSM.process_review_decision(db_session, sub, rev1, "approve")
    db_session.commit()
    assert sub.status == "under_legal_review"

    # رأی داور ۲: رد
    ok, st, msg = QuorumReviewFSM.process_review_decision(db_session, sub, rev2, "reject", "سند دارای مغایرت اساسی با نسخه اصلی است")
    db_session.commit()
    assert ok is True
    assert st == "rejected"
    assert sub.status == "rejected"
    assert sub.awarded_credits == 0


def test_request_correction_flow(db_session: Session):
    """درخواست اصلاح توسط داور باید وضعیت را به needs_correction تغییر دهد."""
    sub_user = User(id=str(uuid.uuid4()), email="sub_corr@test.ir", hashed_password="h", full_name="کاربر", role=UserRole.CONTRIBUTOR, is_active=True)
    rev = User(id=str(uuid.uuid4()), email="r_corr@test.ir", hashed_password="h", full_name="داور", role=UserRole.REVIEWER, is_active=True)
    db_session.add_all([sub_user, rev])
    db_session.commit()

    sub = Submission(
        id=str(uuid.uuid4()),
        submitter_id=sub_user.id,
        source_title="سند نیازمند اصلاح",
        legal_document_name="ماده ۸",
        raw_legal_text="متن ناقص",
        source_url="https://qavanin.ir/corr",
        source_domain="قوانین",
        document_type="law",
        issuing_authority="مجلس",
        required_reviewers=1,
        status="submitted",
    )
    db_session.add(sub)
    db_session.commit()

    ok, st, msg = QuorumReviewFSM.process_review_decision(db_session, sub, rev, "request_correction", "لطفا شماره تبصره اصلاح شود")
    db_session.commit()
    assert ok is True
    assert st == "needs_correction"
    assert sub.status == "needs_correction"


# ==============================================================================
# ۵. تست‌های وضعیت‌های پایانی و غیرقابل برگشت (Terminal States Enforcement)
# ==============================================================================

@pytest.mark.parametrize("terminal_status", ["accepted", "rejected", "in_processing"])
def test_terminal_states_cannot_be_reviewed(db_session: Session, terminal_status):
    """سند در وضعیت‌های قطعی (نهایی، رد شده، یا در حال پردازش داخلی) نباید مجدداً قابل داوری باشد."""
    sub_user = User(id=str(uuid.uuid4()), email=f"user_{terminal_status}@test.ir", hashed_password="h", full_name="کاربر", role=UserRole.CONTRIBUTOR, is_active=True)
    rev = User(id=str(uuid.uuid4()), email=f"rev_{terminal_status}@test.ir", hashed_password="h", full_name="داور", role=UserRole.REVIEWER, is_active=True)
    db_session.add_all([sub_user, rev])
    db_session.commit()

    sub = Submission(
        id=str(uuid.uuid4()),
        submitter_id=sub_user.id,
        source_title="سند وضعیت قطعی",
        legal_document_name="ماده نهایی",
        raw_legal_text="متن نهایی",
        source_url="https://qavanin.ir/term",
        source_domain="قوانین",
        document_type="law",
        issuing_authority="مجلس",
        status=terminal_status,
    )
    db_session.add(sub)
    db_session.commit()

    ok, st, msg = QuorumReviewFSM.process_review_decision(db_session, sub, rev, "approve")
    assert ok is False
    assert st == terminal_status
    assert "تغییر وضعیت ناممکن است" in msg


# ==============================================================================
# ۶. تست‌های احراز هویت و دسترسی لایه API داوری
# ==============================================================================

def test_contributor_cannot_access_review_queue(client: TestClient, contributor_headers):
    """کاربر عادی مشارکت‌کننده نباید به صف داوری یا ارسال نظر دسترسی داشته باشد (HTTP 403)."""
    resp = client.get("/api/v1/contribution/review/pending", headers=contributor_headers)
    assert resp.status_code == 403
    assert "Reviewer permissions required" in resp.json()["detail"]


def test_reviewer_can_access_review_queue(client: TestClient, reviewer_headers):
    """کاربر با نقش داور باید به صف داوری دسترسی داشته باشد (HTTP 200)."""
    resp = client.get("/api/v1/contribution/review/pending", headers=reviewer_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_review_decision_nonexistent_submission_404(client: TestClient, reviewer_headers):
    """ارسال نظر برای شناسه سند ناموجود باید خطای ۴۰۴ بازگرداند."""
    payload = {
        "submission_id": "nonexistent-uuid-1234",
        "decision": "approve",
        "reviewer_notes": "تایید سند موهوم",
    }
    resp = client.post("/api/v1/contribution/review/decision", json=payload, headers=reviewer_headers)
    assert resp.status_code == 404
    assert "یافت نشد" in resp.json()["detail"]
