from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_password_changed
from app.models.user import User
from app.services import route_service

router = APIRouter(prefix="/api/routes", tags=["routes"])


@router.get("")
def list_routes(db: Session = Depends(get_db), _: User = Depends(require_password_changed)):
    try:
        return route_service.route_inventory(db)
    except (RuntimeError, OSError) as exc:
        raise HTTPException(503, detail=str(exc))


@router.post("/reconcile")
def reconcile(db: Session = Depends(get_db), _: User = Depends(require_password_changed)):
    from app.services import wg_service
    try:
        wg_service.apply_config(db)
        return route_service.route_inventory(db)
    except (RuntimeError, OSError) as exc:
        raise HTTPException(503, detail=f"Configuración guardada; aplicación pendiente: {exc}")
