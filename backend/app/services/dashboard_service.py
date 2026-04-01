from sqlalchemy.orm import Session

from app.models.peer import Peer
from app.schemas.dashboard import DashboardStats, PeerStatusItem, TrafficItem
from app.services.wg_service import get_peer_statuses


def get_stats(db: Session) -> DashboardStats:
    peers = db.query(Peer).filter(Peer.peer_type != "server").all()
    statuses = get_peer_statuses()

    online = 0
    total_rx = 0
    total_tx = 0

    for peer in peers:
        if not peer.is_enabled:
            continue
        st = statuses.get(peer.public_key)
        if st and st.is_online:
            online += 1
        if st:
            total_rx += st.rx_bytes
            total_tx += st.tx_bytes

    enabled = [p for p in peers if p.is_enabled]
    return DashboardStats(
        total_peers=len(enabled),
        online_peers=online,
        offline_peers=len(enabled) - online,
        total_rx_bytes=total_rx,
        total_tx_bytes=total_tx,
        roadwarrior_count=sum(1 for p in enabled if p.peer_type == "roadwarrior"),
        branch_office_count=sum(1 for p in enabled if p.peer_type == "branch_office"),
    )


def get_peers_status(db: Session) -> list[PeerStatusItem]:
    peers = db.query(Peer).filter(Peer.peer_type != "server").order_by(Peer.name).all()
    statuses = get_peer_statuses()

    result = []
    for peer in peers:
        st = statuses.get(peer.public_key)
        result.append(PeerStatusItem(
            id=peer.id,
            name=peer.name,
            peer_type=peer.peer_type,
            assigned_ip=peer.assigned_ip,
            is_enabled=peer.is_enabled,
            is_online=bool(st and st.is_online and peer.is_enabled),
            endpoint=st.endpoint if st else None,
            last_handshake=st.last_handshake if st else 0,
            rx_bytes=st.rx_bytes if st else 0,
            tx_bytes=st.tx_bytes if st else 0,
        ))

    return result


def get_traffic(db: Session) -> list[TrafficItem]:
    peers = db.query(Peer).filter(Peer.is_enabled == True, Peer.peer_type != "server").all()
    statuses = get_peer_statuses()

    result = []
    for peer in peers:
        st = statuses.get(peer.public_key)
        result.append(TrafficItem(
            peer_id=peer.id,
            peer_name=peer.name,
            rx_bytes=st.rx_bytes if st else 0,
            tx_bytes=st.tx_bytes if st else 0,
        ))

    return sorted(result, key=lambda x: x.rx_bytes + x.tx_bytes, reverse=True)
