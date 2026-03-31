from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_password_changed
from app.models.user import User
from app.schemas.group import AddMembersRequest, PeerGroupCreate, PeerGroupResponse, PeerGroupUpdate
from app.services import group_service

router = APIRouter(prefix="/api/groups", tags=["groups"])


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
