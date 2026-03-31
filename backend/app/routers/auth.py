import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    UserResponse,
)
from app.services.audit_service import log as audit_log
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

COOKIE_NAME = "wg_lan_token"
CSRF_COOKIE_NAME = "csrf_token"
COOKIE_MAX_AGE = 60 * 60 * 24  # 24 hours


@router.post("/login")
def login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> UserResponse:
    user = authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(user.id)
    csrf_token = secrets.token_hex(32)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,  # Set True behind HTTPS in production
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
    )
    # CSRF token: readable by JS (not httpOnly)
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
    )

    audit_log(db, "auth.login", user_id=user.id, target_type="user", target_id=user.id)
    return UserResponse.model_validate(user)


@router.post("/logout")
def logout(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    audit_log(db, "auth.logout", user_id=current_user.id)
    response.delete_cookie(COOKIE_NAME)
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

    audit_log(db, "auth.password_change", user_id=current_user.id, target_type="user", target_id=current_user.id)
    return MessageResponse(message="Password changed successfully")


@router.get("/me")
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
