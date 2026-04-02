from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.models.device import Device
from app.schemas.device import (
    DeviceCreateRequest,
    DeviceUpdateRequest,
    DeviceResponse,
)
from app.services.audit_service import log as audit_log

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])


@router.get("", response_model=list[DeviceResponse])
def list_devices(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """List all registered devices."""
    query = db.query(Device)
    
    if user_id is not None:
        query = query.filter(Device.user_id == user_id)
    
    if status:
        query = query.filter(Device.status == status)
    
    devices = query.order_by(Device.id).offset(skip).limit(limit).all()
    return devices


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Get device details."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


@router.patch("/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: int,
    body: DeviceUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update device details."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)
    
    db.commit()
    db.refresh(device)
    
    audit_log(
        db,
        "device.update",
        user_id=current_user.id,
        target_type="device",
        target_id=device_id,
        details={"fields_updated": list(update_data.keys())},
        ip_address=request.client.host if request.client else None,
    )
    return device
