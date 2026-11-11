"""Per-peer configuration revisions; downloading is distinct from applying."""
import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.config_revision import ConfigRevision
from app.models.peer import Peer
from app.models.server_config import ServerConfig
from app.services.config_service import generate_client_config
from app.services.policy_compiler import compile_client_allowed_ips


def clear_default_user_peer_groups(db: Session, user_id: int) -> None:
    """Explicit user group management replaces the historical automatic All grant."""
    from app.models.group import PeerGroup, PeerGroupMember
    default = db.query(PeerGroup).filter(PeerGroup.name == "All").first()
    if default:
        peers = db.query(Peer.id).filter(Peer.user_id == user_id, Peer.peer_type == "roadwarrior")
        db.query(PeerGroupMember).filter(PeerGroupMember.peer_id.in_(peers),
                                        PeerGroupMember.group_id == default.id).delete(synchronize_session=False)


def refresh_revisions(db: Session) -> list[int]:
    from app.services.route_service import route_lock
    with route_lock:
        return _refresh_revisions(db)


def _refresh_revisions(db: Session) -> list[int]:
    cfg = db.query(ServerConfig).first()
    if not cfg:
        return []
    revision = db.query(func.max(ConfigRevision.revision_number)).scalar() or 0
    changed = []
    for peer in db.query(Peer).filter(Peer.peer_type != "server").all():
        routes = compile_client_allowed_ips(db, peer.id)
        config = generate_client_config(peer, cfg, routes)
        digest = hashlib.sha256((config + str(peer.is_enabled)).encode()).hexdigest()
        if digest == peer.desired_config_hash:
            continue
        revision += 1
        peer.desired_config_hash = digest
        peer.config_revision = revision
        db.add(ConfigRevision(peer_id=peer.id, revision_number=revision, change_type="config_updated",
                              changes=json.dumps({"allowed_ips": routes, "enabled": peer.is_enabled,
                                                  "refresh_required": True})))
        changed.append(peer.id)
    if changed:
        cfg.last_config_changed_at = datetime.now(timezone.utc)
    db.commit()
    return changed


def sync_state(peer: Peer) -> tuple[str, str]:
    if peer.applied_config_revision is not None and peer.applied_config_revision == peer.config_revision:
        return "green", "El cliente confirmó la revisión actual"
    if not peer.last_config_downloaded_at:
        return "red", "Configuración pendiente de descarga y aplicación"
    return "yellow", "Pendiente de aplicación o de confirmación del cliente"


def apply_permission_changes(db: Session) -> None:
    from app.services import iptables_service
    from app.services.route_service import route_lock
    with route_lock:
        from app.services.wg_service import ApplyError
        try:
            refresh_revisions(db)
            iptables_service.apply_iptables_rules(db)
        except Exception as exc:
            raise ApplyError(f"Permisos guardados; aplicación pendiente: {exc}") from exc
