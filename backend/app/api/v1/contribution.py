import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.deps import get_db, get_current_user, get_optional_current_user, get_or_create_guest_user
from app.db.models import User, Submission, UploadedFile, Review
from app.schemas.submission import (
    SubmissionCreate,
    ContributionSubmissionOut,
    ContributionStats,
    ContributionHistoryItem,
    RecentActivityItem,
    UrlValidationRequest,
    UrlValidationResponse,
    EnhancedSubmissionRequest,
    EnhancedSubmissionResponse,
    EnhancedTextPreview,
    DuplicateCheckResult,
    TextChangeSchema,
    ExtractedMetadataSchema,
)
from app.core.quarantine import QuarantineManager
from app.core.text_preservation import sanitize_input_text, validate_legal_title
from app.core.text_enhancement import LegalTextEnhancer
from app.core.duplicate_detector import SmartDuplicateDetector
from app.core.source_validator import validate_official_legal_source_url
from app.core.scoring_engine import calculate_submission_quality_score
from app.core.audit_ledger import CryptographicAuditLedger
from app.core.fsm_quorum import evaluate_proposition_risk
from app.core.duplicate_detector import ExactDuplicateDetector
from app.core.text_enhancement import TextFingerprinter
from app.core.rate_limiter import global_rate_limiter, get_client_ip
from app.catalog.legal_catalog import get_legal_authorities, get_canonical_law_codes
from app.core.security import UserRole

router = APIRouter(prefix="/contribution", tags=["Contribution"])
quarantine_mgr = QuarantineManager()

@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Upload a legal document file into quarantine.
    Preserves exact byte-level integrity, calculates SHA-256,
    and isolates the file away from execution.
    """
    user = current_user or get_or_create_guest_user(db)
    client_ip = get_client_ip(request)
    
    # Anti-flood rate limiting (IP-based and User-based)
    if not global_rate_limiter.is_allowed(key=f"upload_ip_{client_ip}", limit=30, window_seconds=60) or \
       not global_rate_limiter.is_allowed(key=f"upload_user_{user.id}", limit=30, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="تعداد فایل‌های آپلودی بیش از حد مجاز است."
        )

    file_bytes = await file.read()
    try:
        quarantine_record = quarantine_mgr.process_and_quarantine(
            file_bytes=file_bytes,
            original_filename=file.filename or "uploaded_document"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    uploaded_file = UploadedFile(
        id=quarantine_record["file_id"],
        submitter_id=user.id,
        original_filename=quarantine_record["original_filename"],
        stored_filename=quarantine_record["stored_filename"],
        storage_path=quarantine_record["storage_path"],
        file_size=quarantine_record["file_size"],
        sha256_hash=quarantine_record["sha256_hash"],
        detected_mime=quarantine_record["detected_mime"],
        quarantine_status=quarantine_record["quarantine_status"],
    )
    db.add(uploaded_file)
    db.flush()
    
    CryptographicAuditLedger.append_entry(
        db=db,
        actor_id=user.id,
        action="FILE_UPLOAD_QUARANTINED",
        target_id=uploaded_file.id,
        details=f"SHA256={uploaded_file.sha256_hash}, Size={uploaded_file.file_size}, Mime={uploaded_file.detected_mime}"
    )
    db.commit()

    return {"file_id": uploaded_file.id}

@router.post("/submit", response_model=ContributionSubmissionOut, status_code=status.HTTP_201_CREATED)
def submit_contribution(
    request: Request,
    submission_in: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Submits a new legal source contribution to staging.
    Enforces official source domain validation, text preservation,
    and computes initial data quality score.
    """
    user = current_user or get_or_create_guest_user(db)
    client_ip = get_client_ip(request)

    # Anti-flood rate limiting (IP-based and User-based)
    if not global_rate_limiter.is_allowed(key=f"submit_ip_{client_ip}", limit=35, window_seconds=60) or \
       not global_rate_limiter.is_allowed(key=f"submit_user_{user.id}", limit=35, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="تعداد ارسال‌های مشارکت بیش از حد مجاز است. لطفاً کمی صبر کنید."
        )

    # 1. Enforce Official Legal Source Whitelist
    is_valid_source, authority_title, error_reason = validate_official_legal_source_url(submission_in.source_url)
    if not is_valid_source:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_reason
        )

    # 2. Validate legal document name
    clean_legal_doc_name = sanitize_input_text(submission_in.legal_document_name)
    if not validate_legal_title(clean_legal_doc_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="عنوان سند قانونی نامعتبر یا بسیار کوتاه است."
        )

    clean_source_title = sanitize_input_text(submission_in.source_title)
    clean_raw_text = sanitize_input_text(submission_in.raw_legal_text, max_length=500000)
    clean_notes = sanitize_input_text(submission_in.contributor_notes) if submission_in.contributor_notes else None
    clean_pub_info = sanitize_input_text(submission_in.publication_info) if submission_in.publication_info else None
    clean_authority = sanitize_input_text(submission_in.issuing_authority) or authority_title

    # 3. Check attached file if provided
    has_file = False
    if submission_in.file_upload_id:
        file_record = db.query(UploadedFile).filter(UploadedFile.id == submission_in.file_upload_id).first()
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="شناسه فایل پیوست یافت نشد."
            )
        has_file = True

    # 4. Calculate Data Quality Score
    quality_score, breakdown = calculate_submission_quality_score(
        source_url=submission_in.source_url,
        raw_legal_text=clean_raw_text,
        legal_document_name=clean_legal_doc_name,
        issuing_authority=clean_authority,
        publication_info=clean_pub_info,
        contributor_notes=clean_notes,
        has_file_attached=has_file
    )

    # 5. Evaluate Proposition Risk & Required Reviewer Quorum
    risk_level, required_reviewers = evaluate_proposition_risk(
        document_type=submission_in.document_type,
        legal_document_name=clean_legal_doc_name,
        raw_legal_text=clean_raw_text
    )

    # 6. Compute content_hash and fingerprint for duplicate detection
    content_hash = ExactDuplicateDetector.compute_hash(clean_raw_text)
    content_fingerprint = TextFingerprinter.compute_simhash(clean_raw_text)

    sub_id = str(uuid.uuid4())
    submission = Submission(
        id=sub_id,
        submitter_id=user.id,
        source_title=clean_source_title,
        legal_document_name=clean_legal_doc_name,
        raw_legal_text=clean_raw_text,
        source_url=submission_in.source_url.strip(),
        source_domain=authority_title,
        document_type=submission_in.document_type,
        issuing_authority=clean_authority,
        publication_info=clean_pub_info,
        contributor_notes=clean_notes,
        file_upload_id=submission_in.file_upload_id,
        quality_score=quality_score,
        awarded_credits=0,
        required_reviewers=required_reviewers,
        current_approvals=0,
        content_hash=content_hash,
        content_fingerprint=content_fingerprint,
        status="submitted",
    )
    db.add(submission)
    db.flush()
    
    CryptographicAuditLedger.append_entry(
        db=db,
        actor_id=user.id,
        action="CONTRIBUTION_SUBMITTED",
        target_id=sub_id,
        details=f"Document={clean_legal_doc_name}, Source={authority_title}, QualityScore={quality_score}, Risk={risk_level}, QuorumRequired={required_reviewers}"
    )
    db.commit()
    db.refresh(submission)

    return submission

