from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_password_changed
from app.models.user import User
from app.schemas.group import (
    AddMembersRequest,
    GroupMemberResponse,
    GroupNetworkAssignment,
    GroupNetworkAssignmentCreate,
    PeerGroupCreate,
    PeerGroupResponse,
    PeerGroupUpdate,
)
from app.services import group_service
from app.services import iptables_service
from app.models.group import GroupNetworkAccess
from app.models.network import Network

router = APIRouter(prefix="/api/groups", tags=["groups"])


def _apply_group_changes(db: Session) -> None:
    """Re-apply iptables rules immediately after any group change.
    Group membership changes only affect server-side iptables enforcement;
    client configs are static so no wg syncconf is needed."""
    try:
        iptables_service.apply_iptables_rules(db)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"iptables re-apply failed: {e}")


@router.get("", response_model=list[PeerGroupResponse])
def list_groups(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    groups = group_service.list_groups(db)
    result = []
    for g in groups:
        count = group_service.get_member_count(db, g.id)
        resp = PeerGroupResponse.model_validate(g)
        resp.member_count = count
        result.append(resp)
    return result


@router.get("/{group_id}", response_model=PeerGroupResponse)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    group = group_service.get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    count = group_service.get_member_count(db, group_id)
    resp = PeerGroupResponse.model_validate(group)
    resp.member_count = count
    return resp


@router.post("", response_model=PeerGroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    body: PeerGroupCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    group = group_service.create_group(db, body)
    _apply_group_changes(db)
    resp = PeerGroupResponse.model_validate(group)
    resp.member_count = 0
    return resp


@router.patch("/{group_id}", response_model=PeerGroupResponse)
def update_group(
    group_id: int,
    body: PeerGroupUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    group = group_service.get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    group = group_service.update_group(db, group, body)
    _apply_group_changes(db)
    count = group_service.get_member_count(db, group_id)
    resp = PeerGroupResponse.model_validate(group)
    resp.member_count = count
    return resp


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    group = group_service.get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    group_service.delete_group(db, group)
    _apply_group_changes(db)


@router.post("/{group_id}/members", status_code=status.HTTP_200_OK)
def add_members(
    group_id: int,
    body: AddMembersRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    group = group_service.get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    added = group_service.add_members(db, group_id, body.peer_ids)
    _apply_group_changes(db)
    return {"added": added}


@router.delete("/{group_id}/members/{peer_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    group_id: int,
    peer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    removed = group_service.remove_member(db, group_id, peer_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    _apply_group_changes(db)


@router.get("/{group_id}/members", response_model=list[GroupMemberResponse])
def get_group_members(
    group_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    group = group_service.get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group_service.get_members(db, group_id)


# --- Group Network Access Endpoints ---

@router.get("/{group_id}/networks", response_model=list[GroupNetworkAssignment])
def get_group_networks(
    group_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """List all networks assigned to a group."""
    group = group_service.get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    
    assignments = db.query(GroupNetworkAccess).filter(
        GroupNetworkAccess.group_id == group_id
    ).all()
    
    result = []
    for a in assignments:
        network = db.query(Network).filter(Network.id == a.network_id).first()
        if network:
            result.append(GroupNetworkAssignment(
                id=a.id,
                network_id=a.network_id,
                network_name=network.name,
                subnet=network.subnet,
                network_type=network.network_type,
                action=a.action,
            ))
    return result


@router.post("/{group_id}/networks", response_model=GroupNetworkAssignment, status_code=status.HTTP_201_CREATED)
def assign_network_to_group(
    group_id: int,
    body: GroupNetworkAssignmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Assign a network to a group with allow/deny action."""
    group = group_service.get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    
    network = db.query(Network).filter(Network.id == body.network_id).first()
    if not network:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network not found")
    
    # Check if assignment already exists
    existing = db.query(GroupNetworkAccess).filter(
        GroupNetworkAccess.group_id == group_id,
        GroupNetworkAccess.network_id == body.network_id,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Network already assigned to this group")
    
    assignment = GroupNetworkAccess(
        group_id=group_id,
        network_id=body.network_id,
        action=body.action,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    _apply_group_changes(db)
    
    return GroupNetworkAssignment(
        id=assignment.id,
        network_id=assignment.network_id,
        network_name=network.name,
        subnet=network.subnet,
        network_type=network.network_type,
        action=assignment.action,
    )


@router.delete("/{group_id}/networks/{network_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_network_from_group(
    group_id: int,
    network_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Remove a network assignment from a group."""
    assignment = db.query(GroupNetworkAccess).filter(
        GroupNetworkAccess.group_id == group_id,
        GroupNetworkAccess.network_id == network_id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network assignment not found")
    
    db.delete(assignment)
    db.commit()
    _apply_group_changes(db)
