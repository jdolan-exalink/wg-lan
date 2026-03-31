from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.services.audit_service import list_logs

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogResponse])
def get_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    target_type: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return list_logs(db, limit=limit, offset=offset, target_type=target_type)
