from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, require_admin
from app.db.models import User, Submission, UploadedFile, Review
from app.core.security import UserRole
from app.config import settings

router = APIRouter(prefix="/admin", tags=["Admin"])


class UserAdminOut(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    total_credits: int
    created_at: str


class UserListResponse(BaseModel):
    users: List[UserAdminOut]
    total: int


class UserActivationRequest(BaseModel):
    activate: bool


class UserRoleUpdateRequest(BaseModel):
    role: str = Field(..., pattern="^(contributor|reviewer|expert|admin)$")


class AdminOverviewStats(BaseModel):
    total_users: int
    total_submissions: int
    pending_reviews: int
    accepted_submissions: int
    rejected_submissions: int
    total_credits_awarded: int
    quarantine_files_count: int


class AdminExportOverview(BaseModel):
    total_export_ready: int
    schema_version: str = "mahoun-1.0"
    isolation_verified: bool = True
    export_token_configured: bool = True


@router.get("/users", response_model=UserListResponse)
def list_users(
    role: Optional[str] = Query(None, description="فیلتر بر اساس نقش"),
    is_active: Optional[bool] = Query(None, description="فیلتر کاربران فعال/غیرفعال"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """لیست جامع کاربران سیستم همراه با فیلتر نقش و وضعیت فعال بودن"""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active.is_(is_active))

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    return UserListResponse(
        users=[
            UserAdminOut(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                role=u.role,
                is_active=bool(u.is_active),
                total_credits=u.total_credits or 0,
                created_at=u.created_at.isoformat() if u.created_at else "",
            )
            for u in users
        ],
        total=total,
    )


@router.put("/users/{user_id}/activate")
def toggle_user_activation(
    user_id: str,
    payload: UserActivationRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """فعال یا غیرفعال‌سازی دسترسی کاربر"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="کاربر مورد نظر یافت نشد.",
        )

    if user.id == admin.id and not payload.activate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="مدیر ارشد نمی‌تواند حساب کاربری خود را غیرفعال کند.",
        )

    user.is_active = payload.activate
    db.commit()
    db.refresh(user)

    return {
        "user_id": user.id,
        "is_active": bool(user.is_active),
        "message": f"وضعیت کاربر به {'فعال' if user.is_active else 'غیرفعال'} تغییر یافت.",
    }


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    payload: UserRoleUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """ارتقا یا تغییر نقش کاربر در پلتفرم"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="کاربر مورد نظر یافت نشد.",
        )

    user.role = payload.role
    db.commit()
    db.refresh(user)

    return {
        "user_id": user.id,
        "role": user.role,
        "message": f"نقش کاربر به '{user.role}' ارتقا/تغییر یافت.",
    }


@router.get("/stats/overview", response_model=AdminOverviewStats)
def get_admin_overview_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """آمار جامع و نظارتی کل سیستم برای مدیر پلتفرم"""
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_submissions = db.query(func.count(Submission.id)).scalar() or 0
    pending_reviews = (
        db.query(func.count(Submission.id))
        .filter(Submission.status.in_(["submitted", "under_validation", "under_legal_review"]))
        .scalar()
        or 0
    )
    accepted_submissions = (
        db.query(func.count(Submission.id))
        .filter(Submission.status.in_(["accepted", "approved"]))
        .scalar()
        or 0
    )
    rejected_submissions = (
        db.query(func.count(Submission.id))
        .filter(Submission.status == "rejected")
        .scalar()
        or 0
    )
    total_credits = (
        db.query(func.sum(User.total_credits)).scalar() or 0
    )
    quarantine_files = (
        db.query(func.count(UploadedFile.id)).scalar() or 0
    )

    return AdminOverviewStats(
        total_users=total_users,
        total_submissions=total_submissions,
        pending_reviews=pending_reviews,
        accepted_submissions=accepted_submissions,
        rejected_submissions=rejected_submissions,
        total_credits_awarded=total_credits,
        quarantine_files_count=quarantine_files,
    )


@router.get("/export/overview", response_model=AdminExportOverview)
def get_admin_export_overview(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """گزارش آماری دیتاست آماده استخراج برای درگاه ایزوله مالک (Haji Mamad)"""
    total_export_ready = (
        db.query(func.count(Submission.id))
        .filter(Submission.status.in_(["accepted", "approved"]))
        .scalar()
        or 0
    )

    return AdminExportOverview(
        total_export_ready=total_export_ready,
        schema_version="mahoun-1.0",
        isolation_verified=True,
        export_token_configured=bool(settings.EXPORT_GATEWAY_TOKEN),
    )
