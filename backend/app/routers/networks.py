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
    NetworkPeersUpdate,
)
from app.services import network_service
from app.services.peer_service import _bump_config_changed

router = APIRouter(prefix="/api/networks", tags=["networks"])


def _apply_network_changes(db):
    """Bump config changed and apply WireGuard config after network changes."""
    _bump_config_changed(db)
    db.commit()
    try:
        from app.services import wg_service
        wg_service.apply_config(db)
    except Exception:
        pass


@router.post("/apply", status_code=status.HTTP_200_OK)
def apply_changes(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Apply pending network changes to WireGuard config."""
    _apply_network_changes(db)
    return {"status": "applied"}


@router.get("", response_model=list[NetworkResponse])
def list_networks(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    return network_service.list_networks_with_peers(db)


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
    result = network_service.create_network(db, body)
    _apply_network_changes(db)
    return result


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
    result = network_service.update_network(db, network, body)
    _apply_network_changes(db)
    return result


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
    _apply_network_changes(db)


@router.post("/{network_id}/peers", response_model=NetworkResponse)
def assign_peers(
    network_id: int,
    body: NetworkPeersUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Assign peers to a network. Replaces existing assignments."""
    network = network_service.get_network(db, network_id)
    if not network:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network not found")
    result = network_service.assign_peers_to_network(db, network, body.peer_ids)
    _apply_network_changes(db)
    return result


@router.post("/{network_id}/peers/{peer_id}", response_model=NetworkResponse)
def add_peer(
    network_id: int,
    peer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Add a single peer to a network."""
    network = network_service.get_network(db, network_id)
    if not network:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network not found")
    result = network_service.add_peer_to_network(db, network, peer_id)
    _apply_network_changes(db)
    return result


@router.delete("/{network_id}/peers/{peer_id}", response_model=NetworkResponse)
def remove_peer(
    network_id: int,
    peer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Remove a peer from a network."""
    network = network_service.get_network(db, network_id)
    if not network:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network not found")
    result = network_service.remove_peer_from_network(db, network, peer_id)
    _apply_network_changes(db)
    return result


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
