import hashlib
import json
from pathlib import Path
from typing import Optional, Generator
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.deps import get_db, verify_gateway_pull_token
from app.db.models import Submission, UploadedFile, Review, AuditLog
from app.core.audit_ledger import CryptographicAuditLedger
from app.core.exceptions import ExportGatewayError

router = APIRouter(prefix="/internal/export", tags=["Export Pull Gateway"])

MAX_EXPORT_LIMIT = 500
DEFAULT_EXPORT_LIMIT = 100

def compute_manifest_checksum(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def serialize_submission(sub: Submission, latest_review: Optional[Review], file_meta: Optional[dict]) -> dict:
    return {
        "submission_id": sub.id,
        "source_title": sub.source_title,
        "legal_document_name": sub.legal_document_name,
        "raw_legal_text": sub.raw_legal_text,
        "source_url": sub.source_url,
        "source_domain": sub.source_domain,
        "quality_score": sub.quality_score,
        "document_type": sub.document_type,
        "issuing_authority": sub.issuing_authority,
        "publication_info": sub.publication_info,
        "contributor_notes": sub.contributor_notes,
        "submitted_at": sub.created_at.isoformat(),
        "approved_at": sub.updated_at.isoformat(),
        "reviewer_id": latest_review.reviewer_id if latest_review else None,
        "file": file_meta,
    }

def get_file_meta(db: Session, file_upload_id: str) -> Optional[dict]:
    if not file_upload_id:
        return None
    f = db.query(UploadedFile).filter(UploadedFile.id == file_upload_id).first()
    if not f:
        return None
    return {
        "file_id": f.id,
        "original_filename": f.original_filename,
        "sha256_hash": f.sha256_hash,
        "file_size": f.file_size,
        "detected_mime": f.detected_mime,
    }

def get_latest_approval(db: Session, submission_id: str) -> Optional[Review]:
    return db.query(Review).filter(
        Review.submission_id == submission_id,
        Review.decision == "approve"
    ).order_by(Review.created_at.desc()).first()

@router.get("/approved-packages")
def get_approved_packages(
    cursor: Optional[str] = Query(None, description="Cursor for pagination (submission ID)"),
    limit: int = Query(DEFAULT_EXPORT_LIMIT, le=MAX_EXPORT_LIMIT),
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_gateway_pull_token)
):
    """
    PULL-BASED EXPORT GATEWAY with cursor-based pagination.
    Returns accepted submissions after the cursor.
    """
    query = db.query(Submission).filter(Submission.status == "accepted")
    
    if cursor:
        query = query.filter(Submission.id > cursor)
    
    submissions = query.order_by(Submission.id.asc()).limit(limit + 1).all()
    
    has_more = len(submissions) > limit
    if has_more:
        submissions = submissions[:limit]
    
    next_cursor = submissions[-1].id if submissions else None

    packages = []
    for sub in submissions:
        file_meta = get_file_meta(db, sub.file_upload_id)
        latest_review = get_latest_approval(db, sub.id)
        package_data = serialize_submission(sub, latest_review, file_meta)
        transit_hash = compute_manifest_checksum(package_data)
        packages.append({
            "manifest": package_data,
            "staging_transit_sha256": transit_hash
        })

    checkpoint = CryptographicAuditLedger.get_ledger_checkpoint(db)

    return {
        "count": len(packages),
        "packages": packages,
        "ledger_checkpoint": checkpoint,
        "pagination": {
            "next_cursor": next_cursor,
            "has_more": has_more,
            "limit": limit
        }
    }

@router.get("/approved-packages/stream")
def stream_approved_packages(
    limit: int = Query(MAX_EXPORT_LIMIT, le=MAX_EXPORT_LIMIT),
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_gateway_pull_token)
):
    """
    Streams approved packages as newline-delimited JSON for memory-efficient large exports.
    """
    def generate() -> Generator[bytes, None, None]:
        query = db.query(Submission).filter(Submission.status == "accepted").order_by(Submission.id.asc()).limit(limit)
        for sub in query.yield_per(50):
            file_meta = get_file_meta(db, sub.file_upload_id)
            latest_review = get_latest_approval(db, sub.id)
            package_data = serialize_submission(sub, latest_review, file_meta)
            transit_hash = compute_manifest_checksum(package_data)
            yield json.dumps({
                "manifest": package_data,
                "staging_transit_sha256": transit_hash
            }, ensure_ascii=False).encode("utf-8") + b"\n"
    
    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=mahoun_approved_packages.jsonl"}
    )

@router.get("/ledger-checkpoint")
def export_ledger_checkpoint(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_gateway_pull_token)
):
    return CryptographicAuditLedger.get_ledger_checkpoint(db)

