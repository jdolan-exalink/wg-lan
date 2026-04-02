from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_password_changed
from app.models.group import Policy
from app.models.user import User
from app.schemas.policy import PolicyCreate, PolicyUpdate, PolicyMatrixResponse, PolicyResponse
from app.services import policy_service, wg_service
from app.services import iptables_service


def _apply_instant(db: Session) -> None:
    """Re-apply iptables rules immediately. No wg syncconf needed since
    client configs are static (all networks). Policy enforcement is purely
    server-side, so this is the only operation required."""
    try:
        iptables_service.apply_iptables_rules(db)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"iptables re-apply failed: {e}")

router = APIRouter(prefix="/api/policies", tags=["policies"])


@router.get("/firewall-rules")
def get_firewall_rules(
    _: User = Depends(require_password_changed),
):
    """Return live iptables NETLOOM-FWD rules for the UI."""
    return iptables_service.get_fwd_rules()


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
    _apply_instant(db)
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
    _apply_instant(db)
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
    _apply_instant(db)


@router.patch("/reorder", status_code=status.HTTP_200_OK)
def reorder_policies(
    ids: list[int],
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Update policy positions from an ordered list of IDs (index = position)."""
    for idx, policy_id in enumerate(ids):
        db.query(Policy).filter(Policy.id == policy_id).update({"position": idx})
    db.commit()
    _apply_instant(db)
    return {"ok": True}
