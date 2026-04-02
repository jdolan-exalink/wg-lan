import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    UserResponse,
)
from app.schemas.user import TokenResponse
from app.services.audit_service import log as audit_log
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    hash_password,
    revoke_all_user_tokens,
    revoke_refresh_token,
    verify_password,
    verify_refresh_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

COOKIE_NAME = "netloom_token"
REFRESH_COOKIE_NAME = "netloom_refresh"
CSRF_COOKIE_NAME = "csrf_token"
COOKIE_MAX_AGE = 60 * settings.access_token_expire_minutes  # Access token lifetime in seconds
REFRESH_COOKIE_MAX_AGE = 60 * 60 * 24 * settings.refresh_token_expire_days  # Refresh token lifetime in seconds


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(
        db,
        user.id,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )

    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=False,  # Set True behind HTTPS in production
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=REFRESH_COOKIE_MAX_AGE,
    )
    # CSRF token: readable by JS (not httpOnly)
    csrf_token = secrets.token_hex(32)
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
    )

    audit_log(
        db,
        "auth.login",
        user_id=user.id,
        target_type="user",
        target_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=COOKIE_MAX_AGE,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Refresh access token using refresh token with rotation."""
    old_refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not old_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    refresh_record = verify_refresh_token(db, old_refresh_token)
    if not refresh_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Revoke old refresh token (rotation)
    revoke_refresh_token(db, old_refresh_token)

    # Check if user is still active
    user = db.query(User).filter(User.id == refresh_record.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    # Issue new tokens
    access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(
        db,
        user.id,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )

    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=REFRESH_COOKIE_MAX_AGE,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=COOKIE_MAX_AGE,
    )


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if refresh_token:
        revoke_refresh_token(db, refresh_token)
    
    audit_log(db, "auth.logout", user_id=current_user.id, target_type="user", target_id=current_user.id)
    response.delete_cookie(COOKIE_NAME)
    response.delete_cookie(REFRESH_COOKIE_NAME)
    response.delete_cookie(CSRF_COOKIE_NAME)
    return MessageResponse(message="Logged out")


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    current_user.password_hash = hash_password(body.new_password)
    current_user.must_change_password = False
    db.commit()

    # Invalidate all sessions on password change
    revoke_all_user_tokens(db, current_user.id)

    audit_log(
        db,
        "auth.password_change",
        user_id=current_user.id,
        target_type="user",
        target_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return MessageResponse(message="Password changed successfully")


@router.get("/me")
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
