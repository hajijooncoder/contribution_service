import hashlib
import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session
from app.api.deps import get_db, verify_gateway_pull_token
from app.db.models import Submission, UploadedFile, Review, AuditLog
from app.core.audit_ledger import CryptographicAuditLedger

router = APIRouter(prefix="/internal/export", tags=["Export Pull Gateway"])

def compute_manifest_checksum(payload: dict) -> str:
    """Computes SHA-256 checksum over normalized JSON payload for transit integrity."""
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

@router.get("/approved-packages")
def get_approved_packages(
    since_timestamp: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_gateway_pull_token)
):
    """
    PULL-BASED EXPORT GATEWAY:
    Invoked by the internal protected Mahoun core (or manual admin export tool)
    to pull accepted legal packages.
    """
    query = db.query(Submission).filter(Submission.status == "accepted")
    submissions = query.order_by(Submission.updated_at.asc()).limit(limit).all()
    
    packages = []
    for sub in submissions:
        file_meta = None
        if sub.file_upload_id:
            f = db.query(UploadedFile).filter(UploadedFile.id == sub.file_upload_id).first()
            if f:
                file_meta = {
                    "file_id": f.id,
                    "original_filename": f.original_filename,
                    "sha256_hash": f.sha256_hash,
                    "file_size": f.file_size,
                    "detected_mime": f.detected_mime,
                }
        
        latest_review = db.query(Review).filter(
            Review.submission_id == sub.id,
            Review.decision == "approve"
        ).order_by(Review.created_at.desc()).first()

        package_data = {
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

        transit_hash = compute_manifest_checksum(package_data)
        
        packages.append({
            "manifest": package_data,
            "staging_transit_sha256": transit_hash
        })

    checkpoint = CryptographicAuditLedger.get_ledger_checkpoint(db)

    return {
        "count": len(packages),
        "packages": packages,
        "ledger_checkpoint": checkpoint
    }

@router.get("/ledger-checkpoint")
def export_ledger_checkpoint(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_gateway_pull_token)
):
    """
    Returns the latest cryptographic checkpoint of the staging audit ledger
    for external witness anchoring and verification by the internal core.
    """
    return CryptographicAuditLedger.get_ledger_checkpoint(db)

@router.get("/dataset.jsonl")
def export_dataset_jsonl(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_gateway_pull_token)
):
    """
    Exports all accepted legal submissions as a clean JSONL dataset,
    ready for offline inspection, manual review, and high-quality knowledge graph feeding.
    """
    submissions = db.query(Submission).filter(Submission.status == "accepted").order_by(Submission.updated_at.asc()).all()
    
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

    content = "\n".join(lines)
    return Response(
        content=content,
        media_type="application/x-ndjson; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=mahoun_approved_legal_dataset.jsonl"}
    )

@router.get("/dataset.txt", response_class=PlainTextResponse)
def export_dataset_txt(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_gateway_pull_token)
):
    """
    Exports all accepted legal submissions as a single human-readable clean text file,
    separated by standard section dividers for direct manual inspection.
    """
    submissions = db.query(Submission).filter(Submission.status == "accepted").order_by(Submission.updated_at.asc()).all()
    
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
    return PlainTextResponse(
        content=full_text,
        headers={"Content-Disposition": "attachment; filename=mahoun_legal_dataset.txt"}
    )

@router.get("/package-file/{file_id}")
def download_quarantined_file(
    file_id: str,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_gateway_pull_token)
):
    """
    Streams raw quarantined file bytes.
    Enforces exact SHA-256 header for recipient verification.
    """
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="فایل پیوست یافت نشد."
        )

    file_path = Path(file_record.storage_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="فایل فیزیکی در قرنطینه یافت نشد."
        )

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
    """
    Acknowledges receipt and ingestion by internal secure core or manual workflow.
    Transitions staging status to 'in_processing'.
    """
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="مشارکت یافت نشد.")

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
