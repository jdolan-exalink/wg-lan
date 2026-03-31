from sqlalchemy.orm import Session

from app.models.group import PeerGroup, Policy
from app.models.zone import Zone
from app.schemas.policy import PolicyMatrixResponse, PolicyMatrixRow, PolicyMatrixCell, PolicyUpsert


def list_policies(
    db: Session,
    group_id: int | None = None,
    zone_id: int | None = None,
) -> list[Policy]:
    query = db.query(Policy)
    if group_id:
        query = query.filter(Policy.group_id == group_id)
    if zone_id:
        query = query.filter(Policy.zone_id == zone_id)
    return query.all()


def upsert_policy(db: Session, data: PolicyUpsert) -> Policy:
    existing = db.query(Policy).filter(
        Policy.group_id == data.group_id,
        Policy.zone_id == data.zone_id,
    ).first()

    if existing:
        existing.action = data.action
        db.commit()
        db.refresh(existing)
        return existing

    policy = Policy(group_id=data.group_id, zone_id=data.zone_id, action=data.action)
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def delete_policy(db: Session, policy_id: int) -> bool:
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        return False
    db.delete(policy)
    db.commit()
    return True


def get_policy_matrix(db: Session) -> PolicyMatrixResponse:
    groups = db.query(PeerGroup).order_by(PeerGroup.name).all()
    zones = db.query(Zone).order_by(Zone.name).all()
    policies = db.query(Policy).all()

    # Build lookup: (group_id, zone_id) -> policy
    policy_map: dict[tuple[int, int], Policy] = {
        (p.group_id, p.zone_id): p for p in policies
    }

    zone_ids = [z.id for z in zones]
    zone_names = {z.id: z.name for z in zones}

    rows: list[PolicyMatrixRow] = []
    for group in groups:
        cells: dict[int, PolicyMatrixCell] = {}
        for zone in zones:
            pol = policy_map.get((group.id, zone.id))
            cells[zone.id] = PolicyMatrixCell(
                action=pol.action if pol else None,
                policy_id=pol.id if pol else None,
            )
        rows.append(PolicyMatrixRow(
            group_id=group.id,
            group_name=group.name,
            zones=cells,
        ))

    return PolicyMatrixResponse(groups=rows, zone_ids=zone_ids, zone_names=zone_names)
