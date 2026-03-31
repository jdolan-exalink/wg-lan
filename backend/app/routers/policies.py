from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_password_changed
from app.models.user import User
from app.schemas.policy import PolicyMatrixResponse, PolicyResponse, PolicyUpsert
from app.services import policy_service

router = APIRouter(prefix="/api/policies", tags=["policies"])


@router.get("", response_model=list[PolicyResponse])
def list_policies(
    group_id: int | None = None,
    zone_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    return policy_service.list_policies(db, group_id=group_id, zone_id=zone_id)


@router.get("/matrix", response_model=PolicyMatrixResponse)
def get_policy_matrix(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    return policy_service.get_policy_matrix(db)


@router.post("", response_model=PolicyResponse)
def upsert_policy(
    body: PolicyUpsert,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    return policy_service.upsert_policy(db, body)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    deleted = policy_service.delete_policy(db, policy_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
