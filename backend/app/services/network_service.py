import json
import ipaddress

from sqlalchemy.orm import Session
from fastapi import HTTPException

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
            "gateway_ip": network.gateway_ip,
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
            "gateway_ip": network.gateway_ip,
            "peer_id": network.peer_id,
            "peer_count": len(peers),
            "peers": peer_info,
        })
    return result


def _validate_gateway(db, peer_id, gateway_ip):
    if peer_id is not None and gateway_ip:
        raise HTTPException(422, "Elegí un peer gateway o una IP de siguiente salto")
    if peer_id is not None:
        peer = db.get(Peer, peer_id)
        if not peer or peer.peer_type not in {"branch_office", "server"}:
            raise HTTPException(422, "El gateway debe ser una sucursal o el servidor VPN")


def _sync_owned_subnets(db, peer_id):
    if peer_id is None:
        return
    peer = db.get(Peer, peer_id)
    if peer and peer.peer_type == "branch_office":
        db.flush()
        peer.remote_subnets = json.dumps(sorted(n.subnet for n in db.query(Network).filter(Network.peer_id == peer_id).all()))


def create_network(db: Session, data: NetworkCreate) -> Network:
    _validate_gateway(db, data.peer_id, data.gateway_ip)
    from app.models.server_config import ServerConfig
    cfg = db.query(ServerConfig).first()
    if cfg and ipaddress.ip_network(data.subnet).overlaps(ipaddress.ip_network(cfg.address, strict=False)):
        raise HTTPException(409, "La red se solapa con el segmento de túneles VPN")
    if data.is_default:
        db.query(Network).filter(Network.is_default == True).update({"is_default": False})

    network = Network(**data.model_dump())
    db.add(network)
    _sync_owned_subnets(db, network.peer_id)
    db.commit()
    db.refresh(network)
    return network


def update_network(db: Session, network: Network, data: NetworkUpdate) -> Network:
    updates = data.model_dump(exclude_unset=True)
    updates = {key: value for key, value in updates.items() if value is not None or key in {"peer_id", "gateway_ip", "description"}}
    old_peer_id = network.peer_id
    _validate_gateway(db, updates.get("peer_id", network.peer_id), updates.get("gateway_ip", network.gateway_ip))
    if updates.get("is_default"):
        db.query(Network).filter(Network.id != network.id, Network.is_default == True).update(
            {"is_default": False}
        )
    for key, value in updates.items():
        setattr(network, key, value)
    _sync_owned_subnets(db, old_peer_id)
    _sync_owned_subnets(db, network.peer_id)
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
    from app.models.group import GroupNetworkAccess
    from app.models.user import UserNetworkAccess
    from app.models.peer import PeerOverride
    for model in (GroupNetworkAccess, UserNetworkAccess, PeerOverride):
        db.query(model).filter(model.network_id == network.id).delete(synchronize_session=False)
    db.query(Peer).filter(Peer.network_id == network.id).update({"network_id": None}, synchronize_session=False)
    old_peer_id = network.peer_id
    # Let database cascades delete assignments rather than nulling required FKs.
    db.expire(network, ["peer_access", "group_access", "user_access"])
    db.query(Network).filter(Network.id == network.id).delete(synchronize_session=False)
    _sync_owned_subnets(db, old_peer_id)
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
