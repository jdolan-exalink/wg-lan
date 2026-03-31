import json

from sqlalchemy.orm import Session

from app.models.peer import Peer, PeerOverride
from app.models.group import PeerGroupMember
from app.models.network import Network
from app.schemas.peer import BranchOfficeCreate, PeerOverrideCreate, PeerUpdate, RoadWarriorCreate
from app.services import wg_service
from app.services.policy_compiler import compile_allowed_cidrs
from app.utils.ip_utils import get_next_available_ip
from app.utils.wg_keygen import safe_generate_keypair
from app.config import settings


def _get_used_ips(db: Session, exclude_peer_id: int | None = None) -> list[str]:
    query = db.query(Peer.assigned_ip)
    if exclude_peer_id:
        query = query.filter(Peer.id != exclude_peer_id)
    return [row[0] for row in query.all()]


def _assign_groups(db: Session, peer_id: int, group_ids: list[int]) -> None:
    for group_id in group_ids:
        db.add(PeerGroupMember(peer_id=peer_id, group_id=group_id))


def create_roadwarrior(db: Session, data: RoadWarriorCreate, created_by: int) -> Peer:
    # Validate network_id if provided (optional - only for LAN association)
    if data.network_id:
        network = db.query(Network).filter(Network.id == data.network_id).first()
        if not network:
            raise ValueError(f"Network {data.network_id} not found")

    # Assign VPN IP from global settings subnet
    used_ips = _get_used_ips(db)
    assigned_ip = get_next_available_ip(settings.subnet, used_ips)
    private_key, public_key = safe_generate_keypair()

    peer = Peer(
        name=data.name,
        peer_type="roadwarrior",
        device_type=data.device_type,
        private_key=private_key,
        public_key=public_key,
        assigned_ip=assigned_ip,
        network_id=data.network_id,
        tunnel_mode=data.tunnel_mode,
        dns=data.dns,
        persistent_keepalive=data.persistent_keepalive,
        is_enabled=True,
        created_by=created_by,
    )
    db.add(peer)
    db.flush()  # Get peer.id

    _assign_groups(db, peer.id, data.group_ids)
    db.commit()
    db.refresh(peer)

    # Apply WireGuard config (best-effort — doesn't fail the request)
    try:
        wg_service.apply_config(db)
    except Exception:
        pass

    return peer


def create_branch_office(db: Session, data: BranchOfficeCreate, created_by: int) -> Peer:
    # Validate network_id if provided (optional - only for LAN association)
    if data.network_id:
        network = db.query(Network).filter(Network.id == data.network_id).first()
        if not network:
            raise ValueError(f"Network {data.network_id} not found")

    # Assign VPN IP from global settings subnet
    used_ips = _get_used_ips(db)
    assigned_ip = get_next_available_ip(settings.subnet, used_ips)
    private_key, public_key = safe_generate_keypair()

    peer = Peer(
        name=data.name,
        peer_type="branch_office",
        device_type=data.device_type,
        private_key=private_key,
        public_key=public_key,
        assigned_ip=assigned_ip,
        network_id=data.network_id,
        tunnel_mode="split",  # Branch offices always split-tunnel
        remote_subnets=json.dumps(data.remote_subnets),
        dns=data.dns,
        persistent_keepalive=data.persistent_keepalive,
        is_enabled=True,
        created_by=created_by,
    )
    db.add(peer)
    db.flush()

    _assign_groups(db, peer.id, data.group_ids)
    db.commit()
    db.refresh(peer)

    try:
        wg_service.apply_config(db)
    except Exception:
        pass

    return peer


def list_peers(db: Session, peer_type: str | None = None) -> list[Peer]:
    query = db.query(Peer)
    if peer_type:
        query = query.filter(Peer.peer_type == peer_type)
    return query.order_by(Peer.name).all()


def get_peer(db: Session, peer_id: int) -> Peer | None:
    return db.query(Peer).filter(Peer.id == peer_id).first()


def update_peer(db: Session, peer: Peer, data: PeerUpdate) -> Peer:
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(peer, key, value)
    db.commit()
    db.refresh(peer)
    try:
        wg_service.apply_config(db)
    except Exception:
        pass
    return peer


def revoke_peer(db: Session, peer: Peer) -> None:
    db.delete(peer)
    db.commit()
    try:
        wg_service.apply_config(db)
    except Exception:
        pass


def toggle_peer(db: Session, peer: Peer) -> Peer:
    peer.is_enabled = not peer.is_enabled
    if peer.is_enabled:
        peer.revoked_at = None
    db.commit()
    db.refresh(peer)
    try:
        wg_service.apply_config(db)
    except Exception:
        pass
    return peer


def regenerate_keys(db: Session, peer: Peer) -> Peer:
    private_key, public_key = safe_generate_keypair()
    peer.private_key = private_key
    peer.public_key = public_key
    db.commit()
    db.refresh(peer)
    try:
        wg_service.apply_config(db)
    except Exception:
        pass
    return peer


def upsert_override(db: Session, peer: Peer, data: PeerOverrideCreate) -> PeerOverride:
    existing = db.query(PeerOverride).filter(
        PeerOverride.peer_id == peer.id,
        PeerOverride.zone_id == data.zone_id,
    ).first()
    if existing:
        existing.action = data.action
        existing.reason = data.reason
        db.commit()
        db.refresh(existing)
        return existing

    override = PeerOverride(
        peer_id=peer.id,
        zone_id=data.zone_id,
        action=data.action,
        reason=data.reason,
    )
    db.add(override)
    db.commit()
    db.refresh(override)
    return override


def delete_override(db: Session, peer_id: int, zone_id: int) -> bool:
    override = db.query(PeerOverride).filter(
        PeerOverride.peer_id == peer_id,
        PeerOverride.zone_id == zone_id,
    ).first()
    if not override:
        return False
    db.delete(override)
    db.commit()
    return True
