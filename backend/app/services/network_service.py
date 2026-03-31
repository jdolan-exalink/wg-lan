from sqlalchemy.orm import Session

from app.models.network import Network
from app.schemas.network import NetworkCreate, NetworkUpdate
from app.utils.ip_utils import subnets_overlap


def list_networks(db: Session) -> list[Network]:
    return db.query(Network).order_by(Network.name).all()


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
