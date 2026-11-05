from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRole:
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"
    ADMIN = "admin"

COOKIE_NAME = "mahoun_auth"
CSRF_COOKIE_NAME = "mahoun_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password[:72], hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password[:72])

def create_access_token(subject: Union[str, Any], role: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)

def set_auth_cookies(response, access_token: str, csrf_token: str) -> None:
    is_secure = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

def clear_auth_cookies(response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/", secure=settings.ENVIRONMENT == "production", samesite="strict")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/", secure=settings.ENVIRONMENT == "production", samesite="strict")

def verify_csrf_token(request, csrf_token: str) -> bool:
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    return cookie_token is not None and secrets.compare_digest(cookie_token, csrf_token)