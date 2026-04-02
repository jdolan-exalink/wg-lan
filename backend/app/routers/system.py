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
from app.schemas.system import BackupResponse, FirewallStatusResponse, FirewallStatusUpdate, HealthResponse, RegenerateKeyResponse, ServerConfigResponse, ServerConfigUpdate
from app.services import wg_service
from app.utils.wg_keygen import safe_generate_keypair

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

    update_data = body.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(cfg, key, value)

    db.commit()
    db.refresh(cfg)

    # Try to apply config to WireGuard (may fail if WG not available)
    try:
        wg_service.apply_config(db)
    except Exception:
        pass

    return cfg


@router.post("/server-config/regenerate-key", response_model=RegenerateKeyResponse)
def regenerate_keypair(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Regenerate server keypair. This will disconnect all clients."""
    cfg = db.query(ServerConfig).first()
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not initialised")

    private_key, public_key = safe_generate_keypair()
    cfg.private_key = private_key
    cfg.public_key = public_key
    db.commit()
    db.refresh(cfg)

    # Try to apply config to WireGuard
    try:
        wg_service.apply_config(db)
    except Exception:
        pass

    return RegenerateKeyResponse(
        public_key=public_key,
        message="Server keypair regenerated. All clients must update their config files.",
    )


@router.post("/apply-config")
def apply_config(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Apply config to WireGuard. Auto-restarts WG if needed."""
    try:
        wg_service.apply_config(db)
        # Ensure WG is running after applying config
        if not wg_service.is_interface_up():
            try:
                wg_service.bring_up()
            except Exception:
                pass  # May fail on systems without WG kernel module
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
        dest = backup_dir / f"netloom_{ts}.db"
        shutil.copy2(db_path, dest)
        return BackupResponse(message="Backup created", path=str(dest))

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database file not found")


@router.post("/wg/up")
def wg_up(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Bring WireGuard interface up. Creates it if needed."""
    if wg_service.is_interface_up():
        return {"message": "WireGuard interface is already up"}
    try:
        wg_service.ensure_interface_up(db)
        return {"message": "WireGuard interface brought up"}
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"WireGuard not available: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bring up WireGuard: {str(e)}",
        )


@router.post("/wg/down")
def wg_down(
    _: User = Depends(require_password_changed),
):
    """Bring WireGuard interface down."""
    if not wg_service.is_interface_up():
        return {"message": "WireGuard interface is already down"}
    try:
        wg_service.bring_down()
        return {"message": "WireGuard interface brought down"}
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"WireGuard not available: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bring down WireGuard: {str(e)}",
        )


@router.post("/wg/restart")
def wg_restart(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Restart WireGuard: apply config, bring down, bring up."""
    try:
        wg_service.apply_config(db)
        try:
            wg_service.bring_down()
        except Exception:
            pass  # May already be down
        wg_service.bring_up()
        return {"message": "WireGuard restarted successfully"}
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"WireGuard not available: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart WireGuard: {str(e)}",
        )


@router.get("/firewall", response_model=FirewallStatusResponse)
def get_firewall_status(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Get the firewall enabled/disabled state. When disabled, all traffic is allowed."""
    cfg = db.query(ServerConfig).first()
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not initialised")
    return FirewallStatusResponse(firewall_enabled=cfg.firewall_enabled)


@router.patch("/firewall", response_model=FirewallStatusResponse)
def set_firewall_status(
    body: FirewallStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Enable or disable the firewall. When disabled, all peers can reach all networks."""
    cfg = db.query(ServerConfig).first()
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not initialised")
    cfg.firewall_enabled = body.firewall_enabled
    db.commit()
    db.refresh(cfg)
    try:
        from app.services import iptables_service
        iptables_service.apply_iptables_rules(db)
    except Exception:
        pass
    return FirewallStatusResponse(firewall_enabled=cfg.firewall_enabled)
