import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import require_password_changed
from app.models.server_config import ServerConfig
from app.models.user import User
from app.schemas.system import BackupResponse, HealthResponse, ServerConfigResponse, ServerConfigUpdate
from app.services import wg_service

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    wg_status = "up" if wg_service.is_interface_up() else "down"

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        db=db_status,
        wg_interface=wg_status,
    )


@router.get("/server-config", response_model=ServerConfigResponse)
def get_server_config(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    cfg = db.query(ServerConfig).first()
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not initialised")
    return cfg


@router.put("/server-config", response_model=ServerConfigResponse)
def update_server_config(
    body: ServerConfigUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    cfg = db.query(ServerConfig).first()
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not initialised")
    for key, value in body.model_dump(exclude_none=True).items():
        setattr(cfg, key, value)
    db.commit()
    db.refresh(cfg)
    try:
        wg_service.apply_config(db)
    except Exception:
        pass
    return cfg


@router.post("/apply-config")
def apply_config(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    try:
        wg_service.apply_config(db)
        return {"message": "Config applied successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/backup", response_model=BackupResponse)
def backup(
    _: User = Depends(require_password_changed),
):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path("./data/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)

    db_path = Path(settings.db_path)
    if db_path.exists():
        dest = backup_dir / f"wg-lan_{ts}.db"
        shutil.copy2(db_path, dest)
        return BackupResponse(message="Backup created", path=str(dest))

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database file not found")
