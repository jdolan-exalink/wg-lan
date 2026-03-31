from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_password_changed
from app.models.user import User
from app.schemas.dashboard import DashboardStats, PeerStatusItem, TrafficItem
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    return dashboard_service.get_stats(db)


@router.get("/peers-status", response_model=list[PeerStatusItem])
def get_peers_status(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    return dashboard_service.get_peers_status(db)


@router.get("/traffic", response_model=list[TrafficItem])
def get_traffic(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    return dashboard_service.get_traffic(db)
