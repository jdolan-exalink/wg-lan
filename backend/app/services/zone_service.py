from sqlalchemy.orm import Session

from app.models.zone import Zone, ZoneNetwork
from app.schemas.zone import ZoneCreate, ZoneNetworkCreate, ZoneUpdate


def list_zones(db: Session) -> list[Zone]:
    return db.query(Zone).order_by(Zone.name).all()


def get_zone(db: Session, zone_id: int) -> Zone | None:
    return db.query(Zone).filter(Zone.id == zone_id).first()


def create_zone(db: Session, data: ZoneCreate) -> Zone:
    zone = Zone(name=data.name, description=data.description)
    db.add(zone)
    db.flush()  # Get zone.id before adding networks

    for net in data.networks:
        db.add(ZoneNetwork(zone_id=zone.id, cidr=net.cidr, description=net.description))

    db.commit()
    db.refresh(zone)
    return zone


def update_zone(db: Session, zone: Zone, data: ZoneUpdate) -> Zone:
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(zone, key, value)
    db.commit()
    db.refresh(zone)
    return zone


def delete_zone(db: Session, zone: Zone) -> None:
    db.delete(zone)
    db.commit()


def add_zone_network(db: Session, zone: Zone, data: ZoneNetworkCreate) -> ZoneNetwork:
    zn = ZoneNetwork(zone_id=zone.id, cidr=data.cidr, description=data.description)
    db.add(zn)
    db.commit()
    db.refresh(zn)
    return zn


def delete_zone_network(db: Session, zone_network_id: int) -> None:
    zn = db.query(ZoneNetwork).filter(ZoneNetwork.id == zone_network_id).first()
    if zn:
        db.delete(zn)
        db.commit()


def get_all_cidrs_for_zones(db: Session, zone_ids: list[int]) -> list[str]:
    """Return all CIDRs belonging to a list of zone IDs."""
    rows = db.query(ZoneNetwork).filter(ZoneNetwork.zone_id.in_(zone_ids)).all()
    return [r.cidr for r in rows]
