from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ── User Schemas ──────────────────────────────────────────────

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    email: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False


class UserCreateRequest(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    password_confirm: str = Field(..., min_length=8, max_length=128)


class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class UserChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    new_password_confirm: str = Field(..., min_length=8, max_length=128)


class UserResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_active: bool
    is_admin: bool
    must_change_password: bool
    onboarding_completed: bool
    last_login_at: Optional[datetime] = None
    last_failed_login_at: Optional[datetime] = None
    failed_login_count: int = 0
    created_at: datetime
    updated_at: datetime
    auth_source: str = "local"

    model_config = {"from_attributes": True}


class UserDetailResponse(UserResponse):
    groups: list[GroupSummary] = []


class GroupSummary(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Group Assignment Schemas ─────────────────────────────────

class UserGroupAssignRequest(BaseModel):
    group_ids: list[int] = Field(..., min_length=1)


# ── Network Assignment Schemas ───────────────────────────────

class UserNetworkAssignment(BaseModel):
    id: int
    network_id: int
    network_name: str
    subnet: str
    network_type: str
    action: str

    model_config = {"from_attributes": True}


class UserNetworkAssignmentCreate(BaseModel):
    network_id: int
    action: str = "allow"  # 'allow' or 'deny'


# ── Login/Refresh Schemas ────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class MessageResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
