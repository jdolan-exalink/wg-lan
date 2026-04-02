from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.group import PeerGroup, Policy
from app.schemas.policy import PolicyCreate, PolicyUpdate, PolicyMatrixResponse, PolicyMatrixRow, PolicyMatrixCell


def list_policies(
    db: Session,
    source_group_id: int | None = None,
    dest_group_id: int | None = None,
) -> list[Policy]:
    query = db.query(Policy)
    if source_group_id:
        query = query.filter(Policy.source_group_id == source_group_id)
    if dest_group_id:
        query = query.filter(Policy.dest_group_id == dest_group_id)
    return query.order_by(Policy.position, Policy.id).all()


def create_policy(db: Session, data: PolicyCreate) -> Policy:
    # Check for existing policy with same source/dest/direction
    existing = db.query(Policy).filter(
        Policy.source_group_id == data.source_group_id,
        Policy.dest_group_id == data.dest_group_id,
        Policy.direction == data.direction,
    ).first()
    
    if existing:
        existing.action = data.action
        db.commit()
        db.refresh(existing)
        return existing
    
    max_pos = db.query(func.max(Policy.position)).scalar() or 0
    policy = Policy(
        source_group_id=data.source_group_id,
        dest_group_id=data.dest_group_id,
        direction=data.direction,
        action=data.action,
        position=max_pos + 1,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def update_policy(db: Session, policy: Policy, data: PolicyUpdate) -> Policy:
    updates = data.model_dump(exclude_none=True)
    for key, value in updates.items():
        setattr(policy, key, value)
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
    source_groups = db.query(PeerGroup).order_by(PeerGroup.name).all()
    dest_groups = db.query(PeerGroup).order_by(PeerGroup.name).all()
    policies = db.query(Policy).all()

    # Build lookup: (source_group_id, dest_group_id, direction) -> policy
    policy_map: dict[tuple[int, int, str], Policy] = {
        (p.source_group_id, p.dest_group_id, p.direction): p for p in policies
    }

    dest_group_ids = [g.id for g in dest_groups]
    dest_group_names = {g.id: g.name for g in dest_groups}

    rows: list[PolicyMatrixRow] = []
    for source_group in source_groups:
        dest_cells: dict[int, PolicyMatrixCell] = {}
        for dest_group in dest_groups:
            # Check for policies in both directions
            outbound_pol = policy_map.get((source_group.id, dest_group.id, "outbound"))
            inbound_pol = policy_map.get((source_group.id, dest_group.id, "inbound"))
            both_pol = policy_map.get((source_group.id, dest_group.id, "both"))
            
            # Prefer 'both' if exists, otherwise use outbound
            pol = both_pol or outbound_pol
            
            dest_cells[dest_group.id] = PolicyMatrixCell(
                action=pol.action if pol else None,
                policy_id=pol.id if pol else None,
                direction=pol.direction if pol else None,
            )
        
        rows.append(PolicyMatrixRow(
            source_group_id=source_group.id,
            source_group_name=source_group.name,
            dest_groups=dest_cells,
        ))

    return PolicyMatrixResponse(
        source_groups=rows,
        dest_group_ids=dest_group_ids,
        dest_group_names=dest_group_names,
    )
