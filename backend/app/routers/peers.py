from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
import hashlib

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
from app.services.config_service import generate_client_config, generate_mikrotik_config, generate_mikrotik_manual_commands
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
    from app.models.server_config import ServerConfig
    from app.services.wg_service import get_peer_statuses

    peers = peer_service.list_peers(db, peer_type=peer_type)
    wg_statuses = get_peer_statuses()
    server_cfg = db.query(ServerConfig).first()
    config_changed_at = server_cfg.last_config_changed_at if server_cfg else None

    result = []
    for p in peers:
        wg = wg_statuses.get(p.public_key)
        if p.last_config_hash is None:
            sync = "red"
        elif config_changed_at and p.last_config_downloaded_at and config_changed_at > p.last_config_downloaded_at:
            sync = "yellow"
        else:
            sync = "green"
        result.append(PeerResponse.from_orm_peer(p, db=db, wg_status=wg, sync_status=sync))
    return result


@router.get("/{peer_id}", response_model=PeerResponse)
def get_peer(
    peer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    from app.models.server_config import ServerConfig
    from app.services.wg_service import get_peer_statuses

    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")

    wg_statuses = get_peer_statuses()
    wg = wg_statuses.get(peer.public_key)
    server_cfg = db.query(ServerConfig).first()
    config_changed_at = server_cfg.last_config_changed_at if server_cfg else None

    if peer.last_config_hash is None:
        sync = "red"
    elif config_changed_at and peer.last_config_downloaded_at and config_changed_at > peer.last_config_downloaded_at:
        sync = "yellow"
    else:
        sync = "green"

    return PeerResponse.from_orm_peer(peer, db=db, wg_status=wg, sync_status=sync)


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
    return PeerResponse.from_orm_peer(peer, db=db)


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
    return PeerResponse.from_orm_peer(peer, db=db)


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
    return PeerResponse.from_orm_peer(peer, db=db)


@router.post("/{peer_id}/groups", response_model=PeerResponse)
def update_peer_groups(
    peer_id: int,
    body: AddMembersRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Replace all group memberships for a peer with the given list."""
    from app.models.group import PeerGroupMember
    from app.services.peer_service import _bump_config_changed
    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")

    db.query(PeerGroupMember).filter(PeerGroupMember.peer_id == peer_id).delete()

    for gid in body.peer_ids:
        db.add(PeerGroupMember(peer_id=peer_id, group_id=gid))

    _bump_config_changed(db)
    db.commit()
    db.refresh(peer)
    try:
        from app.services import wg_service
        wg_service.apply_config(db)
    except Exception:
        pass
    return PeerResponse.from_orm_peer(peer, db=db)


def _protect_system_peer(peer):
    if getattr(peer, 'is_system', False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify the system peer")


@router.delete("/{peer_id}")
def revoke_peer(
    peer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_password_changed),
):
    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")
    _protect_system_peer(peer)
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
    _protect_system_peer(peer)
    peer = peer_service.toggle_peer(db, peer)
    return PeerResponse.from_orm_peer(peer, db=db)


@router.post("/{peer_id}/regenerate-keys", response_model=PeerResponse)
def regenerate_keys(
    peer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")
    _protect_system_peer(peer)
    peer = peer_service.regenerate_keys(db, peer)
    return PeerResponse.from_orm_peer(peer, db=db)


@router.get("/{peer_id}/config")
def download_config(
    peer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")
    _protect_system_peer(peer)
    server_cfg = _get_server_config(db)
    allowed_cidrs = compile_client_allowed_ips(db, peer_id)
    config_str = generate_client_config(peer, server_cfg, allowed_cidrs)
    
    from datetime import datetime, timezone
    peer.last_config_hash = hashlib.sha256(config_str.encode()).hexdigest()
    peer.last_config_downloaded_at = datetime.now(timezone.utc)
    db.commit()
    
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
    """Download MikroTik RouterOS CLI commands for WinBox terminal."""
    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")
    _protect_system_peer(peer)
    server_cfg = _get_server_config(db)
    allowed_cidrs = compile_client_allowed_ips(db, peer_id)
    
    config_str = generate_mikrotik_manual_commands(peer, server_cfg, allowed_cidrs)
    
    filename = f"{peer.name.lower().replace(' ', '-')}-mikrotik.txt"
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
    _protect_system_peer(peer)
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


@router.delete("/{peer_id}/overrides/{network_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_override(
    peer_id: int,
    network_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    deleted = peer_service.delete_override(db, peer_id, network_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Override not found")


@router.get("/{peer_id}/sync-status")
def get_sync_status(
    peer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """
    Return sync status for a peer.
    - green: config matches (no server changes since last download)
    - yellow: config is outdated (server changed since last download)
    - red: peer has never downloaded a config
    """
    from app.models.server_config import ServerConfig
    from app.services.wg_service import get_peer_statuses

    peer = peer_service.get_peer(db, peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")

    server_cfg = db.query(ServerConfig).first()
    config_changed_at = server_cfg.last_config_changed_at if server_cfg else None

    if peer.last_config_hash is None:
        sync_status = "red"
        message = "Config never downloaded"
    elif config_changed_at and peer.last_config_downloaded_at and config_changed_at > peer.last_config_downloaded_at:
        sync_status = "yellow"
        message = "Config outdated — server routes changed"
    else:
        sync_status = "green"
        message = "Config is up to date"

    wg_statuses = get_peer_statuses()
    wg = wg_statuses.get(peer.public_key)
    is_online = wg.is_online if wg else False

    return {
        "peer_id": peer.id,
        "peer_name": peer.name,
        "sync_status": sync_status,
        "sync_message": message,
        "is_online": is_online,
        "last_config_downloaded_at": peer.last_config_downloaded_at.isoformat() if peer.last_config_downloaded_at else None,
        "last_config_changed_at": config_changed_at.isoformat() if config_changed_at else None,
    }
