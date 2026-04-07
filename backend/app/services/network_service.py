from sqlalchemy.orm import Session

from app.models.network import Network
from app.models.peer import Peer, PeerNetworkAccess
from app.schemas.network import NetworkCreate, NetworkUpdate
from app.utils.ip_utils import subnets_overlap


def list_networks(db: Session) -> list[Network]:
    return db.query(Network).order_by(Network.name).all()


def get_network(db: Session, network_id: int) -> Network | None:
    return db.query(Network).filter(Network.id == network_id).first()


def get_network_with_peers(db: Session, network_id: int) -> dict:
    network = get_network(db, network_id)
    if not network:
        return {}

    access_rows = db.query(PeerNetworkAccess).filter(
        PeerNetworkAccess.network_id == network_id
    ).all()
    peer_ids = [a.peer_id for a in access_rows]
    peers = db.query(Peer).filter(Peer.id.in_(peer_ids)).all() if peer_ids else []
    peer_info = [
        {
            "id": p.id,
            "name": p.name,
            "peer_type": p.peer_type,
            "assigned_ip": p.assigned_ip,
            "device_type": p.device_type,
        }
        for p in peers
    ]

    return {
        "id": network.id,
        "name": network.name,
        "subnet": network.subnet,
        "description": network.description,
        "network_type": network.network_type,
        "is_default": network.is_default,
        "nat_enabled": network.nat_enabled,
        "peer_id": network.peer_id,
        "peer_count": len(peers),
        "peers": peer_info,
    }


def list_networks_with_peers(db: Session) -> list[dict]:
    networks = list_networks(db)
    result = []
    for network in networks:
        access_rows = db.query(PeerNetworkAccess).filter(
            PeerNetworkAccess.network_id == network.id
        ).all()
        peer_ids = [a.peer_id for a in access_rows]
        peers = db.query(Peer).filter(Peer.id.in_(peer_ids)).all() if peer_ids else []
        peer_info = [
            {
                "id": p.id,
                "name": p.name,
                "peer_type": p.peer_type,
                "assigned_ip": p.assigned_ip,
                "device_type": p.device_type,
            }
            for p in peers
        ]
        result.append({
            "id": network.id,
            "name": network.name,
            "subnet": network.subnet,
            "description": network.description,
            "network_type": network.network_type,
            "is_default": network.is_default,
            "nat_enabled": network.nat_enabled,
            "peer_id": network.peer_id,
            "peer_count": len(peers),
            "peers": peer_info,
        })
    return result


def create_network(db: Session, data: NetworkCreate) -> Network:
    if data.is_default:
        db.query(Network).filter(Network.is_default == True).update({"is_default": False})

    network = Network(**data.model_dump())
    db.add(network)
    db.commit()
    db.refresh(network)
    return network


def update_network(db: Session, network: Network, data: NetworkUpdate) -> Network:
    updates = data.model_dump(exclude_none=True)
    if updates.get("is_default"):
        db.query(Network).filter(Network.id != network.id, Network.is_default == True).update(
            {"is_default": False}
        )
    for key, value in updates.items():
        setattr(network, key, value)
    db.commit()
    db.refresh(network)
    return network


def add_peer_to_network(db: Session, network: Network, peer_id: int) -> Network:
    existing = db.query(PeerNetworkAccess).filter(
        PeerNetworkAccess.peer_id == peer_id,
        PeerNetworkAccess.network_id == network.id,
    ).first()
    if not existing:
        db.add(PeerNetworkAccess(peer_id=peer_id, network_id=network.id))
        db.commit()
    db.refresh(network)
    return network


def remove_peer_from_network(db: Session, network: Network, peer_id: int) -> Network:
    access = db.query(PeerNetworkAccess).filter(
        PeerNetworkAccess.peer_id == peer_id,
        PeerNetworkAccess.network_id == network.id,
    ).first()
    if access:
        db.delete(access)
        db.commit()
    db.refresh(network)
    return network


def assign_peers_to_network(db: Session, network: Network, peer_ids: list[int]) -> Network:
    db.query(PeerNetworkAccess).filter(
        PeerNetworkAccess.network_id == network.id
    ).delete()
    for pid in peer_ids:
        db.add(PeerNetworkAccess(peer_id=pid, network_id=network.id))
    db.commit()
    db.refresh(network)
    return network


def delete_network(db: Session, network: Network) -> None:
    db.query(PeerNetworkAccess).filter(
        PeerNetworkAccess.network_id == network.id
    ).delete()
    db.delete(network)
    db.commit()


def check_conflict(
    db: Session, subnet: str, exclude_id: int | None = None
) -> tuple[bool, str | None]:
    query = db.query(Network)
    if exclude_id:
        query = query.filter(Network.id != exclude_id)

    for existing in query.all():
        if subnets_overlap(subnet, existing.subnet):
            return True, existing.name

    return False, None
