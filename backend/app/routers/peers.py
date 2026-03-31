from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_password_changed
from app.models.user import User
from app.schemas.peer import (
    BranchOfficeCreate,
    PeerOverrideCreate,
    PeerPermissionSummary,
    PeerResponse,
    PeerUpdate,
    RoadWarriorCreate,
)
from app.schemas.group import AddMembersRequest
from app.services import peer_service
from app.services.audit_service import log as audit_log
from app.services.config_service import generate_client_config, generate_mikrotik_config
from app.services.policy_compiler import compile_allowed_cidrs, compile_client_allowed_ips, compile_override_summary
from app.utils.qr import generate_qr_png

router = APIRouter(prefix="/api/peers", tags=["peers"])


def _get_server_config(db):
    from app.models.server_config import ServerConfig
    cfg = db.query(ServerConfig).first()
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server config not initialised yet",
        )
    return cfg


@router.get("", response_model=list[PeerResponse])
def list_peers(
    peer_type: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    peers = peer_service.list_peers(db, peer_type=peer_type)
    return [PeerResponse.from_orm_peer(p) for p in peers]


@router.get("/{peer_id}", response_model=PeerResponse)
def get_peer(
    peer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")
    return PeerResponse.from_orm_peer(peer)


@router.post("/roadwarrior", response_model=PeerResponse, status_code=status.HTTP_201_CREATED)
def create_roadwarrior(
    body: RoadWarriorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_password_changed),
):
    try:
        peer = peer_service.create_roadwarrior(db, body, created_by=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    audit_log(db, "peer.create", user_id=current_user.id, target_type="peer", target_id=peer.id, details={"name": peer.name, "type": "roadwarrior"})
    return PeerResponse.from_orm_peer(peer)


@router.post("/branch-office", response_model=PeerResponse, status_code=status.HTTP_201_CREATED)
def create_branch_office(
    body: BranchOfficeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_password_changed),
):
    try:
        peer = peer_service.create_branch_office(db, body, created_by=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    audit_log(db, "peer.create", user_id=current_user.id, target_type="peer", target_id=peer.id, details={"name": peer.name, "type": "branch_office"})
    return PeerResponse.from_orm_peer(peer)


@router.patch("/{peer_id}", response_model=PeerResponse)
def update_peer(
    peer_id: int,
    body: PeerUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")
    peer = peer_service.update_peer(db, peer, body)
    return PeerResponse.from_orm_peer(peer)


@router.post("/{peer_id}/groups", response_model=PeerResponse)
def update_peer_groups(
    peer_id: int,
    body: AddMembersRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Replace all group memberships for a peer with the given list."""
    from app.models.group import PeerGroupMember
    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")

    # Remove existing memberships
    db.query(PeerGroupMember).filter(PeerGroupMember.peer_id == peer_id).delete()

    # Add new ones
    for gid in body.peer_ids:
        db.add(PeerGroupMember(peer_id=peer_id, group_id=gid))

    db.commit()
    db.refresh(peer)
    return PeerResponse.from_orm_peer(peer)


@router.delete("/{peer_id}")
def revoke_peer(
    peer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_password_changed),
):
    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")
    peer_service.revoke_peer(db, peer)
    audit_log(db, "peer.revoke", user_id=current_user.id, target_type="peer", target_id=peer_id, details={"name": peer.name})
    return {"message": f"Peer '{peer.name}' deleted successfully"}


@router.post("/{peer_id}/toggle", response_model=PeerResponse)
def toggle_peer(
    peer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")
    peer = peer_service.toggle_peer(db, peer)
    return PeerResponse.from_orm_peer(peer)


@router.post("/{peer_id}/regenerate-keys", response_model=PeerResponse)
def regenerate_keys(
    peer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")
    peer = peer_service.regenerate_keys(db, peer)
    return PeerResponse.from_orm_peer(peer)


@router.get("/{peer_id}/config")
def download_config(
    peer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")
    server_cfg = _get_server_config(db)
    allowed_cidrs = compile_client_allowed_ips(db, peer_id)
    config_str = generate_client_config(peer, server_cfg, allowed_cidrs)
    filename = f"{peer.name.lower().replace(' ', '-')}.conf"
    return Response(
        content=config_str,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{peer_id}/config/mikrotik")
def download_mikrotik_config(
    peer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Download MikroTik RouterOS compatible WireGuard config."""
    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")
    server_cfg = _get_server_config(db)
    allowed_cidrs = compile_client_allowed_ips(db, peer_id)
    config_str = generate_mikrotik_config(peer, server_cfg, allowed_cidrs)
    filename = f"{peer.name.lower().replace(' ', '-')}-mikrotik.conf"
    return Response(
        content=config_str,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{peer_id}/qrcode")
def get_qrcode(
    peer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")
    server_cfg = _get_server_config(db)
    allowed_cidrs = compile_client_allowed_ips(db, peer_id)
    config_str = generate_client_config(peer, server_cfg, allowed_cidrs)
    png_bytes = generate_qr_png(config_str)
    return Response(content=png_bytes, media_type="image/png")


@router.get("/{peer_id}/permissions", response_model=PeerPermissionSummary)
def get_permissions(
    peer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")
    return compile_override_summary(db, peer_id)


@router.post("/{peer_id}/overrides")
def upsert_override(
    peer_id: int,
    body: PeerOverrideCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")
    return peer_service.upsert_override(db, peer, body)


@router.delete("/{peer_id}/overrides/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_override(
    peer_id: int,
    zone_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    deleted = peer_service.delete_override(db, peer_id, zone_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Override not found")
