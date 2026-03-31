from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_password_changed
from app.models.user import User
from app.schemas.zone import ZoneCreate, ZoneNetworkCreate, ZoneResponse, ZoneUpdate, ZoneNetworkResponse
from app.services import zone_service

router = APIRouter(prefix="/api/zones", tags=["zones"])


@router.get("", response_model=list[ZoneResponse])
def list_zones(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    return zone_service.list_zones(db)


@router.get("/{zone_id}", response_model=ZoneResponse)
def get_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    zone = zone_service.get_zone(db, zone_id)
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    return zone


@router.post("", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
def create_zone(
    body: ZoneCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    return zone_service.create_zone(db, body)


@router.patch("/{zone_id}", response_model=ZoneResponse)
def update_zone(
    zone_id: int,
    body: ZoneUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    zone = zone_service.get_zone(db, zone_id)
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    return zone_service.update_zone(db, zone, body)


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    zone = zone_service.get_zone(db, zone_id)
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    zone_service.delete_zone(db, zone)


@router.post("/{zone_id}/networks", response_model=ZoneNetworkResponse, status_code=status.HTTP_201_CREATED)
def add_zone_network(
    zone_id: int,
    body: ZoneNetworkCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    zone = zone_service.get_zone(db, zone_id)
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    return zone_service.add_zone_network(db, zone, body)


@router.delete("/{zone_id}/networks/{zn_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone_network(
    zone_id: int,
    zn_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    zone_service.delete_zone_network(db, zn_id)