@router.get("/stats", response_model=ContributionStats)
def get_stats(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Returns aggregated staging statistics and contributor credits."""
    total = db.query(func.count(Submission.id)).scalar() or 0
    pending = db.query(func.count(Submission.id)).filter(
        Submission.status.in_(["submitted", "under_validation", "under_legal_review"])
    ).scalar() or 0
    accepted = db.query(func.count(Submission.id)).filter(Submission.status == "accepted").scalar() or 0
    rejected = db.query(func.count(Submission.id)).filter(Submission.status == "rejected").scalar() or 0

    credits = current_user.total_credits if current_user else (
        db.query(func.sum(Submission.awarded_credits)).scalar() or 0
    )

    return ContributionStats(
        total_submissions=total,
        pending_submissions=pending,
        accepted_submissions=accepted,
        rejected_submissions=rejected,
        contribution_credits=credits
    )

@router.get("/recent-activity", response_model=List[RecentActivityItem])
def get_recent_activity(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns the most recent activities for the current authenticated user.
    Used by the main Dashboard for real-time progress tracking.
    """
    submissions = (
        db.query(Submission)
        .filter(Submission.submitter_id == current_user.id)
        .order_by(Submission.updated_at.desc())
        .limit(max(1, min(limit, 20)))
        .all()
    )
    return [
        RecentActivityItem(
            id=sub.id,
            title=sub.legal_document_name,
            status=sub.status,
            date=(sub.updated_at or sub.created_at).isoformat(),
            awarded_credits=sub.awarded_credits or 0
        )
        for sub in submissions
    ]

@router.get("/history", response_model=List[ContributionHistoryItem])
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns contribution history strictly for the authenticated submitter.
    Eliminates information leakage to anonymous or third-party callers.
    """
    submissions = (
        db.query(Submission)
        .filter(Submission.submitter_id == current_user.id)
        .order_by(Submission.created_at.desc())
        .limit(100)
        .all()
    )

    result = []
    for sub in submissions:
        latest_review = db.query(Review).filter(Review.submission_id == sub.id).order_by(Review.created_at.desc()).first()
        val_result = latest_review.validation_result if latest_review else None

        result.append(ContributionHistoryItem(
            id=sub.id,
            date=sub.created_at.strftime("%Y-%m-%d"),
            source=sub.legal_document_name or sub.source_title,
            status=sub.status,
            verification_result=val_result,
            earned_credits=sub.awarded_credits
        ))
    return result

@router.get("/status/{submission_id}", response_model=ContributionSubmissionOut)
def get_submission_status(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns status of a specific contribution submission.
    Enforces ownership isolation: only the document submitter, an authorized reviewer,
    or an administrator can inspect the submission details.
    """
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="شناسه مشارکت یافت نشد."
        )
    
    # Enforce IDOR protection
    if sub.submitter_id != current_user.id and current_user.role not in [UserRole.REVIEWER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="شما مجاز به مشاهده جزئیات این مشارکت نیستید."
        )
    return sub

