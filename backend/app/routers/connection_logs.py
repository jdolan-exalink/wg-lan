from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_password_changed
from app.models.user import User
from app.schemas.connection_log import ConnectionLogResponse, ConnectionStats
from app.services import connection_log_service

router = APIRouter(prefix="/api/connection-logs", tags=["connection-logs"])


@router.get("", response_model=list[ConnectionLogResponse])
def list_connection_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    event_type: str | None = Query(None),
    severity: str | None = Query(None),
    peer_id: int | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    return connection_log_service.list_logs(
        db, limit=limit, offset=offset,
        event_type=event_type, severity=severity, peer_id=peer_id,
    )


@router.get("/stats", response_model=ConnectionStats)
def get_connection_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    return connection_log_service.get_stats(db)


@router.post("/sync")
def sync_peer_status(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Manually trigger peer status sync to detect connection issues."""
    connection_log_service.sync_peer_status_logs(db)
    return {"message": "Peer status sync completed"}
