import json
import logging

from sqlalchemy.orm import Session

from app.models.peer import Peer, PeerOverride
from app.models.group import PeerGroup, PeerGroupMember, Policy
from app.models.network import Network
from app.schemas.peer import BranchOfficeCreate, PeerOverrideCreate, PeerUpdate, RoadWarriorCreate
from app.services import wg_service
from app.services.policy_compiler import compile_allowed_cidrs
from app.utils.ip_utils import get_next_available_ip
from app.utils.wg_keygen import safe_generate_keypair
from app.config import settings

logger = logging.getLogger(__name__)


def _get_used_ips(db: Session, exclude_peer_id: int | None = None) -> list[str]:
    query = db.query(Peer.assigned_ip)
    if exclude_peer_id:
        query = query.filter(Peer.id != exclude_peer_id)
    return [row[0] for row in query.all()]


def _assign_groups(db: Session, peer_id: int, group_ids: list[int]) -> None:
    for group_id in group_ids:
        db.add(PeerGroupMember(peer_id=peer_id, group_id=group_id))


def _ensure_all_group(db: Session) -> int:
    """Ensure the 'All' group exists and return its ID."""
    group = db.query(PeerGroup).filter(PeerGroup.name == "All").first()
    if group:
        return group.id
    group = PeerGroup(name="All", description="All peers — default access")
    db.add(group)
    db.flush()
    return group.id


def _ensure_all_to_all_policy(db: Session, group_id: int) -> None:
    """Ensure an allow-both policy exists from the group to itself."""
    existing = db.query(Policy).filter(
        Policy.source_group_id == group_id,
        Policy.dest_group_id == group_id,
        Policy.direction == "both",
    ).first()
    if not existing:
        db.add(Policy(
            source_group_id=group_id,
            dest_group_id=group_id,
            direction="both",
            action="allow",
        ))


def _create_branch_group_and_policies(db: Session, peer: Peer) -> int:
    """
    When a branch office is created, auto-create a group named '{name}-lan'
    and set up all-to-all policies with the 'All' group.
    Returns the new group ID.
    """
    group_name = f"{peer.name}-lan"
    
    existing = db.query(PeerGroup).filter(PeerGroup.name == group_name).first()
    if existing:
        db.add(PeerGroupMember(peer_id=peer.id, group_id=existing.id))
        return existing.id
    
    group = PeerGroup(name=group_name, description=f"Auto-created for branch office '{peer.name}'")
    db.add(group)
    db.flush()
    
    db.add(PeerGroupMember(peer_id=peer.id, group_id=group.id))
    
    all_group_id = _ensure_all_group(db)
    
    _ensure_all_to_all_policy(db, all_group_id)
    
    db.add(Policy(
        source_group_id=all_group_id,
        dest_group_id=group.id,
        direction="both",
        action="allow",
    ))
    db.add(Policy(
        source_group_id=group.id,
        dest_group_id=all_group_id,
        direction="both",
        action="allow",
    ))
    db.add(Policy(
        source_group_id=group.id,
        dest_group_id=group.id,
        direction="both",
        action="allow",
    ))
    
    return group.id


def _bump_config_changed(db: Session) -> None:
    """Update last_config_changed_at to signal all peers are out of sync."""
    from datetime import datetime, timezone
    from app.models.server_config import ServerConfig
    cfg = db.query(ServerConfig).first()
    if cfg:
        cfg.last_config_changed_at = datetime.now(timezone.utc)


def _create_peer_networks(db: Session, peer: Peer, remote_subnets: list[str] | None = None) -> None:
    """
    For branch_office peers: create Network records for each remote subnet,
    linked to the peer as the gateway (peer_id).
    Roadwarriors do not own networks, so this is a no-op for them.
    """
    if peer.peer_type != "branch_office" or not remote_subnets:
        return

    for subnet in remote_subnets:
        existing = db.query(Network).filter(Network.subnet == subnet).first()
        if existing:
            if existing.peer_id is None:
                existing.peer_id = peer.id
            continue
        network = Network(
            name=f"{peer.name} — {subnet}",
            subnet=subnet,
            description=f"Auto-created for branch office '{peer.name}'",
            network_type="lan",
            is_default=False,
            peer_id=peer.id,
        )
        db.add(network)