@router.post("/validate-url", response_model=UrlValidationResponse)
def validate_url(
    payload: UrlValidationRequest,
):
    """
    اعتبارسنجی آنی و در لحظه آدرس منبع قانونی.
    بررسی تعلق دامنه به مراجع رسمی کشور و استخراج نام مرجع.
    """
    is_valid, authority, error = validate_official_legal_source_url(payload.url)
    return UrlValidationResponse(
        valid=is_valid,
        authority=authority if is_valid else None,
        error=error if not is_valid else None
    )

@router.get("/catalog/authorities")
def get_catalog_authorities():
    """Returns canonical reference list of legal authorities."""
    return get_legal_authorities()

@router.get("/catalog/codes")
def get_catalog_codes():
    """Returns canonical reference list of legal codes."""
    return get_canonical_law_codes()


@router.post("/submit/enhanced", response_model=EnhancedSubmissionResponse, status_code=status.HTTP_200_OK)
async def submit_enhanced_contribution(
    request: Request,
    submission_in: EnhancedSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Enhanced submission with text enhancement and duplicate detection"""
    user = current_user or get_or_create_guest_user(db)
    client_ip = get_client_ip(request)

    if not global_rate_limiter.is_allowed(key=f"submit_ip_{client_ip}", limit=35, window_seconds=60) or \
       not global_rate_limiter.is_allowed(key=f"submit_user_{user.id}", limit=35, window_seconds=60):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="تعداد ارسال‌های مشارکت بیش از حد مجاز است.")

    is_valid_source, authority_title, error_reason = validate_official_legal_source_url(submission_in.source_url)
    if not is_valid_source:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_reason)

    enhancer = LegalTextEnhancer()

    if submission_in.skip_enhancement:
        enhanced_text = submission_in.raw_legal_text
        enhancement_result = None
        quality_score_computed = 50
    else:
        try:
            enhancement_result = enhancer.enhance(
                raw_text=submission_in.raw_legal_text,
                title=submission_in.legal_document_name,
                document_type=submission_in.document_type
            )
            enhanced_text = enhancement_result.enhanced
            quality_score_computed = int(enhancement_result.quality_score)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"خطا در بهبود کیفیت متن: {str(e)}")

    detector = SmartDuplicateDetector(db, Submission)
    metadata_dict = {'title': submission_in.legal_document_name, 'document_type': submission_in.document_type, 'authority': authority_title}
    duplicate_report = detector.check_all_levels(text=enhanced_text, metadata=metadata_dict, title=submission_in.legal_document_name)

    if duplicate_report.is_duplicate and not submission_in.force_submit:
        duplicate_result = DuplicateCheckResult(
            is_duplicate=True, level=duplicate_report.level.value, similarity=duplicate_report.similarity,
            existing_id=duplicate_report.existing_id, message=duplicate_report.message,
            overlapping_submissions=[{"submission_id": o.submission_id, "overlapping_articles": o.overlapping_articles, "overlap_percentage": o.overlap_percentage} for o in duplicate_report.overlapping_submissions],
            related_versions=[{"submission_id": v.submission_id, "version_type": v.version_type, "confidence": v.confidence} for v in duplicate_report.related_versions]
        )
        return EnhancedSubmissionResponse(status="duplicate_detected", submission_id=None, enhanced_preview=None, duplicate_check=duplicate_result, message=f"هشدار: {duplicate_report.message}")

    if not submission_in.force_submit and enhancement_result:
        preview = EnhancedTextPreview(
            original_length=len(submission_in.raw_legal_text), enhanced_length=len(enhanced_text), changes_count=len(enhancement_result.changes),
            changes=[TextChangeSchema(line_number=ch.line_number, original=ch.original[:100], corrected=ch.corrected[:100], change_type=ch.change_type, reason=ch.reason) for ch in enhancement_result.changes[:10]],
            metadata=ExtractedMetadataSchema(article_count=enhancement_result.metadata.article_count, note_count=enhancement_result.metadata.note_count, clause_count=enhancement_result.metadata.clause_count,
                keywords=enhancement_result.metadata.keywords, references=enhancement_result.metadata.references, approval_date=enhancement_result.metadata.approval_date,
                legal_entities=enhancement_result.metadata.legal_entities, risk_level=enhancement_result.metadata.risk_level, detected_document_type=enhancement_result.metadata.detected_document_type),
            quality_score=enhancement_result.quality_score, fingerprint=enhancement_result.fingerprint, content_hash=enhancement_result.content_hash,
            suggested_improvements=[f"تشخیص {enhancement_result.metadata.article_count} ماده", f"استخراج {len(enhancement_result.metadata.keywords)} کلیدواژه", f"نمره: {enhancement_result.quality_score}/100"]
        )
        return EnhancedSubmissionResponse(status="preview", submission_id=None, enhanced_preview=preview, duplicate_check=None, message="پیش‌نمایش آماده است.")

    trad_quality, _ = calculate_submission_quality_score(source_url=submission_in.source_url, raw_legal_text=enhanced_text, legal_document_name=submission_in.legal_document_name,
        issuing_authority=authority_title, publication_info=submission_in.publication_info, contributor_notes=submission_in.contributor_notes, has_file_attached=False)
    risk_level, required_reviewers = evaluate_proposition_risk(document_type=submission_in.document_type, legal_document_name=submission_in.legal_document_name, raw_legal_text=enhanced_text)

    if enhancement_result:
        metadata_json = json.dumps({"article_count": enhancement_result.metadata.article_count, "note_count": enhancement_result.metadata.note_count, "keywords": enhancement_result.metadata.keywords,
            "references": enhancement_result.metadata.references, "risk_level": enhancement_result.metadata.risk_level}, ensure_ascii=False)
        changes_json = json.dumps([{"line": ch.line_number, "type": ch.change_type, "reason": ch.reason} for ch in enhancement_result.changes], ensure_ascii=False)
        content_hash, content_fingerprint, text_quality_score, detected_risk = enhancement_result.content_hash, enhancement_result.fingerprint, int(enhancement_result.quality_score), enhancement_result.metadata.risk_level
    else:
        # حتی اگر enhancement نداشتیم، باید content_hash رو برای duplicate detection محاسبه کنیم
        import hashlib
        content_hash = hashlib.sha256(enhanced_text.encode('utf-8')).hexdigest()
        metadata_json = changes_json = content_fingerprint = text_quality_score = None
        detected_risk = risk_level

    sub_id = str(uuid.uuid4())
    submission = Submission(id=sub_id, submitter_id=user.id, source_title=submission_in.source_title, legal_document_name=submission_in.legal_document_name, raw_legal_text=enhanced_text,
        source_url=submission_in.source_url, source_domain=authority_title, document_type=submission_in.document_type, issuing_authority=authority_title, publication_info=submission_in.publication_info,
        contributor_notes=submission_in.contributor_notes, quality_score=trad_quality, text_quality_score=text_quality_score, required_reviewers=required_reviewers, status="submitted",
        content_hash=content_hash, content_fingerprint=content_fingerprint, auto_extracted_metadata=metadata_json, enhancement_changes=changes_json, detected_risk_level=detected_risk)
    db.add(submission)
    db.flush()
    CryptographicAuditLedger.append_entry(db=db, actor_id=user.id, action="ENHANCED_CONTRIBUTION_SUBMITTED", target_id=sub_id,
        details=f"Document={submission_in.legal_document_name}, QualityScore={text_quality_score or 'N/A'}, DuplicateLevel={duplicate_report.level.value}")
    db.commit()
    db.refresh(submission)
    return EnhancedSubmissionResponse(status="submitted", submission_id=sub_id, enhanced_preview=None, duplicate_check=None, message=f"ثبت شد: {sub_id}")
