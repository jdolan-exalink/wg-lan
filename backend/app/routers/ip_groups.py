from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_password_changed
from app.models.ip_group import IpGroup, IpGroupEntry
from app.models.network import Network
from app.models.user import User
from app.schemas.ip_group import IpGroupCreate, IpGroupUpdate, IpGroupResponse, IpGroupEntryResponse

router = APIRouter(prefix="/api/ip-groups", tags=["ip-groups"])


def _apply_instant(db: Session) -> None:
    from app.services import iptables_service
    try:
        iptables_service.apply_iptables_rules(db)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"iptables re-apply after ip-group change: {e}")


@router.get("", response_model=list[IpGroupResponse])
def list_ip_groups(
    network_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    query = db.query(IpGroup)
    if network_id is not None:
        query = query.filter(IpGroup.network_id == network_id)
    groups = query.all()
    result = []
    for g in groups:
        network = db.query(Network).filter(Network.id == g.network_id).first()
        result.append(IpGroupResponse(
            id=g.id,
            name=g.name,
            network_id=g.network_id,
            network_name=network.name if network else None,
            subnet=network.subnet if network else None,
            description=g.description,
            entry_count=len(g.entries),
            entries=[IpGroupEntryResponse(
                id=e.id,
                ip_group_id=e.ip_group_id,
                ip_address=e.ip_address,
                label=e.label,
                created_at=e.created_at,
            ) for e in g.entries],
            created_at=g.created_at,
            updated_at=g.updated_at,
        ))
    return result


@router.get("/{ip_group_id}", response_model=IpGroupResponse)
def get_ip_group(
    ip_group_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    g = db.query(IpGroup).filter(IpGroup.id == ip_group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="IP Group not found")
    network = db.query(Network).filter(Network.id == g.network_id).first()
    return IpGroupResponse(
        id=g.id,
        name=g.name,
        network_id=g.network_id,
        network_name=network.name if network else None,
        subnet=network.subnet if network else None,
        description=g.description,
        entry_count=len(g.entries),
        entries=[IpGroupEntryResponse(
            id=e.id,
            ip_group_id=e.ip_group_id,
            ip_address=e.ip_address,
            label=e.label,
            created_at=e.created_at,
        ) for e in g.entries],
        created_at=g.created_at,
        updated_at=g.updated_at,
    )


@router.post("", response_model=IpGroupResponse, status_code=status.HTTP_201_CREATED)
def create_ip_group(
    body: IpGroupCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    network = db.query(Network).filter(Network.id == body.network_id).first()
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")

    existing = db.query(IpGroup).filter(IpGroup.name == body.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"IP Group '{body.name}' already exists")

    ip_group = IpGroup(
        name=body.name,
        network_id=body.network_id,
        description=body.description,
    )
    db.add(ip_group)
    db.flush()

    for entry_data in body.entries:
        entry = IpGroupEntry(
            ip_group_id=ip_group.id,
            ip_address=entry_data.ip_address,
            label=entry_data.label,
        )
        db.add(entry)

    db.commit()
    db.refresh(ip_group)

    network = db.query(Network).filter(Network.id == ip_group.network_id).first()
    return IpGroupResponse(
        id=ip_group.id,
        name=ip_group.name,
        network_id=ip_group.network_id,
        network_name=network.name if network else None,
        subnet=network.subnet if network else None,
        description=ip_group.description,
        entry_count=len(ip_group.entries),
        entries=[IpGroupEntryResponse(
            id=e.id,
            ip_group_id=e.ip_group_id,
            ip_address=e.ip_address,
            label=e.label,
            created_at=e.created_at,
        ) for e in ip_group.entries],
        created_at=ip_group.created_at,
        updated_at=ip_group.updated_at,
    )


@router.patch("/{ip_group_id}", response_model=IpGroupResponse)
def update_ip_group(
    ip_group_id: int,
    body: IpGroupUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    g = db.query(IpGroup).filter(IpGroup.id == ip_group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="IP Group not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(g, key, value)

    db.commit()
    db.refresh(g)

    network = db.query(Network).filter(Network.id == g.network_id).first()
    return IpGroupResponse(
        id=g.id,
        name=g.name,
        network_id=g.network_id,
        network_name=network.name if network else None,
        subnet=network.subnet if network else None,
        description=g.description,
        entry_count=len(g.entries),
        entries=[IpGroupEntryResponse(
            id=e.id,
            ip_group_id=e.ip_group_id,
            ip_address=e.ip_address,
            label=e.label,
            created_at=e.created_at,
        ) for e in g.entries],
        created_at=g.created_at,
        updated_at=g.updated_at,
    )


@router.delete("/{ip_group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ip_group(
    ip_group_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    g = db.query(IpGroup).filter(IpGroup.id == ip_group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="IP Group not found")

    from app.models.group import Policy
    policies_using = db.query(Policy).filter(Policy.dest_ip_group_id == ip_group_id).count()
    if policies_using > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete: {policies_using} policy(ies) reference this IP group")

    db.delete(g)
    db.commit()
    _apply_instant(db)


@router.post("/{ip_group_id}/entries", response_model=IpGroupEntryResponse, status_code=status.HTTP_201_CREATED)
def add_entry(
    ip_group_id: int,
    body: IpGroupEntryResponse,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    g = db.query(IpGroup).filter(IpGroup.id == ip_group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="IP Group not found")

    existing = db.query(IpGroupEntry).filter(
        IpGroupEntry.ip_group_id == ip_group_id,
        IpGroupEntry.ip_address == body.ip_address,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"IP {body.ip_address} already in this group")

    entry = IpGroupEntry(
        ip_group_id=ip_group_id,
        ip_address=body.ip_address,
        label=body.label,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    _apply_instant(db)
    return IpGroupEntryResponse(
        id=entry.id,
        ip_group_id=entry.ip_group_id,
        ip_address=entry.ip_address,
        label=entry.label,
        created_at=entry.created_at,
    )


@router.delete("/{ip_group_id}/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    ip_group_id: int,
    entry_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    entry = db.query(IpGroupEntry).filter(
        IpGroupEntry.id == entry_id,
        IpGroupEntry.ip_group_id == ip_group_id,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    db.delete(entry)
    db.commit()
    _apply_instant(db)
