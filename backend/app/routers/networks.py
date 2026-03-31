from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_password_changed
from app.models.user import User
from app.schemas.network import (
    NetworkCreate,
    NetworkResponse,
    NetworkUpdate,
    SubnetConflictCheck,
    SubnetConflictResponse,
)
from app.services import network_service

router = APIRouter(prefix="/api/networks", tags=["networks"])


@router.get("", response_model=list[NetworkResponse])
def list_networks(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    return network_service.list_networks(db)


@router.get("/{network_id}", response_model=NetworkResponse)
def get_network(
    network_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    network = network_service.get_network(db, network_id)
    if not network:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network not found")
    return network


@router.post("", response_model=NetworkResponse, status_code=status.HTTP_201_CREATED)
def create_network(
    body: NetworkCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    has_conflict, conflicting = network_service.check_conflict(db, body.subnet)
    if has_conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Subnet overlaps with existing network '{conflicting}'",
        )
    return network_service.create_network(db, body)


@router.patch("/{network_id}", response_model=NetworkResponse)
def update_network(
    network_id: int,
    body: NetworkUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    network = network_service.get_network(db, network_id)
    if not network:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network not found")
    return network_service.update_network(db, network, body)


@router.delete("/{network_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_network(
    network_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    network = network_service.get_network(db, network_id)
    if not network:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network not found")
    network_service.delete_network(db, network)


@router.post("/check-conflict", response_model=SubnetConflictResponse)
def check_conflict(
    body: SubnetConflictCheck,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    has_conflict, conflicting = network_service.check_conflict(db, body.subnet, body.exclude_id)
    return SubnetConflictResponse(
        has_conflict=has_conflict,
        conflicting_network=conflicting,
    )
