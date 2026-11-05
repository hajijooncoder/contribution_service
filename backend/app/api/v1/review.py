from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_reviewer
from app.db.models import User, Submission
from app.schemas.review import PendingReviewItem, ReviewDecision
from app.core.fsm_quorum import QuorumReviewFSM
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/contribution/review", tags=["Review"])

@router.get("/pending", response_model=List[PendingReviewItem])
def get_pending_reviews(
    db: Session = Depends(get_db),
    current_reviewer: User = Depends(require_reviewer)
):
    """
    Returns submissions pending legal review.
    Accessible strictly to users with Reviewer or Admin role.
    """
    pending = db.query(Submission).filter(
        Submission.status.in_(["submitted", "under_validation", "under_legal_review"])
    ).order_by(Submission.created_at.asc()).all()

    items = []
    for sub in pending:
        items.append(PendingReviewItem(
            id=sub.id,
            source_title=sub.source_title,
            legal_document_name=sub.legal_document_name,
            source_url=sub.source_url,
            document_type=sub.document_type,
            issuing_authority=sub.issuing_authority,
            submitted_by=sub.submitter.full_name if sub.submitter else "ناشناس",
            submitted_at=sub.created_at.strftime("%Y-%m-%d %H:%M"),
            validation_result=None
        ))
    return items

@router.post("/decision")
async def submit_review_decision(
    decision: ReviewDecision,
    db: Session = Depends(get_db),
    current_reviewer: User = Depends(require_reviewer)
):
    """
    Submits a review decision (approve / reject / request_correction).
    Updates the submission state machine and records review audit trail.
    """
    sub = db.query(Submission).filter(Submission.id == decision.submission_id).first()
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="شناسه مشارکت یافت نشد."
        )

    success, new_status, message = QuorumReviewFSM.process_review_decision(
        db=db,
        submission=sub,
        reviewer=current_reviewer,
        decision=decision.decision,
        reviewer_notes=decision.reviewer_notes,
        validation_result=decision.validation_result
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    db.commit()

    # Dispatch real-time WebSocket notification to submitter
    if sub.submitter_id:
        try:
            await ws_manager.send_personal_notification(
                sub.submitter_id,
                {
                    "type": "review_decision_update",
                    "submission_id": sub.id,
                    "title": sub.legal_document_name,
                    "new_status": new_status,
                    "decision": decision.decision,
                    "message": f"وضعیت مشارکت '{sub.legal_document_name}' به '{new_status}' تغییر یافت."
                }
            )
        except Exception:
            pass

    return {
        "status": "ok",
        "submission_id": sub.id,
        "new_status": new_status,
        "decision": decision.decision,
        "message": message
    }
