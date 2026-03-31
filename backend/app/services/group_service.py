from sqlalchemy.orm import Session

from app.models.group import PeerGroup, PeerGroupMember
from app.schemas.group import PeerGroupCreate, PeerGroupUpdate


def list_groups(db: Session) -> list[PeerGroup]:
    return db.query(PeerGroup).order_by(PeerGroup.name).all()


def get_group(db: Session, group_id: int) -> PeerGroup | None:
    return db.query(PeerGroup).filter(PeerGroup.id == group_id).first()


def create_group(db: Session, data: PeerGroupCreate) -> PeerGroup:
    group = PeerGroup(**data.model_dump())
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def update_group(db: Session, group: PeerGroup, data: PeerGroupUpdate) -> PeerGroup:
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(group, key, value)
    db.commit()
    db.refresh(group)
    return group


def delete_group(db: Session, group: PeerGroup) -> None:
    db.delete(group)
    db.commit()


def add_members(db: Session, group_id: int, peer_ids: list[int]) -> int:
    added = 0
    for peer_id in peer_ids:
        existing = db.query(PeerGroupMember).filter(
            PeerGroupMember.peer_id == peer_id,
            PeerGroupMember.group_id == group_id,
        ).first()
        if not existing:
            db.add(PeerGroupMember(peer_id=peer_id, group_id=group_id))
            added += 1
    db.commit()
    return added


def remove_member(db: Session, group_id: int, peer_id: int) -> bool:
    member = db.query(PeerGroupMember).filter(
        PeerGroupMember.peer_id == peer_id,
        PeerGroupMember.group_id == group_id,
    ).first()
    if not member:
        return False
    db.delete(member)
    db.commit()
    return True


def get_member_count(db: Session, group_id: int) -> int:
    return db.query(PeerGroupMember).filter(PeerGroupMember.group_id == group_id).count()


def get_members(db: Session, group_id: int) -> list[dict]:
    """Get all peer members of a group with their details."""
    from app.models.peer import Peer
    members = (
        db.query(PeerGroupMember)
        .join(Peer, PeerGroupMember.peer_id == Peer.id)
        .filter(PeerGroupMember.group_id == group_id)
        .all()
    )
    return [
        {
            "peer_id": m.peer_id,
            "peer_name": m.peer.name,
            "peer_type": m.peer.peer_type,
            "assigned_ip": m.peer.assigned_ip,
        }
        for m in members
    ]