def create_roadwarrior(db: Session, data: RoadWarriorCreate, created_by: int) -> Peer:
    network_id = data.network_id or None
    if network_id:
        network = db.query(Network).filter(Network.id == network_id).first()
        if not network:
            raise ValueError(f"Network {network_id} not found")

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
        network_id=network_id,
        tunnel_mode=data.tunnel_mode,
        dns=data.dns,
        persistent_keepalive=data.persistent_keepalive,
        is_enabled=True,
        created_by=created_by,
    )
    db.add(peer)
    db.flush()

    group_ids = list(data.group_ids) if data.group_ids else []
    if not group_ids:
        all_group_id = _ensure_all_group(db)
        group_ids.append(all_group_id)
        _ensure_all_to_all_policy(db, all_group_id)

    _assign_groups(db, peer.id, group_ids)
    _create_peer_networks(db, peer)
    
    db.commit()
    db.refresh(peer)

    try:
        wg_service.apply_config(db)
    except Exception:
        pass

    return peer


def create_branch_office(db: Session, data: BranchOfficeCreate, created_by: int) -> Peer:
    network_id = data.network_id or None
    if network_id:
        network = db.query(Network).filter(Network.id == network_id).first()
        if not network:
            raise ValueError(f"Network {network_id} not found")

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
        network_id=network_id,
        tunnel_mode="split",
        remote_subnets=json.dumps(data.remote_subnets),
        dns=data.dns,
        persistent_keepalive=data.persistent_keepalive,
        is_enabled=True,
        created_by=created_by,
    )
    db.add(peer)
    db.flush()

    _create_peer_networks(db, peer, data.remote_subnets)
    
    group_ids = list(data.group_ids) if data.group_ids else []
    if not group_ids:
        _create_branch_group_and_policies(db, peer)
    else:
        _assign_groups(db, peer.id, group_ids)
    
    db.commit()
    db.refresh(peer)

    _bump_config_changed(db)
    db.commit()

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
    update_data = data.model_dump(exclude_none=True)
    
    if "remote_subnets" in update_data:
        new_subnets = update_data.pop("remote_subnets")
        old_subnets = json.loads(peer.remote_subnets) if peer.remote_subnets else []
        
        peer.remote_subnets = json.dumps(new_subnets)
        
        added = set(new_subnets) - set(old_subnets)
        removed = set(old_subnets) - set(new_subnets)
        
        for subnet in removed:
            network = db.query(Network).filter(
                Network.subnet == subnet,
                Network.peer_id == peer.id,
            ).first()
            if network:
                db.delete(network)
        
        for subnet in added:
            existing = db.query(Network).filter(Network.subnet == subnet).first()
            if existing:
                if existing.peer_id is None:
                    existing.peer_id = peer.id
            else:
                db.add(Network(
                    name=f"{peer.name} — {subnet}",
                    subnet=subnet,
                    description=f"Auto-created for branch office '{peer.name}'",
                    network_type="lan",
                    is_default=False,
                    peer_id=peer.id,
                ))
    
    for key, value in update_data.items():
        setattr(peer, key, value)
    
    db.commit()
    db.refresh(peer)
    _bump_config_changed(db)
    db.commit()
    try:
        wg_service.apply_config(db)
    except Exception:
        pass
    return peer


def revoke_peer(db: Session, peer: Peer) -> None:
    if peer.is_system:
        raise ValueError("Cannot delete system peer (VPN server)")
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
        PeerOverride.network_id == data.network_id,
    ).first()
    if existing:
        existing.action = data.action
        existing.reason = data.reason
        db.commit()
        db.refresh(existing)
        return existing

    override = PeerOverride(
        peer_id=peer.id,
        network_id=data.network_id,
        action=data.action,
        reason=data.reason,
    )
    db.add(override)
    db.commit()
    db.refresh(override)
    return override


def delete_override(db: Session, peer_id: int, network_id: int) -> bool:
    override = db.query(PeerOverride).filter(
        PeerOverride.peer_id == peer_id,
        PeerOverride.network_id == network_id,
    ).first()
    if not override:
        return False
    db.delete(override)
    db.commit()
    return True
