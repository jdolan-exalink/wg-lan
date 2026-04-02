from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Device Schemas ────────────────────────────────────────────

class DeviceBase(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=100)
    hostname: Optional[str] = None
    os_type: Optional[str] = None
    device_fingerprint: Optional[str] = None


class DeviceCreateRequest(DeviceBase):
    user_id: int


class DeviceUpdateRequest(BaseModel):
    device_name: Optional[str] = None
    status: Optional[str] = None


class DeviceResponse(BaseModel):
    id: int
    user_id: int
    device_name: str
    hostname: Optional[str] = None
    os_type: Optional[str] = None
    device_fingerprint: Optional[str] = None
    status: str
    last_seen_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    config_revision: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Device Registration (Client API) ─────────────────────────

class DeviceRegisterRequest(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=100)
    hostname: Optional[str] = None
    os_type: Optional[str] = None
    device_fingerprint: Optional[str] = None


class DeviceRegisterResponse(DeviceResponse):
    pass
