from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.models import User
from app.schemas.auth import UserRegister, UserOut, UserRoleUpdate
from app.core.security import (
    get_password_hash, verify_password, create_access_token, UserRole,
    set_auth_cookies, clear_auth_cookies, generate_csrf_token, verify_csrf_token
)
from app.api.deps import get_db, get_current_user, require_admin
from app.core.rate_limiter import global_rate_limiter, get_client_ip

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, request: Request, response: Response, db: Session = Depends(get_db)):
    client_ip = get_client_ip(request)
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

    access_token = create_access_token(subject=new_user.id, role=new_user.role)
    csrf_token = generate_csrf_token()
    set_auth_cookies(response, access_token, csrf_token)
    
    return new_user

async def _login_user(identifier: str, password: str, request: Request, response: Response, db: Session) -> dict:
    client_ip = get_client_ip(request)
    if not global_rate_limiter.is_allowed(key=f"login_ip_{client_ip}", limit=20, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="تلاش‌های ورود بیش از حد مجاز است. لطفاً چند دقیقه دیگر امتحان کنید."
        )

    user = db.query(User).filter(User.email == identifier).first()
    if not user or not verify_password(password, user.hashed_password):
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
    csrf_token = generate_csrf_token()
    set_auth_cookies(response, access_token, csrf_token)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id
    }

@router.post("/login")
async def login(
    request: Request, 
    response: Response, 
    db: Session = Depends(get_db),
    username: str = Form(None),
    password: str = Form(None),
):
    if username is None or password is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="username and password required")
    return await _login_user(username, password, request, response, db)

@router.post("/token")
async def login_token(
    request: Request, 
    response: Response, 
    db: Session = Depends(get_db),
    username: str = Form(None),
    password: str = Form(None),
):
    # Handle form data
    if username is not None and password is not None:
        return await _login_user(username, password, request, response, db)
    
    # Handle JSON (backward compatibility)
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            email = body.get("email")
            password = body.get("password")
            if email and password:
                return await _login_user(email, password, request, response, db)
        except HTTPException:
            # Re-raise HTTP exceptions (like 401) instead of catching them
            raise
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"JSON parse error in login_token: {e}")
    
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="email and password required")

@router.post("/login/json")
async def login_json(
    login_data: LoginRequest,
    request: Request, 
    response: Response, 
    db: Session = Depends(get_db),
):
    return await _login_user(login_data.email, login_data.password, request, response, db)

@router.post("/logout")
def logout(request: Request, response: Response):
    clear_auth_cookies(response)
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/csrf-token")
def get_csrf_token(request: Request, response: Response):
    csrf_token = request.cookies.get("mahoun_csrf")
    if not csrf_token:
        csrf_token = generate_csrf_token()
        is_secure = request.url.scheme == "https"
        response.set_cookie(
            key="mahoun_csrf",
            value=csrf_token,
            httponly=False,
            secure=is_secure,
            samesite="strict",
            max_age=60 * 60 * 24,
            path="/",
        )
    return {"csrf_token": csrf_token}

@router.put("/users/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: str,
    role_update: UserRoleUpdate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        if not verify_csrf_token(request, request.headers.get("X-CSRF-Token", "")):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")
    
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