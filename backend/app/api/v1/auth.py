from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.db.models import User
from app.schemas.auth import UserRegister, UserLogin, Token, UserOut, UserRoleUpdate
from app.core.security import get_password_hash, verify_password, create_access_token, UserRole
from app.api.deps import get_db, get_current_user, require_admin
from app.core.rate_limiter import global_rate_limiter, get_client_ip

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, request: Request, db: Session = Depends(get_db)):
    client_ip = get_client_ip(request)
    # Anti-Sybil / Anti-flood rate limiting per IP
    if not global_rate_limiter.is_allowed(key=f"register_ip_{client_ip}", limit=10, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="تعداد درخواست‌های ثبت‌نام از این آدرس بیش از حد مجاز است."
        )

    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    # HARDCODED: Public self-registration ALWAYS creates standard CONTRIBUTOR accounts.
    # Privileged roles (reviewer, admin) require offline promotion or authenticated admin approval.
    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=UserRole.CONTRIBUTOR,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/token", response_model=Token)
def login(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    client_ip = get_client_ip(request)
    # Brute-force protection on login
    if not global_rate_limiter.is_allowed(key=f"login_ip_{client_ip}", limit=20, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="تلاش‌های ورود بیش از حد مجاز است. لطفاً چند دقیقه دیگر امتحان کنید."
        )

    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account."
        )
    access_token = create_access_token(subject=user.id, role=user.role)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id
    }

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/users/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: str,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Administrative role promotion endpoint.
    Strictly requires active administrator authentication.
    """
    target_role = role_update.role
    if target_role not in [UserRole.CONTRIBUTOR, UserRole.REVIEWER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"نقش نامعتبر است. نقش‌های مجاز: {UserRole.CONTRIBUTOR}, {UserRole.REVIEWER}, {UserRole.ADMIN}"
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="کاربر یافت نشد.")
    
    user.role = target_role
    db.commit()
    db.refresh(user)
    return user
