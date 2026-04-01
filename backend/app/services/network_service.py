from sqlalchemy.orm import Session

from app.models.network import Network
from app.models.peer import Peer
from app.schemas.network import NetworkCreate, NetworkUpdate
from app.utils.ip_utils import subnets_overlap


def list_networks(db: Session) -> list[Network]:
    return db.query(Network).order_by(Network.name).all()


def get_network(db: Session, network_id: int) -> Network | None:
    return db.query(Network).filter(Network.id == network_id).first()


def get_network_with_peers(db: Session, network_id: int) -> dict:
    """Get network with associated peer information."""
    network = get_network(db, network_id)
    if not network:
        return {}

    peers = db.query(Peer).filter(Peer.network_id == network_id).all()
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
        "peer_id": network.peer_id,
        "peer_count": len(peers),
        "peers": peer_info,
    }


def list_networks_with_peers(db: Session) -> list[dict]:
    """List all networks with their associated peer information."""
    networks = list_networks(db)
    result = []
    for network in networks:
        peers = db.query(Peer).filter(Peer.network_id == network.id).all()
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
            "peer_id": network.peer_id,
            "peer_count": len(peers),
            "peers": peer_info,
        })
    return result


def get_network(db: Session, network_id: int) -> Network | None:
    return db.query(Network).filter(Network.id == network_id).first()


def create_network(db: Session, data: NetworkCreate) -> Network:
    # If this is being set as default, unset others
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


def assign_peers_to_network(db: Session, network: Network, peer_ids: list[int]) -> Network:
    """Assign peers to a network. Removes existing assignments first."""
    # Remove existing assignments for this network
    db.query(Peer).filter(Peer.network_id == network.id).update({"network_id": None})
    
    # Assign new peers
    if peer_ids:
        db.query(Peer).filter(Peer.id.in_(peer_ids)).update({"network_id": network.id}, synchronize_session=False)
    
    db.commit()
    db.refresh(network)
    return network


def remove_peer_from_network(db: Session, network: Network, peer_id: int) -> Network:
    """Remove a peer from a network."""
    peer = db.query(Peer).filter(Peer.id == peer_id).first()
    if peer and peer.network_id == network.id:
        peer.network_id = None
        db.commit()
    db.refresh(network)
    return network


def delete_network(db: Session, network: Network) -> None:
    """Delete a network and unassign any peers."""
    db.query(Peer).filter(Peer.network_id == network.id).update({"network_id": None})
    db.delete(network)
    db.commit()


def check_conflict(db: Session, subnet: str, exclude_id: int | None = None) -> tuple[bool, str | None]:
    """Check if a subnet conflicts with existing networks."""
    query = db.query(Network)
    if exclude_id:
        query = query.filter(Network.id != exclude_id)
    
    existing_networks = query.all()
    for network in existing_networks:
        if subnets_overlap(subnet, network.subnet):
            return True, network.name
    
    return False, None
    db.refresh(network)
    return network


def delete_network(db: Session, network: Network) -> None:
    db.delete(network)
    db.commit()


def check_conflict(
    db: Session, subnet: str, exclude_id: int | None = None
) -> tuple[bool, str | None]:
    """Check if a subnet overlaps with any existing network. Returns (has_conflict, conflicting_name)."""
    query = db.query(Network)
    if exclude_id:
        query = query.filter(Network.id != exclude_id)

    for existing in query.all():
        if subnets_overlap(subnet, existing.subnet):
            return True, existing.name

    return False, None
