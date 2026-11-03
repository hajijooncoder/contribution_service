import hashlib
import json
from datetime import datetime, timezone
from typing import Tuple, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.models import Submission, Review, User
from app.core.audit_ledger import CryptographicAuditLedger

HIGH_RISK_KEYWORDS = ["نسخ", "اصلاح", "ابطال", "تخصیص", "تقیید", "لغو"]

def evaluate_proposition_risk(document_type: str, legal_document_name: str, raw_legal_text: str) -> Tuple[str, int]:
    """
    Evaluates proposition risk based on Whitepaper 2.1 and Roadmap Phase 2:
    - High-Risk: Laws, treaties, or propositions involving repeals/amendments. Requires 2 independent reviewers.
    - Low-Risk: Minor bylaws, regulations, circulars without repeals. Requires 1 reviewer.
    Returns: (risk_level, required_reviewers)
    """
    text_content = f"{legal_document_name} {raw_legal_text}".lower()
    
    # Check if document type is high-risk or contains repeal/amendment keywords
    is_high_risk = (
        document_type in ["law", "treaty"] or
        any(kw in text_content for kw in HIGH_RISK_KEYWORDS)
    )
    
    if is_high_risk:
        return "HIGH", 2
    return "LOW", 1

def generate_tri_party_provenance_stamp(
    submission: Submission,
    reviewer_ids: List[str],
    consensus_score: float = 1.0
) -> dict:
    """Generates immutable Tri-party Provenance Stamp per Phase 4 of Roadmap."""
    now_iso = datetime.now(timezone.utc).isoformat()
    raw_payload = f"{submission.id}|{submission.submitter_id}|{','.join(sorted(reviewer_ids))}|{now_iso}"
    prov_hash = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

    return {
        "source_type": "COMMUNITY_CONTRIBUTION",
        "submission_id": submission.id,
        "contributor_id": submission.submitter_id,
        "verified_by": sorted(reviewer_ids),
        "quorum_size": len(reviewer_ids),
        "consensus_score": consensus_score,
        "approval_timestamp": now_iso,
        "staging_provenance_sha256": prov_hash
    }

class QuorumReviewFSM:
    """
    Strict Finite State Machine (FSM) enforcing risk-proportional consensus quorum
    and conflict of interest prevention.
    """

    @staticmethod
    def process_review_decision(
        db: Session,
        submission: Submission,
        reviewer: User,
        decision: str,
        reviewer_notes: Optional[str] = None,
        validation_result: Optional[str] = None
    ) -> Tuple[bool, str, str]:
        """
        Processes a reviewer vote with:
        1. Conflict of interest guard (submitter cannot review own work).
        2. Double-voting guard (same reviewer cannot review twice).
        3. Quorum evaluation (single approval for low-risk, 2 approvals for high-risk).
        4. Cryptographic audit chain logging.
        Returns: (success, new_status, message)
        """
        # 1. Conflict of Interest Check
        if reviewer.id == submission.submitter_id:
            return False, submission.status, "تعارض منافع: مشارکت‌کننده مجاز به داوری یا تأیید ارسال خود نیست."

        # 2. Existing review check (Double-voting prevention)
        existing_review = db.query(Review).filter(
            Review.submission_id == submission.id,
            Review.reviewer_id == reviewer.id
        ).first()
        if existing_review:
            return False, submission.status, "داوری تکراری: شما قبلاً نظر خود را درباره این سند ثبت کرده‌اید."

        # Serialize concurrent reviewer voting using database row-level locking
        try:
            locked_sub = db.query(Submission).filter(Submission.id == submission.id).with_for_update().first()
            if locked_sub:
                submission = locked_sub
        except Exception:
            pass

        # 3. Check current state eligibility under lock
        if submission.status in ["accepted", "rejected", "in_processing"]:
            return False, submission.status, f"تغییر وضعیت ناممکن است؛ سند در وضعیت قطعی '{submission.status}' قرار دارد."

        # Record this review
        review_record = Review(
            submission_id=submission.id,
            reviewer_id=reviewer.id,
            decision=decision,
            reviewer_notes=reviewer_notes,
            validation_result=validation_result or f"Vote: {decision}"
        )
        db.add(review_record)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            return False, submission.status, "داوری تکراری: نظر شما قبلاً برای این سند ثبت شده است."

        # 4. Handle State Transitions
        if decision == "reject":
            submission.status = "rejected"
            CryptographicAuditLedger.append_entry(
                db=db,
                actor_id=reviewer.id,
                action="REVIEW_REJECTED",
                target_id=submission.id,
                details=f"Rejected by {reviewer.email}: {reviewer_notes}"
            )
            return True, "rejected", "سند توسط داور رد شد."

        if decision == "request_correction":
            submission.status = "needs_correction"
            CryptographicAuditLedger.append_entry(
                db=db,
                actor_id=reviewer.id,
                action="REVIEW_NEEDS_CORRECTION",
                target_id=submission.id,
                details=f"Needs correction requested by {reviewer.email}: {reviewer_notes}"
            )
            return True, "needs_correction", "سند نیازمند اصلاح تشخیص داده شد."

        if decision == "approve":
            submission.current_approvals = (submission.current_approvals or 0) + 1
            
            # Check all approvals so far
            approvals = db.query(Review).filter(
                Review.submission_id == submission.id,
                Review.decision == "approve"
            ).all()
            approved_reviewer_ids = [r.reviewer_id for r in approvals]

            # Check if quorum threshold is satisfied
            if len(approved_reviewer_ids) >= submission.required_reviewers:
                submission.status = "accepted"
                submission.awarded_credits = submission.quality_score
                if submission.submitter:
                    submission.submitter.total_credits = (submission.submitter.total_credits or 0) + submission.awarded_credits

                # Stamp Tri-Party Provenance
                provenance = generate_tri_party_provenance_stamp(submission, approved_reviewer_ids)
                submission.provenance_stamp = json.dumps(provenance, ensure_ascii=False)

                CryptographicAuditLedger.append_entry(
                    db=db,
                    actor_id=reviewer.id,
                    action="QUORUM_REACHED_ACCEPTED",
                    target_id=submission.id,
                    details=f"Quorum ({len(approved_reviewer_ids)}/{submission.required_reviewers}) achieved. Provenance stamped."
                )
                return True, "accepted", f"حدنصاب داوری حاصل شد ({len(approved_reviewer_ids)} از {submission.required_reviewers}) و سند نهایی گردید."
            else:
                submission.status = "under_legal_review"
                CryptographicAuditLedger.append_entry(
                    db=db,
                    actor_id=reviewer.id,
                    action="REVIEW_VOTE_RECORDED",
                    target_id=submission.id,
                    details=f"Vote 1/{submission.required_reviewers} recorded by {reviewer.email}. Awaiting second independent review."
                )
                return True, "under_legal_review", f"رأی مثبت داور ثبت شد ({len(approved_reviewer_ids)} از {submission.required_reviewers}). در انتظار داوری همتای دوم."

        return False, submission.status, "تصمیم نامعتبر است."