@router.get("/dataset.jsonl")
def export_dataset_jsonl(
    cursor: Optional[str] = Query(None),
    limit: int = Query(DEFAULT_EXPORT_LIMIT, le=MAX_EXPORT_LIMIT),
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_gateway_pull_token)
):
    """
    Exports accepted legal submissions as JSONL with cursor pagination.
    """
    query = db.query(Submission).filter(Submission.status == "accepted")
    if cursor:
        query = query.filter(Submission.id > cursor)
    
    submissions = query.order_by(Submission.id.asc()).limit(limit + 1).all()
    has_more = len(submissions) > limit
    if has_more:
        submissions = submissions[:limit]
    
    next_cursor = submissions[-1].id if submissions else None

    lines = []
    for sub in submissions:
        record = {
            "id": sub.id,
            "title": sub.legal_document_name,
            "type": sub.document_type,
            "authority": sub.issuing_authority,
            "source_url": sub.source_url,
            "source_domain": sub.source_domain,
            "quality_score": sub.quality_score,
            "raw_text": sub.raw_legal_text,
            "approved_at": sub.updated_at.isoformat()
        }
        lines.append(json.dumps(record, ensure_ascii=False))

    content = "\n".join(lines) + ("\n" if lines else "")
    
    response = Response(
        content=content,
        media_type="application/x-ndjson; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=mahoun_approved_legal_dataset.jsonl"}
    )
    if next_cursor:
        response.headers["X-Next-Cursor"] = next_cursor
    response.headers["X-Has-More"] = str(has_more).lower()
    return response

@router.get("/dataset.jsonl/stream")
def stream_dataset_jsonl(
    limit: int = Query(MAX_EXPORT_LIMIT, le=MAX_EXPORT_LIMIT),
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_gateway_pull_token)
):
    """
    Streams dataset as JSONL for memory-efficient export.
    """
    def generate() -> Generator[bytes, None, None]:
        query = db.query(Submission).filter(Submission.status == "accepted").order_by(Submission.id.asc()).limit(limit)
        for sub in query.yield_per(50):
            record = {
                "id": sub.id,
                "title": sub.legal_document_name,
                "type": sub.document_type,
                "authority": sub.issuing_authority,
                "source_url": sub.source_url,
                "source_domain": sub.source_domain,
                "quality_score": sub.quality_score,
                "raw_text": sub.raw_legal_text,
                "approved_at": sub.updated_at.isoformat()
            }
            yield json.dumps(record, ensure_ascii=False).encode("utf-8") + b"\n"
    
    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=mahoun_approved_legal_dataset.jsonl"}
    )

@router.get("/dataset.txt", response_class=PlainTextResponse)
def export_dataset_txt(
    cursor: Optional[str] = Query(None),
    limit: int = Query(DEFAULT_EXPORT_LIMIT, le=MAX_EXPORT_LIMIT),
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_gateway_pull_token)
):
    query = db.query(Submission).filter(Submission.status == "accepted")
    if cursor:
        query = query.filter(Submission.id > cursor)
    
    submissions = query.order_by(Submission.id.asc()).limit(limit + 1).all()
    has_more = len(submissions) > limit
    if has_more:
        submissions = submissions[:limit]
    
    next_cursor = submissions[-1].id if submissions else None

    sections = []
    for idx, sub in enumerate(submissions, 1):
        sec = [
            "==================================================================",
            f"سند شماره: {idx} | شناسه: {sub.id}",
            f"عنوان: {sub.legal_document_name}",
            f"نوع سند: {sub.document_type} | مرجع صدور: {sub.issuing_authority}",
            f"منبع رسمی: {sub.source_domain} ({sub.source_url})",
            f"نمره کیفیت داده: {sub.quality_score}/100",
            f"تاریخ تایید: {sub.updated_at.strftime('%Y-%m-%d %H:%M')}",
            "------------------------------------------------------------------",
            sub.raw_legal_text,
            "==================================================================\n"
        ]
        sections.append("\n".join(sec))

    full_text = "\n\n".join(sections)
    response = PlainTextResponse(
        content=full_text,
        headers={"Content-Disposition": "attachment; filename=mahoun_legal_dataset.txt"}
    )
    if next_cursor:
        response.headers["X-Next-Cursor"] = next_cursor
    response.headers["X-Has-More"] = str(has_more).lower()
    return response

@router.get("/package-file/{file_id}")
def download_quarantined_file(
    file_id: str,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_gateway_pull_token)
):
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise ExportGatewayError("فایل پیوست یافت نشد.", status_code=404)

    file_path = Path(file_record.storage_path)
    if not file_path.exists():
        raise ExportGatewayError("فایل فیزیکی در قرنطینه یافت نشد.", status_code=404)

    return FileResponse(
        path=str(file_path),
        filename=file_record.original_filename,
        media_type=file_record.detected_mime,
        headers={
            "X-Content-SHA256": file_record.sha256_hash,
            "X-Original-Filename": file_record.original_filename,
        }
    )

@router.post("/mark-ingested/{submission_id}")
def mark_submission_ingested(
    submission_id: str,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_gateway_pull_token)
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise ExportGatewayError("مشارکت یافت نشد.", status_code=404)

    sub.status = "in_processing"
    
    CryptographicAuditLedger.append_entry(
        db=db,
        actor_id="SECURE_CORE_GATEWAY",
        action="PACKAGE_PULLED_BY_INTERNAL_CORE",
        target_id=sub.id,
        details="Package successfully pulled across unidirectional bridge into internal core."
    )
    db.commit()

    return {"status": "ok", "submission_id": sub.id, "new_status": "in_processing"}