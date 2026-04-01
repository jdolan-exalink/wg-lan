from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_password_changed
from app.models.user import User
from app.schemas.policy import PolicyCreate, PolicyUpdate, PolicyMatrixResponse, PolicyResponse
from app.services import policy_service, wg_service

router = APIRouter(prefix="/api/policies", tags=["policies"])


@router.get("", response_model=list[PolicyResponse])
def list_policies(
    source_group_id: int | None = None,
    dest_group_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    return policy_service.list_policies(db, source_group_id=source_group_id, dest_group_id=dest_group_id)


@router.get("/matrix", response_model=PolicyMatrixResponse)
def get_policy_matrix(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    return policy_service.get_policy_matrix(db)


@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
def create_policy(
    body: PolicyCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    policy = policy_service.create_policy(db, body)
    # Apply WireGuard config to update routes
    try:
        wg_service.apply_config(db)
    except Exception:
        pass
    return policy


@router.patch("/{policy_id}", response_model=PolicyResponse)
def update_policy(
    policy_id: int,
    body: PolicyUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    policy = policy_service.update_policy(db, policy, body)
    # Apply WireGuard config to update routes
    try:
        wg_service.apply_config(db)
    except Exception:
        pass
    return policy


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    deleted = policy_service.delete_policy(db, policy_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    # Apply WireGuard config to update routes
    try:
        wg_service.apply_config(db)
    except Exception:
        pass
